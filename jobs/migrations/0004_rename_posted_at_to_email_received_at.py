from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_job_is_favorite"),
    ]

    operations = [
        migrations.RenameField(
            model_name="job",
            old_name="posted_at",
            new_name="email_received_at",
        ),
        migrations.AlterField(
            model_name="job",
            name="email_received_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="When the Upwork alert email landed in Gmail (its internalDate) — not when Upwork itself posted the job.",
            ),
        ),
    ]
