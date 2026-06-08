from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0003_psychoarticle_view_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="psychoarticle",
            name="category",
            field=models.CharField(
                choices=[
                    ("壓力管理", "壓力管理"),
                    ("情緒覺察", "情緒覺察"),
                    ("焦慮", "焦慮"),
                    ("睡眠", "睡眠"),
                    ("人際關係", "人際關係"),
                    ("自我照顧", "自我照顧"),
                    ("AI 小說", "AI 小說"),
                    ("逐字稿", "逐字稿"),
                ],
                db_index=True,
                max_length=30,
                verbose_name="分類",
            ),
        ),
    ]
