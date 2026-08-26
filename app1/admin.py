from django.contrib import admin
from .models import CustomUser, Projects, Task
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Projects)
admin.site.register(Task)
