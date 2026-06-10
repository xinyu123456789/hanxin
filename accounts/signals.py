from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserProfile, UserPreference


@receiver(post_save, sender=User)
def create_related_objects(sender, instance, created, **kwargs):
    """新使用者註冊後，自動建立 Profile / UserPreference。"""
    if created:
        UserProfile.objects.create(user=instance)
        UserPreference.objects.create(user=instance)
