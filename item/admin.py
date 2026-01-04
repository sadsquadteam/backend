from django.contrib import admin

from item.models.item import Item
from item.models.tag import Tag


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'status']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['title']
