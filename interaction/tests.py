from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from interaction.models.comment import Comment
from interaction.models.report import Report
from item.models import Item

User = get_user_model()


class CommentViewSetTests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@gmail.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            email="user2@gmail.com", password="password123"
        )

        self.item = Item.objects.create(title="Test Item", creator=self.user1)

        self.comment1 = Comment.objects.create(
            user=self.user1,
            item=self.item,
            text="First comment",
        )

        self.comment2 = Comment.objects.create(
            user=self.user2,
            item=self.item,
            text="Second comment",
            replies_to=self.comment1,
        )
        self.list_url = reverse("comment-list")

    def test_list_comments(self):
        self.client.force_authenticate(self.user1)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_create_comment_assigns_user(self):
        self.client.force_authenticate(self.user1)

        data = {"item": self.item.id, "text": "New comment"}

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(id=response.data["id"])
        self.assertEqual(comment.user, self.user1)

    def test_user_cannot_update_other_users_comment(self):
        self.client.force_authenticate(self.user1)

        url = reverse("comment-detail", args=[self.comment2.id])
        response = self.client.patch(url, {"text": "Updated text"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_update_own_comment(self):
        self.client.force_authenticate(self.user1)

        url = reverse("comment-detail", args=[self.comment1.id])
        response = self.client.patch(url, {"text": "Updated text"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment1.refresh_from_db()
        self.assertEqual(self.comment1.text, "Updated text")

    def test_user_cannot_delete_other_users_comment(self):
        self.client.force_authenticate(self.user1)

        url = reverse("comment-detail", args=[self.comment2.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reply_to_comment(self):
        self.client.force_authenticate(self.user1)

        data = {
            "item": self.item.id,
            "text": "Reply comment",
            "replies_to": self.comment2.id,
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reply = Comment.objects.get(id=response.data["id"])
        self.assertEqual(reply.replies_to, self.comment2)

    def test_created_at_is_read_only(self):
        self.client.force_authenticate(self.user1)

        data = {
            "item": self.item.id,
            "text": "Attempt override timestamp",
            "created_at": "2000-01-01T00:00:00Z",
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comment = Comment.objects.get(id=response.data["id"])
        self.assertNotEqual(str(comment.created_at), "2000-01-01T00:00:00Z")


class ReportAPITestCase(APITestCase):
    """Test cases for the Report API endpoints."""

    def setUp(self):
        """Set up basic data for report tests."""
        self.creator = User.objects.create_user(
            email="creator@uni.edu", password="Password123!"
        )
        self.item = Item.objects.create(title="Lost Wallet", creator=self.creator)

        self.reporter = User.objects.create_user(
            email="reporter@uni.edu", password="Password123!"
        )

        self.report_url = reverse("create-report")

    def test_create_report_success(self):
        """Test creating a report successfully with an authenticated user."""
        self.client.force_authenticate(user=self.reporter)
        data = {"item": self.item.id, "reason": "SPAM"}
        response = self.client.post(self.report_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.first().reason, "SPAM")

    def test_create_report_unauthenticated(self):
        """Test that unauthenticated users cannot create a report."""
        data = {"item": self.item.id, "reason": "SPAM"}
        response = self.client.post(self.report_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Report.objects.count(), 0)

    def test_create_report_missing_data(self):
        """Test creating a report with missing required fields."""
        self.client.force_authenticate(user=self.reporter)
        response = self.client.post(self.report_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_report_invalid_item(self):
        """Test creating a report for a non-existent item ID."""
        self.client.force_authenticate(user=self.reporter)
        data = {"item": 99999, "reason": "SPAM"}
        response = self.client.post(self.report_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_item_is_deleted_after_six_reports(self):
        """Test that an item is automatically deleted after receiving > 5 reports."""
        for i in range(1, 7):
            user = User.objects.create_user(
                email=f"testuser{i}@uni.edu", password="Password123!"
            )
            self.client.force_authenticate(user=user)

            response = self.client.post(
                self.report_url, {"item": self.item.id, "reason": "INAPPROPRIATE"}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        item_exists = Item.objects.filter(id=self.item.id).exists()
        self.assertFalse(item_exists, "Item should be deleted after 6 reports")
