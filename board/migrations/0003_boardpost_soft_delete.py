from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("board", "0002_add_preset_messages"),
    ]

    operations = [
        migrations.AddField(
            model_name="boardpost",
            name="is_deleted",
            field=models.BooleanField(default=False, verbose_name="已撤回"),
        ),
        migrations.AddField(
            model_name="boardpost",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="撤回時間"),
        ),
    ]
