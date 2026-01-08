from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(AdminProfile)
admin.site.register(Department)
admin.site.register(Students)
admin.site.register(Notice)