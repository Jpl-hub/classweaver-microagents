import logging
from pathlib import Path
import uuid
from typing import Any, Dict, List

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from src.core.models import PrestudyJob, QuizAnswer, QuizSession
from src.kb import ingest as kb_ingest
from src.kb import retrieve as kb_retrieve
from src.services import printable as printable_service
from src.services import ppt as ppt_service
from src.services.pipeline import run_pipeline
from src.services.scoring import score_quiz

from .serializers import (
    KnowledgeSearchSerializer,
    PrestudyResponseSerializer,
    PrestudyTextSerializer,
    QuizAnswerSerializer,
    QuizStartRequestSerializer,
    QuizSubmitRequestSerializer,
)

logger = logging.getLogger(__name__)


class PrestudyFromTextView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = PrestudyTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["text"]

        job = PrestudyJob.objects.create(source_type="text", source_excerpt=text[:512], status="processing")
        try:
            payload = run_pipeline(job=job, text=text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Prestudy pipeline failed for job %s", job.pk)
            job.status = "failed"
            job.save(update_fields=["status"])
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_serializer = PrestudyResponseSerializer(payload)
        return Response(response_serializer.data)


class PrestudyFromPptView(APIView):
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

        job = PrestudyJob.objects.create(source_type="ppt", source_excerpt="", status="processing")
        try:
            payload = run_pipeline(job=job, ppt_file=upload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Prestudy pipeline failed for job %s", job.pk)
            job.status = "failed"
            job.save(update_fields=["status"])
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_serializer = PrestudyResponseSerializer(payload)
        return Response(response_serializer.data)


class PrestudyDetailView(APIView):
    def get(self, request, pk: int, *args, **kwargs):
        job = get_object_or_404(PrestudyJob, pk=pk)
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
        serializer = PrestudyResponseSerializer(base_payload)
        return Response(serializer.data)


class QuizStartView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = QuizStartRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(PrestudyJob, pk=serializer.validated_data["job_id"])
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
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = QuizSubmitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_object_or_404(QuizSession, session_id=serializer.validated_data["session_id"])
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
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist("file")
        if not files:
            single = request.FILES.get("file")
            if single:
                files = [single]
        if not files:
            return Response({"detail": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            summary = kb_ingest.ingest_documents(files=files)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Knowledge ingestion failed")
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(summary, status=status.HTTP_201_CREATED)


class KnowledgeSearchView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = KnowledgeSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["query"]
        top_k = serializer.validated_data["top_k"]
        try:
            results = kb_retrieve.retrieve_context(query=query, top_k=top_k)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Knowledge search failed")
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"results": results})
