from django.db import models

from item.models.tag import Tag
from users.models import CustomUser


class Item(models.Model):
    STATUS_CHOICES = (
        ("lost", "Lost"),
        ("found", "Found"),
        ("delivered", "Delivered"),
    )

    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='items/')
    tags = models.ManyToManyField(to=Tag)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
