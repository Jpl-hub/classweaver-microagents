from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_lesson_entities"),
    ]

    operations = [
        migrations.AddField(
            model_name="prestudyjob",
            name="knowledge_doc_ids",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
