import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from src.services.evaluation import compare_report_summaries


class Command(BaseCommand):
    help = "对比两份 benchmark 报告，输出 summary 指标差异。"

    def add_arguments(self, parser):
        parser.add_argument("--baseline", type=str, required=True, help="基线报告 JSON 路径")
        parser.add_argument("--candidate", type=str, required=True, help="候选报告 JSON 路径")
        parser.add_argument("--output", type=str, help="可选，输出差异报告路径")

    def handle(self, *args, **options):
        baseline_path = Path(options["baseline"])
        candidate_path = Path(options["candidate"])
        if not baseline_path.exists():
            raise CommandError(f"Baseline report not found: {baseline_path}")
        if not candidate_path.exists():
            raise CommandError(f"Candidate report not found: {candidate_path}")

        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid report JSON: {exc}") from exc

        diff = compare_report_summaries(baseline=baseline, candidate=candidate)
        rendered = json.dumps(diff, ensure_ascii=False, indent=2)

        output = options.get("output")
        if output:
            Path(output).write_text(rendered + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"对比完成，报告已写入 {output}"))
            return
        self.stdout.write(rendered)
