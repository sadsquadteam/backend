from django.conf import settings
from django.db import models

from interaction.models.comment import Comment
from item.models import Item


class Report(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_submitted",
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "item"], name="unique_user_item_report"
            ),
            models.UniqueConstraint(
                fields=["user", "comment"], name="unique_user_comment_report"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(item__isnull=False, comment__isnull=True)
                    | models.Q(item__isnull=True, comment__isnull=False)
                ),
                name="report_must_have_exactly_one_target",
            ),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            if self.item:
                if self.item.reports.count() > 5:
                    self.item.delete()
            elif self.comment:
                if self.comment.reports.count() > 5:
                    self.comment.delete()
