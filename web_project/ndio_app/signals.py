from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import User_Detail

@receiver(post_save, sender=User)
def create_referral(sender, instance, created, **kwargs):
    if created:
        User_Detail.objects.create(user=instance)