from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("growth", "0004_alter_weeklyreviewversion_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="kudosnote",
            name="is_deleted",
            field=models.BooleanField(default=False, verbose_name="已刪除"),
        ),
        migrations.AddField(
            model_name="kudosnote",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="刪除時間"),
        ),
    ]
