from django.db import migrations, models


def migrate_fallback_status(apps, schema_editor):
    PrestudyJob = apps.get_model("core", "PrestudyJob")
    PrestudyJob.objects.filter(status="completed_with_fallback").update(status="completed")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_knowledgechunk_embedding_vector"),
    ]

    operations = [
        migrations.RunPython(migrate_fallback_status, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="prestudyjob",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("queued", "Queued"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=32,
            ),
        ),
    ]
