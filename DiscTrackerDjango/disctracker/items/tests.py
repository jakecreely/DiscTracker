from django.test import TestCase
from django.urls import reverse

# Create your tests here.
class ItemIndexViewTests(TestCase):
    def test_no_items(self):
        """
        If no items exist, an appropriate message is displayed
        """
        response = self.client.get(reverse("items:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No items are available.")
        self.assertQuerySetEqual(response.context["items_list"], [])