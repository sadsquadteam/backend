from django.contrib import admin

from interaction.models.comment import Comment
from interaction.models.report import Report


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "text")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "comment", "created_at")
    list_filter = ("created_at",)
    search_fields = ("reason", "user__username")
