from django.urls import path

from interaction.views.comment import CommentModelViewSet

urlpatterns = [
    path("comments/", CommentModelViewSet.as_view(
        {
            "get": "list",
            "post": "create",
        }
    ), name="comment-list"),
    path("comments/<int:pk>/", CommentModelViewSet.as_view(
        {
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }
    ), name="comment-detail"),
]
