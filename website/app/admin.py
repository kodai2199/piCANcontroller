from django.contrib import admin
from .models import Installation, Command

# Register your models here.
admin.site.register(Installation)
admin.site.register(Command)