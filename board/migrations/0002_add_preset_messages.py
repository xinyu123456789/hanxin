from django.db import migrations

EXTRA_MESSAGES = [
    "你比你想的更有力量",
    "每一天都不容易，謝謝你還在",
    "記得今天也要愛自己",
    "你值得被溫柔對待",
    "不管今天怎麼樣，你都撐過來了",
    "休息不是放棄，是讓自己更好",
    "你不需要完美，你只需要是你自己",
    "今天做了什麼小事讓自己開心？",
    "被你陪伴，真的很幸運",
    "你的感受很重要，值得被好好對待",
    "一步一步來，不用急",
    "你已經很棒了，繼續加油",
    "陪你在這裡，無論如何",
    "今天能做到這樣，真的很不容易",
    "允許自己脆弱，那也是勇敢的一種",
    "你比昨天的自己更好了",
    "謝謝你願意在這裡分享",
]


def add_messages(apps, schema_editor):
    PresetMessage = apps.get_model("board", "PresetMessage")
    existing = set(PresetMessage.objects.values_list("content", flat=True))
    for content in EXTRA_MESSAGES:
        if content not in existing:
            PresetMessage.objects.create(content=content, is_active=True)


def remove_messages(apps, schema_editor):
    PresetMessage = apps.get_model("board", "PresetMessage")
    PresetMessage.objects.filter(content__in=EXTRA_MESSAGES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("board", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_messages, remove_messages),
    ]
