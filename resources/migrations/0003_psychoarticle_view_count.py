from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0002_articleview"),
    ]

    operations = [
        migrations.AddField(
            model_name="psychoarticle",
            name="view_count",
            field=models.PositiveIntegerField(default=0, verbose_name="點擊次數"),
        ),
    ]
