from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Issue

User = get_user_model()


class IssueHubAPITest(APITestCase):

    # set up test users and any necessary data
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username="user1",
            password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="pass123"
        )

    # helper method to authenticate a user
    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # test issue creation by authenticated user
    def test_issue_creation(self):
        self.authenticate(self.user1)

        url = reverse("issue-list")

        data = {
            "title": "Test Issue",
            "description": "Testing issue creation",
            "priority": "high"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Issue.objects.count(), 1)
    
    # test that only the reporter can assign an issue to someone
    def test_only_reporter_can_assign(self):
        issue = Issue.objects.create(
            title="Test",
            description="Test desc",
            reporter=self.user1,
            priority="low"
        )

        self.authenticate(self.user2)

        url = reverse("issue-assign", args=[issue.id])

        response = self.client.post(url, {"assignee_id": self.user2.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    # test that only the assignee can change the status of an issue
    def test_assignee_can_change_status(self):  
        issue = Issue.objects.create(
            title="Test",
            description="Test desc",
            reporter=self.user1,
            assignee=self.user2,
            priority="low"
        )

        self.authenticate(self.user2)

        url = reverse("issue-change-status", args=[issue.id])

        response = self.client.post(url, {"status": "in_progress"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # test that a non-assignee cannot change the status of an issue
    def test_non_assignee_cannot_change_status(self):
        issue = Issue.objects.create(
            title="Test",
            description="Test desc",
            reporter=self.user1,
            assignee=self.user2,
            priority="low"
        )

        self.authenticate(self.user1)

        url = reverse("issue-change-status", args=[issue.id])

        response = self.client.post(url, {"status": "in_progress"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)