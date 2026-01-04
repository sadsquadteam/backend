from rest_framework import generics, permissions

from item.models.tag import Tag
from item.serializers.tag import TagSerializer


class TagListAPIView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]