from rest_framework import serializers

from item.models.tag import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "title",
        ]
        read_only_fields = [
            "id",
            "title",
        ]
