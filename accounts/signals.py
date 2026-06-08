from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserProfile, AISetting, UserPreference


@receiver(post_save, sender=User)
def create_related_objects(sender, instance, created, **kwargs):
    """新使用者註冊後，自動建立 Profile / AISetting / UserPreference。"""
    if created:
        UserProfile.objects.create(user=instance)
        AISetting.objects.create(user=instance)
        UserPreference.objects.create(user=instance)
