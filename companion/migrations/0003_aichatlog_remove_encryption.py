from django.db import migrations, models


class Migration(migrations.Migration):
    """
    移除 AIChatLog.message_content 的欄位加密。
    原欄位是 bytea（加密二進位），改成純 text。
    舊的加密資料無法解密還原，會一併捨棄。
    """

    dependencies = [
        ("companion", "0002_aichatlog_mood"),
    ]

    operations = [
        # 1. 刪除舊的加密 bytea 欄位
        migrations.RunSQL(
            sql="ALTER TABLE companion_aichatlog DROP COLUMN IF EXISTS message_content;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 2. 新增純文字欄位
        migrations.AddField(
            model_name="aichatlog",
            name="message_content",
            field=models.TextField(default="", verbose_name="內容"),
            preserve_default=False,
        ),
    ]
