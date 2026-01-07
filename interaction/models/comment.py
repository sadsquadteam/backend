from django.db import models

from item.models import Item
from users.models import CustomUser


class Comment(models.Model):
    user = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    item = models.ForeignKey(
        to=Item,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        to='self',
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.item}"
