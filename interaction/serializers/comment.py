from rest_framework import serializers

from interaction.models.comment import Comment


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.id")

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "item",
            "text",
            "replies_to",
            "created_at",
        ]
        read_only_fields = [
            "created_at",
        ]
