from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from interaction.models.comment import Comment
from interaction.serializers.comment import CommentSerializer


class CommentModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Comment.objects.all()
        else:
            return self.request.user.comments.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
