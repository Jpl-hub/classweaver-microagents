from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("structure", models.JSONField(blank=True, default=dict)),
                ("notes", models.TextField(blank=True)),
                (
                    "job",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_plan", to="core.prestudyjob"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="RecommendationTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("input_snapshot", models.JSONField(blank=True, default=dict)),
                ("output", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                (
                    "job",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="core.prestudyjob"),
                ),
                (
                    "session",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recommendations",
                        to="core.quizsession",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="LessonEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(max_length=64)),
                ("actor", models.CharField(blank=True, max_length=64)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "plan",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="core.lessonplan"),
                ),
            ],
            options={
                "ordering": ("-occurred_at",),
                "abstract": False,
            },
        ),
    ]
