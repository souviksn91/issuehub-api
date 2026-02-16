from django.contrib import admin
from .models import Issue, Comment

# Register your models here.


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "reporter",
        "assignee",
        "status",
        "priority",
        "is_archived",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "is_archived",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "issue",
        "author",
        "created_at",
    )

    search_fields = (
        "content",
    )

    readonly_fields = (
        "created_at",
    )
