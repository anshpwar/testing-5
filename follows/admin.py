from django.contrib import admin

from .models import Block, Follow

admin.site.register(Follow)
admin.site.register(Block)
