from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companion", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aichatlog",
            name="mood_score",
            field=models.SmallIntegerField(
                blank=True, null=True, verbose_name="情緒分數"
            ),
        ),
        migrations.AddField(
            model_name="aichatlog",
            name="mood_reasoning",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="評分說明"
            ),
        ),
    ]
