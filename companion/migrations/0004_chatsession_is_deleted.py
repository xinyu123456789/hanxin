from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companion", "0003_aichatlog_remove_encryption"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="is_deleted",
            field=models.BooleanField(default=False, verbose_name="已刪除"),
        ),
    ]
