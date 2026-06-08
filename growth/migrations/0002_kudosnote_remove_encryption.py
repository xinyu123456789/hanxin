from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("growth", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE growth_kudosnote DROP COLUMN IF EXISTS praise_content;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddField(
            model_name="kudosnote",
            name="praise_content",
            field=models.TextField(default="", verbose_name="內容"),
            preserve_default=False,
        ),
    ]
