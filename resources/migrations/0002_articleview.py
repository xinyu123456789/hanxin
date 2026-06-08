from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ArticleView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_viewed_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="article_views",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("article", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="views",
                    to="resources.psychoarticle",
                )),
            ],
            options={
                "verbose_name": "文章閱讀記錄",
                "verbose_name_plural": "文章閱讀記錄",
                "ordering": ["-first_viewed_at"],
                "unique_together": {("user", "article")},
            },
        ),
    ]
