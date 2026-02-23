from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import IssueViewSet, CommentViewSet, RegisterView

# Main router for issues
router = DefaultRouter()
router.register(r'issues', IssueViewSet, basename='issue')

# Nested router for comments under issues
issues_router = NestedDefaultRouter(router, r'issues', lookup='issue')
issues_router.register(r'comments', CommentViewSet, basename='issue-comments')

# Combine both router URL patterns
urlpatterns = router.urls + issues_router.urls


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
] + router.urls + issues_router.urls