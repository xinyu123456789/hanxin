from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="crisis_until",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="危機狀態到期時間",
            ),
        ),
    ]
