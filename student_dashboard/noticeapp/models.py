from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

# Create your models here.
def get_expire_date():
    return timezone.now() + timedelta(days=3)

class AdminProfile(models.Model):
    admin_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=15, default='admin')


class Department(models.Model):
    d_name = models.CharField(max_length=20)
    d_code = models.CharField(max_length=15, unique=True)


class Students(models.Model):
    enrollment_no = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    password = models.TextField()
    role = models.CharField(max_length=15, default='student')
    full_name = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    sem = models.CharField(max_length=5, default='1')


class Notice(models.Model):
    notice_title = models.CharField(max_length=50)
    notice_description = models.TextField()
    notice_attachment = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    sem = models.CharField(max_length=5, default='1')
    created_at = models.DateTimeField(auto_now_add=True)
    expired_date = models.DateTimeField(default=get_expire_date)
    is_active = models.BooleanField(default=True)