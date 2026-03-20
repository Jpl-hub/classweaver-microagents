import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from src.core.models import KnowledgeBase
from src.kb.retrieve import retrieve_context
from src.services.evaluation import evaluate_retrieval_cases


class Command(BaseCommand):
    help = "使用标注数据集评估知识库检索质量（hit rate / MRR / recall@k / precision@k）。"

    def add_arguments(self, parser):
        parser.add_argument("--base-id", type=int, required=True, help="知识库 ID")
        parser.add_argument("--dataset", type=str, required=True, help="评测数据集 JSON 文件路径")
        parser.add_argument("--top-k", type=int, default=5, help="检索 top-k，默认 5")
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

        report = evaluate_retrieval_cases(
            cases=cases,
            top_k=options["top_k"],
            retrieve_fn=lambda query, top_k: retrieve_context(query=query, top_k=top_k, base=base),
        )
        report["config"] = {
            "base_id": base.pk,
            "base_name": base.name,
            "top_k": options["top_k"],
            "dataset": str(dataset_path),
        }

        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        output = options.get("output")
        if output:
            Path(output).write_text(rendered + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"评测完成，报告已写入 {output}"))
        else:
            self.stdout.write(rendered)
