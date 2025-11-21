from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from src.core.models import KnowledgeChunk, KnowledgeDocument
from src.kb import store as kb_store


class Command(BaseCommand):
    help = "删除所有知识库文档、切片记录，并清空本地向量索引文件。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="跳过交互确认（慎用）。",
        )

    def handle(self, *args, **options):
        confirm = options["yes"]
        if not confirm:
            answer = input("该操作会永久删除所有知识库记录和向量索引，确定继续？[yes/NO]: ").strip().lower()
            if answer not in {"y", "yes"}:
                self.stdout.write(self.style.WARNING("已取消重置。"))
                return

        with transaction.atomic():
            chunk_deleted, _ = KnowledgeChunk.objects.all().delete()
            doc_deleted, _ = KnowledgeDocument.objects.all().delete()

        agent_settings = settings.AGENT_SETTINGS
        paths = [
            Path(agent_settings["vstore_path"]),
            Path(agent_settings["vstore_meta"]),
        ]
        for path in paths:
            if path.exists():
                path.unlink()

        kb_store.clear_store_cache()

        self.stdout.write(
            self.style.SUCCESS(
                f"知识库已重置：删除文档 {doc_deleted} 条、切片 {chunk_deleted} 条，并清理向量索引文件。"
            )
        )
