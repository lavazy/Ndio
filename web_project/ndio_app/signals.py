from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import UserDetail, AgentProfile, ManagerProfile


@receiver(post_save, sender=User)
def create_referral(sender, instance, created, **kwargs):
    if created:
        UserDetail.objects.create(user=instance)


# A signal that listens for user creation and assigns a user group="client" automatically
@receiver(post_save, sender=User)
def assign_default_group(sender, instance, created, **kwargs):
    if created and not instance.groups.exists():
        user_group, _ = Group.objects.get_or_create(name="client")
        instance.groups.add(user_group)
        print("Group assigned!!")
