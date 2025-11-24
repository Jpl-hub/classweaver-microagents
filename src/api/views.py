import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
import uuid
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from src.core.models import KnowledgeBase, KnowledgeDocument, LessonEvent, LessonPlan, PrestudyJob, QuizAnswer, QuizSession
from src.kb import ingest as kb_ingest
from src.kb import retrieve as kb_retrieve
from src.services import printable as printable_service
from src.services import ppt as ppt_service
from src.services.jobs import enqueue_prestudy_job
from src.services import recommendation as recommendation_service
from src.services.scoring import score_quiz
from src.agents.utils import build_client

from .serializers import (
    KnowledgeSearchSerializer,
    KnowledgeBaseSerializer,
    KnowledgeQaSerializer,
    LessonEventSerializer,
    PrestudyJobStatusSerializer,
    PrestudyResponseSerializer,
    PrestudyTextSerializer,
    QuizAnswerSerializer,
    QuizStartRequestSerializer,
    QuizSubmitRequestSerializer,
    RecommendationTaskSerializer,
    RecommendationTriggerSerializer,
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


@dataclass
class AuthPayload:
    id: int
    username: str
    email: str


def _serialize_user(user: Any) -> dict:
    payload = AuthPayload(id=user.pk, username=user.get_username(), email=getattr(user, "email", "") or "")
    return asdict(payload)


def _get_base_for_user(user: Any, base_id: Any | None) -> KnowledgeBase:
    if base_id is None or str(base_id).strip() == "":
        raise ValueError("base_id is required")
    try:
        return get_object_or_404(KnowledgeBase, pk=int(base_id), user=user)
    except (ValueError, TypeError):
        raise ValueError("base_id must be a valid integer") from None


class RegisterView(APIView):
    parser_classes = [JSONParser]
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        email = serializer.validated_data.get("email", "").strip()
        password = serializer.validated_data["password"]

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)

        return Response(UserSerializer(_serialize_user(user)).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    parser_classes = [JSONParser]
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        return Response(UserSerializer(_serialize_user(user)).data)


class LogoutView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(_serialize_user(request.user)).data)


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request, *args, **kwargs):
        token = get_token(request)
        return Response({"csrfToken": token})


def _parse_doc_ids(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            return [raw]
    return []


class PrestudyFromTextView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = PrestudyTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["text"]
        try:
            base = _get_base_for_user(request.user, serializer.validated_data.get("base_id"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        job = PrestudyJob.objects.create(
            user=request.user,
            knowledge_base=base,
            source_type="text",
            source_excerpt=text[:512],
            status="queued",
        )
        enqueue_prestudy_job(job=job, text=text)

        response_serializer = PrestudyJobStatusSerializer(
            {"id": str(job.pk), "status": job.status, "detail": "任务已提交，正在排队", "estimated_wait_sec": 20}
        )
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)


class PrestudyFromPptView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "Missing PPTX file."}, status=status.HTTP_400_BAD_REQUEST)
        suffix = Path(upload.name).suffix.lower()
        if suffix not in ppt_service.ALLOWED_EXTENSIONS:
            return Response({"detail": "Only PPTX files are supported."}, status=status.HTTP_400_BAD_REQUEST)
        if upload.content_type and upload.content_type not in ppt_service.ALLOWED_MIME_TYPES:
            return Response({"detail": f"Unsupported content type: {upload.content_type}"}, status=status.HTTP_400_BAD_REQUEST)

        file_bytes = upload.read()
        try:
            base = _get_base_for_user(request.user, request.data.get("base_id"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        job = PrestudyJob.objects.create(
            user=request.user,
            knowledge_base=base,
            source_type="ppt",
            source_excerpt="",
            status="queued",
        )
        enqueue_prestudy_job(job=job, ppt_bytes=file_bytes, filename=upload.name)

        response_serializer = PrestudyJobStatusSerializer(
            {"id": str(job.pk), "status": job.status, "detail": "PPT 解析中，稍后可查看结果", "estimated_wait_sec": 40}
        )
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)


class PrestudyDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        job = get_object_or_404(PrestudyJob, pk=pk, user=request.user)
        base_payload = {
            "id": str(job.pk),
            "status": job.status,
            "planner_json": job.planner_json or {},
            "final_json": job.final_json or {},
            "model_trace": job.model_trace or {},
            "duration_ms": job.duration_ms,
        }
        printable_payload = printable_service.build_printable_payload(base_payload["final_json"])
        base_payload["printable"] = printable_payload
        plan = getattr(job, "lesson_plan", None)
        if plan:
            base_payload["lesson_plan"] = {
                "id": plan.pk,
                "title": plan.title,
                "structure": plan.structure,
                "notes": plan.notes,
            }
        serializer = PrestudyResponseSerializer(base_payload)
        return Response(serializer.data)


class PrestudyJobStatusView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        job = get_object_or_404(PrestudyJob, pk=pk, user=request.user)
        detail = ""
        if job.status == "queued":
            detail = "排队中，请稍后刷新"
        elif job.status == "processing":
            detail = "正在调用模型 ..."
        elif job.status == "failed":
            detail = "任务失败，请查看日志或重试"
        serializer = PrestudyJobStatusSerializer(
            {
                "id": str(job.pk),
                "status": job.status,
                "detail": detail,
                "estimated_wait_sec": 10 if job.status in {"queued", "processing"} else 0,
            }
        )
        return Response(serializer.data)


class QuizStartView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = QuizStartRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(PrestudyJob, pk=serializer.validated_data["job_id"], user=request.user)
        quiz_items: List[Dict[str, Any]] = job.final_json.get("quiz", {}).get("items", [])
        if not quiz_items:
            return Response({"detail": "Quiz data is unavailable for this job."}, status=status.HTTP_409_CONFLICT)

        session = QuizSession.objects.create(
            job=job,
            session_id=uuid.uuid4().hex,
            questions_snapshot=quiz_items,
        )

        questions = [
            {
                "id": item.get("id"),
                "question": item.get("question"),
                "options": item.get("options"),
                "difficulty": item.get("difficulty", "medium"),
            }
            for item in quiz_items
        ]

        return Response({"session_id": session.session_id, "questions": questions})


class QuizSubmitView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = QuizSubmitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_object_or_404(QuizSession, session_id=serializer.validated_data["session_id"], job__user=request.user)
        answers = serializer.validated_data["answers"]
        if not answers:
            return Response({"detail": "No answers provided."}, status=status.HTTP_400_BAD_REQUEST)

        questions = session.questions_snapshot or []
        result = score_quiz(questions=questions, answers=answers)

        now = timezone.now()
        session.ended_at = now
        session.save(update_fields=["ended_at"])

        quiz_answer_objects = []
        answer_map = {answer["id"]: answer["answer"] for answer in answers}
        for question in questions:
            qid = question.get("id")
            if not qid:
                continue
            quiz_answer_objects.append(
                QuizAnswer(
                    session=session,
                    question_id=qid,
                    answer=answer_map.get(qid, ""),
                    correct=result["detail_map"].get(qid, {}).get("correct", False),
                    used_variant=question.get("selected_variant", ""),
                    kp_ids=question.get("kp_ids", []),
                )
            )
        QuizAnswer.objects.bulk_create(quiz_answer_objects)

        # Remove helper map before returning response
        result.pop("detail_map", None)
        return Response(result)


class KnowledgeUploadView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            base = _get_base_for_user(request.user, request.data.get("base_id"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        files = request.FILES.getlist("file")
        if not files:
            single = request.FILES.get("file")
            if single:
                files = [single]
        if not files:
            return Response({"detail": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            summary = kb_ingest.ingest_documents(files=files, base=base)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Knowledge ingestion failed")
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(summary, status=status.HTTP_201_CREATED)


class KnowledgeSearchView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = KnowledgeSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["query"]
        top_k = serializer.validated_data["top_k"]
        try:
            base = _get_base_for_user(request.user, serializer.validated_data.get("base_id"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            results = kb_retrieve.retrieve_context(query=query, top_k=top_k, base=base)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Knowledge search failed")
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"results": results})


class KnowledgeQaView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = KnowledgeQaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"].strip()
        if not question:
            return Response({"detail": "问题不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            base = _get_base_for_user(request.user, serializer.validated_data.get("base_id"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        top_k = serializer.validated_data["top_k"]

        try:
            contexts = kb_retrieve.retrieve_context(query=question, top_k=top_k, base=base)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Knowledge QA search failed")
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not contexts:
            return Response({"answer": "知识库中没有找到相关内容。", "contexts": []})

        client = build_client(settings.AGENT_SETTINGS)
        context_text = "\n\n".join(
            f"[{idx + 1}] {ctx.get('text', '')}" for idx, ctx in enumerate(contexts)
        )
        system_prompt = (
            "你是一个知识库问答助手。根据提供的上下文用中文简洁回答，"
            "如果上下文不足，直接说明无法找到答案，不要编造。"
        )
        user_prompt = f"问题：{question}\n\n可用上下文：\n{context_text}"

        try:
            answer = client.chat(
                model=settings.AGENT_SETTINGS.get("qwen_model", "Qwen/Qwen2.5-14B-Instruct"),
                system=system_prompt,
                user=user_prompt,
                temperature=0.2,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Knowledge QA generation failed")
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"answer": answer, "contexts": contexts})


class KnowledgeDocumentListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        base_id = request.query_params.get("base_id")
        if base_id:
            base = get_object_or_404(KnowledgeBase, pk=base_id, user=request.user)
            docs_qs = KnowledgeDocument.objects.filter(base=base)
        else:
            docs_qs = KnowledgeDocument.objects.filter(user=request.user)
        documents = docs_qs.order_by("-updated_at").values("doc_id", "title", "updated_at", "metadata", "base_id")[:200]
        payload = [
            {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "base_id": doc.get("base_id"),
                "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else "",
                "metadata": doc.get("metadata") or {},
            }
            for doc in documents
        ]
        return Response({"documents": payload})

    def delete(self, request, *args, **kwargs):
        """Delete all knowledge documents and their chunks."""
        deleted_count, _ = KnowledgeDocument.objects.filter(user=request.user).delete()
        return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)


class KnowledgeDocumentDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, doc_id: str, *args, **kwargs):
        base_id = request.query_params.get("base_id")
        qs = KnowledgeDocument.objects.filter(doc_id=doc_id, user=request.user)
        if base_id:
            qs = qs.filter(base_id=base_id)
        doc = qs.first()
        if not doc:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        doc.delete()
        return Response({"deleted": 1}, status=status.HTTP_200_OK)


class KnowledgeBaseListCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, *args, **kwargs):
        bases = KnowledgeBase.objects.filter(user=request.user).order_by("-updated_at")
        serializer = KnowledgeBaseSerializer(
            [
                {"id": base.pk, "name": base.name, "description": base.description}
                for base in bases
            ],
            many=True,
        )
        return Response({"bases": serializer.data})

    def post(self, request, *args, **kwargs):
        serializer = KnowledgeBaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        base = KnowledgeBase.objects.create(
            user=request.user,
            name=serializer.validated_data["name"].strip(),
            description=serializer.validated_data.get("description") or "",
        )
        return Response({"id": base.pk, "name": base.name, "description": base.description}, status=status.HTTP_201_CREATED)


class KnowledgeBaseDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk: int, *args, **kwargs):
        base = get_object_or_404(KnowledgeBase, pk=pk, user=request.user)
        base.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LessonTimelineView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        plan = get_object_or_404(LessonPlan, pk=pk, job__user=request.user)
        events = plan.events.all()[:100]
        payload = {
            "plan": {
                "id": plan.pk,
                "title": plan.title,
                "structure": plan.structure,
                "notes": plan.notes,
            },
            "events": [
                {
                    "id": event.pk,
                    "event_type": event.event_type,
                    "actor": event.actor,
                    "payload": event.payload,
                    "occurred_at": event.occurred_at.isoformat(),
                }
                for event in events
            ],
        }
        return Response(payload)


class LessonEventCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, pk: int, *args, **kwargs):
        plan = get_object_or_404(LessonPlan, pk=pk, job__user=request.user)
        serializer = LessonEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        LessonEvent.objects.create(
            plan=plan,
            event_type=data["event_type"],
            actor=data.get("actor", ""),
            payload=data.get("payload") or {},
        )
        return Response(status=status.HTTP_201_CREATED)


class RecommendationTriggerView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = RecommendationTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = get_object_or_404(PrestudyJob, pk=serializer.validated_data["job_id"], user=request.user)
        session_id = serializer.validated_data.get("session_id")
        session = None
        if session_id:
            session = get_object_or_404(QuizSession, session_id=session_id, job__user=request.user)
        task = recommendation_service.run_recommendation_task(job=job, session=session)
        response = RecommendationTaskSerializer(
            {"id": str(task.pk), "status": task.status, "output": task.output or {}}
        )
        return Response(response.data, status=status.HTTP_201_CREATED)
