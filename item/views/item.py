from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters

from item.models.item import Item
from item.serializers.item import ItemSerializer


class ItemModelViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = {
        'creator': ['exact'],
        'status': ['exact'],
        'tags': ['exact'],
        'tags__title': ['exact', 'icontains'],
        'created_at': ['gt', 'gte', 'lt', 'lte'],
    }

    search_fields = ['title', 'description']

    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.method == "GET":
            return Item.objects.all()
        return Item.objects.filter(creator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
