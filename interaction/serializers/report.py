from rest_framework import serializers

from interaction.models.report import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "item", "comment", "reason", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        item = data.get("item")
        comment = data.get("comment")
        user = self.context["request"].user

        if item and comment:
            raise serializers.ValidationError(
                "You cannot report both an item and a comment at the same time."
            )

        if not item and not comment:
            raise serializers.ValidationError("An item ID or comment ID is required.")

        if item and Report.objects.filter(user=user, item=item).exists():
            raise serializers.ValidationError("You have already reported this item.")

        if comment and Report.objects.filter(user=user, comment=comment).exists():
            raise serializers.ValidationError("You have already reported this comment.")

        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
