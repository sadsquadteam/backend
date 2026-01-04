from rest_framework import serializers

from item.models.item import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            "id",
            "title",
            "description",
            "image",
            "tags",
            "status",
            "creator",
        ]
