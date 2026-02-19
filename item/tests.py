from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from item.models.item import Item
from item.models.tag import Tag

User = get_user_model()


class ItemAPITestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email="x@gmail.com",
            password="password123"
        )
        self.user2 = User.objects.create_user(
            email="y@gmail.com",
            password="password123"
        )

        self.tag1 = Tag.objects.get(title="Electronic")
        self.tag2 = Tag.objects.get(title="Clothing")
        self.tag3 = Tag.objects.get(title="Card")

        self.item1 = Item.objects.create(
            creator=self.user1,
            title="Lost Phone",
            description="Black iPhone",
            latitude=40.0,
            longitude=40.0,
            status="lost"
        )
        self.item1.tags.add(self.tag1)

        self.item2 = Item.objects.create(
            creator=self.user2,
            title="Found Hat",
            description="Brown leather hat",
            latitude=50.0,
            longitude=50.0,
            status="found"
        )
        self.item2.tags.add(self.tag2, self.tag3)

        self.list_url = "/api/items/"
        self.detail_url = f"/api/items/{self.item1.id}/"

    def test_list_items_public_access(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_authenticated_user_can_create_item(self):
        self.client.force_authenticate(user=self.user1)

        payload = {
            "title": "Lost Card",
            "description": "Student card",
            "latitude": 10.0,
            "longitude": 20.0,
            "status": "lost",
            "tags": [self.tag3.id]
        }

        response = self.client.post(self.list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 3)

    def test_unauthenticated_user_cannot_create_item(self):
        payload = {
            "title": "Unauthorized Item",
            "description": "Should fail",
            "latitude": 10.0,
            "longitude": 20.0,
            "status": "lost",
        }

        response = self.client.post(self.list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_update_other_users_item(self):
        self.client.force_authenticate(user=self.user2)

        response = self.client.patch(
            self.detail_url,
            {"title": "Hacked Title"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_item_status(self):
        self.client.force_authenticate(user=self.user1)

        response = self.client.patch(
            self.detail_url,
            {"status": "delivered"},
            format="json"
        )

        self.item1.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.item1.status, "delivered")
        self.assertEqual(response.data["status"], "delivered")

    def test_filter_items_by_status(self):
        response = self.client.get(self.list_url + "?status=lost")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], "lost")

    def test_filter_items_by_tag_title(self):
        response = self.client.get(self.list_url, {"tags__title__icontains": "clothing"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Found Hat")

    def test_search_items_by_title(self):
        response = self.client.get(self.list_url, {"search": "Phone"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Lost Phone")
