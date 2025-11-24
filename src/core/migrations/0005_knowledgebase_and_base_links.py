from django.conf import settings
from django.db import migrations, models


def seed_default_bases(apps, schema_editor):
    KnowledgeBase = apps.get_model("core", "KnowledgeBase")
    KnowledgeDocument = apps.get_model("core", "KnowledgeDocument")
    PrestudyJob = apps.get_model("core", "PrestudyJob")
    UserModel = apps.get_model(settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1])

    # 为现有用户创建默认知识库，并将文档与任务关联到对应的 base
    existing_bases = {}
    for user_id in UserModel.objects.values_list("id", flat=True):
        base, _created = KnowledgeBase.objects.get_or_create(user_id=user_id, name="默认知识库", defaults={"description": ""})
        existing_bases[user_id] = base

    for doc in KnowledgeDocument.objects.filter(base__isnull=True, user_id__isnull=False):
        base = existing_bases.get(doc.user_id)
        if base:
            doc.base_id = base.id
            doc.save(update_fields=["base"])

    for job in PrestudyJob.objects.filter(knowledge_base__isnull=True, user_id__isnull=False):
        base = existing_bases.get(job.user_id)
        if base:
            job.knowledge_base_id = base.id
            job.save(update_fields=["knowledge_base"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_knowledgedocument_user_lessonplan_user_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeBase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="knowledge_bases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at",),
                "unique_together": {("user", "name")},
            },
        ),
        migrations.AddField(
            model_name="prestudyjob",
            name="knowledge_base",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="prestudy_jobs",
                to="core.knowledgebase",
            ),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="base",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="documents",
                to="core.knowledgebase",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="knowledgedocument",
            unique_together={("base", "doc_id")},
        ),
        migrations.RemoveField(
            model_name="prestudyjob",
            name="knowledge_doc_ids",
        ),
        migrations.RunPython(seed_default_bases, migrations.RunPython.noop),
    ]
