from django.urls import path

from item.views.item import ItemModelViewSet
from item.views.tag import TagListAPIView


urlpatterns = [
    path("", ItemModelViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:pk>/", ItemModelViewSet.as_view(
        {
            "put": "update",
            "delete": "destroy",
            "patch": "partial_update",
            "get": "retrieve",
        }
    )),
    path("tags/", TagListAPIView.as_view()),
]
