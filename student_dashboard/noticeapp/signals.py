from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import AdminProfile

@receiver(post_save, sender=User)
def create_admin_profile(sender, instance, created, **kwargs):
    if created:
        AdminProfile.objects.create(admin_user=instance)

@receiver(post_save, sender=User)
def save_admin_profile(sender, instance, **kwargs):
    if hasattr(instance, "adminprofile"):
        instance.adminprofile.save()
