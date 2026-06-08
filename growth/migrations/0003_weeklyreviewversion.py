from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("growth", "0002_kudosnote_remove_encryption"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyReviewVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("week_start", models.DateField(verbose_name="週開始")),
                ("summary_data", models.JSONField(default=dict, verbose_name="回顧資料")),
                ("generated_at", models.DateTimeField(auto_now_add=True, verbose_name="生成時間")),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="review_versions",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "週回顧版本",
                "verbose_name_plural": "週回顧版本",
                "ordering": ["-generated_at"],
            },
        ),
    ]
