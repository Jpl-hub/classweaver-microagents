import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from src.core.models import KnowledgeBase, PrestudyJob
from src.services.evaluation import build_report_metadata, evaluate_review_cases
from src.services.pipeline import run_pipeline


class Command(BaseCommand):
    help = "评估 review cycle 对课程质量分数的影响。"

    def add_arguments(self, parser):
        parser.add_argument("--base-id", type=int, required=True, help="知识库 ID")
        parser.add_argument("--dataset", type=str, required=True, help="评测数据集 JSON 文件路径")
        parser.add_argument("--output", type=str, help="可选，评测报告输出路径")

    def handle(self, *args, **options):
        dataset_path = Path(options["dataset"])
        if not dataset_path.exists():
            raise CommandError(f"Dataset file not found: {dataset_path}")

        try:
            payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid dataset JSON: {exc}") from exc

        cases = payload.get("cases") if isinstance(payload, dict) else payload
        if not isinstance(cases, list):
            raise CommandError("Dataset must be a JSON object with 'cases' list or a top-level list.")

        try:
            base = KnowledgeBase.objects.select_related("user").get(pk=options["base_id"])
        except KnowledgeBase.DoesNotExist as exc:
            raise CommandError(f"Knowledge base not found: {options['base_id']}") from exc

        def review_fn(text: str):
            job = PrestudyJob.objects.create(
                user=base.user,
                knowledge_base=base,
                source_type="text",
                source_excerpt=text[:256],
                status="processing",
            )
            try:
                return run_pipeline(job=job, text=text)
            finally:
                job.delete()

        report = evaluate_review_cases(cases=cases, review_fn=review_fn)
        report["config"] = {
            "base_id": base.pk,
            "base_name": base.name,
            "dataset": str(dataset_path),
            "vector_backend": settings.AGENT_SETTINGS.get("vector_backend"),
            "hybrid_retrieval": settings.AGENT_SETTINGS.get("hybrid_retrieval"),
            "rerank_enabled": settings.AGENT_SETTINGS.get("rerank_enabled"),
            "review_enabled": settings.AGENT_SETTINGS.get("review_enabled"),
            "review_max_rounds": settings.AGENT_SETTINGS.get("review_max_rounds"),
            "review_top_k_multiplier": settings.AGENT_SETTINGS.get("review_top_k_multiplier"),
            "embedding_model": settings.AGENT_SETTINGS.get("embedding_model"),
        }
        report["meta"] = build_report_metadata(
            report_type="review_cycles",
            dataset=str(dataset_path),
            top_k=0,
        )

        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        output = options.get("output")
        if output:
            Path(output).write_text(rendered + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"评测完成，报告已写入 {output}"))
        else:
            self.stdout.write(rendered)
