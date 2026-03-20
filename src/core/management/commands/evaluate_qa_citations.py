import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from src.core.models import KnowledgeBase
from src.services.evaluation import build_report_metadata, evaluate_citation_cases
from src.services.qa import answer_question


class Command(BaseCommand):
    help = "评估知识库问答输出中的 citation 使用质量。"

    def add_arguments(self, parser):
        parser.add_argument("--base-id", type=int, required=True, help="知识库 ID")
        parser.add_argument("--dataset", type=str, required=True, help="评测数据集 JSON 文件路径")
        parser.add_argument("--top-k", type=int, default=4, help="问答检索 top-k，默认 4")
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

        report = evaluate_citation_cases(
            cases=cases,
            top_k=options["top_k"],
            qa_fn=lambda query, top_k: answer_question(question=query, base=base, top_k=top_k),
        )
        report["config"] = {
            "base_id": base.pk,
            "base_name": base.name,
            "top_k": options["top_k"],
            "dataset": str(dataset_path),
            "vector_backend": settings.AGENT_SETTINGS.get("vector_backend"),
            "hybrid_retrieval": settings.AGENT_SETTINGS.get("hybrid_retrieval"),
            "rerank_enabled": settings.AGENT_SETTINGS.get("rerank_enabled"),
            "embedding_model": settings.AGENT_SETTINGS.get("embedding_model"),
        }
        report["meta"] = build_report_metadata(
            report_type="qa_citations",
            dataset=str(dataset_path),
            top_k=options["top_k"],
        )

        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        output = options.get("output")
        if output:
            Path(output).write_text(rendered + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"评测完成，报告已写入 {output}"))
        else:
            self.stdout.write(rendered)
