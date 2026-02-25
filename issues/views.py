from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import MethodNotAllowed
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter



from .models import Issue, Comment
from .serializers import (
    IssueSerializer,
    AssignIssueSerializer,
    ChangeStatusSerializer,
    CommentSerializer,
    RegisterSerializer,
    UserListSerializer,
)
from .permissions import IsReporterOrReadOnly, IsCommentAuthor
from .pagination import IssuePagination, UserPagination, CommentPagination


User = get_user_model()



# REGISTRATION API VIEW
class RegisterView(APIView):
    """
    API endpoint for user registration.
    """

    # anyone can access this endpoint (even without authentication)
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,  # tells Swagger what input looks like
        responses={201: None}        # response type
    )

    def post(self, request):
        # pass request data to serializer
        serializer = RegisterSerializer(data=request.data)
        # validate input data
        serializer.is_valid(raise_exception=True)
        # calls the create() method in RegisterSerializer which creates the user instance and saves it to the database
        serializer.save()  

        return Response(
            {
                "message": "User registered successfully.",
                "username": serializer.data["username"]
            },
            status=status.HTTP_201_CREATED
        )



# USER VIEWSET
# read-only viewset that provides list and retrieve actions for users
# no create/update/delete allowed for users through this endpoint
class UserViewSet(viewsets.ReadOnlyModelViewSet):  
    """
    Read-only endpoint to list all non-superuser users.
    Only authenticated users can access.
    """

    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UserPagination

    def get_queryset(self):
        # exclude superusers from the list of users
        return User.objects.filter(is_superuser=False)



# ISSUE VIEWSET
class IssueViewSet(viewsets.ModelViewSet):
    """
    This ModelViewSet automatically provides:
    - list() - GET /issues/
    - retrieve() - GET /issues/{id}/
    - create() - POST /issues/
    - update() - PUT /issues/{id}/
    - partial_update() - PATCH /issues/{id}/
    - destroy() - DELETE /issues/{id}/
    We will also add custom actions:
    - assign
    - change_status
    - archive
    """

    # base queryset for this viewset
    queryset = Issue.objects.select_related("reporter", "assignee")  # optimize queries by fetching related reporter and assignee in the same query
    # default serializer for normal CRUD operations
    serializer_class = IssueSerializer
    # permission class for object-level permission checks
    permission_classes = [IsAuthenticated, IsReporterOrReadOnly]  # only authenticated users can access
    # use custom pagination class for issues
    pagination_class = IssuePagination  

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'assignee', 'reporter', 'is_archived']  # allows filtering by these fields using query parameters
    search_fields = ['title', 'description']  # allows searching by title and description
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']  # allows ordering by these fields 
    ordering = ['-created_at']  # default ordering by creation date descending

    # allows to modify the context passed to serializers 
    # (e.g. to include the current user or the issue object for custom actions)
    def get_serializer_context(self):
        # call parent method to get default context which includes {"request": request, "format": format, "view": view}
        context = super().get_serializer_context()

        return context  # return the context to send to serializers
    

    # override destroy method to prevent deletion of issues
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE")

    # -----------------------------------------
    # custom action: assign issue to a user
    # endpoint: POST /issues/{id}/assign/ (where {id} is the issue UUID)
    @extend_schema(request=AssignIssueSerializer)  # tells Swagger that this endpoint expects input defined by AssignIssueSerializer
    @action(detail=True, methods=["post"])  
    def assign(self, request, pk=None):  # pk is the issue UUID from the URL

        # get the Issue object based on URL UUID
        issue = self.get_object()  

        # create serializer instance
        # pass request data and issue object via context to serializer for validation
        serializer = AssignIssueSerializer(
            data=request.data,  # data=request.data contains the assignee UUID sent by client in the request body
            context={"issue": issue}  # pass issue object 
        )

        # validate incoming data
        # if invalid, raises 400 with error details
        serializer.is_valid(raise_exception=True)  

        # after validation, get the cleaned user object
        issue.assignee = serializer.validated_data["assignee"]

        # save issue with new assignee
        issue.save()

        # return success response
        return Response(
            {"detail": "Issue assigned successfully."},
            status=status.HTTP_200_OK
        )


    # -----------------------------------------
    # custom action: change status of the issue
    # endpoint: POST /issues/{id}/change_status/
    @extend_schema(request=ChangeStatusSerializer)  # tells Swagger what input looks like for this endpoint
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):

        # get Issue object from database
        issue = self.get_object()

        # create serializer for status change 
        serializer = ChangeStatusSerializer(
            data=request.data,
            context={"issue": issue}
        )

        # validate input data
        serializer.is_valid(raise_exception=True)

        # update status using validated value
        issue.status = serializer.validated_data["status"]

        # save issue with new status
        issue.save()

        return Response(
            {"detail": "Status updated successfully."},
            status=status.HTTP_200_OK
        )


    # -----------------------------------------
    # custom action: archive the issue
    # endpoint: POST /issues/{id}/archive/
    @action(detail=True, methods=["post"], serializer_class=None)  # None means no input expected in request body
    def archive(self, request, pk=None):

        issue = self.get_object()

        # if already archived, return error
        if issue.is_archived:
            return Response(
                {"detail": "Issue already archived."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # mark issue as archived
        issue.is_archived = True

        # save changes
        issue.save()

        return Response(
            {"detail": "Issue archived successfully."},
            status=status.HTTP_200_OK
        )







# COMMENT VIEWSET
class CommentViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD for comments.
    Comments are nested under issues.
    Example endpoint: POST /issues/{issue_id}/comments/
    """
    # serializer for comments
    serializer_class = CommentSerializer
    # permission class
    permission_classes = [IsCommentAuthor]
    # pagination class for comments
    pagination_class = CommentPagination

    def get_queryset(self):
        """
        Return only comments belonging to the specific issue.
        """
        # get issue_pk from URL
        issue_id = self.kwargs.get("issue_pk")
        # filter comments by issue
        # optimize queries by fetching related author and issue in the same query
        return Comment.objects.filter(issue__id=issue_id).select_related("author", "issue")
        # return Comment.objects.filter(issue__id=issue_id) 

    # override serializer context to include issue object when creating a comment
    def get_serializer_context(self):
        # get default context from parent method which is {"request": request, "format": format, "view": view}
        context = super().get_serializer_context()  

        # if creating a comment (i.e. POST /issues/{issue_pk}/comments/)
        if self.action == "create":
            # first get the issue_id from URL kwargs 
            issue_id = self.kwargs.get("issue_pk")  # issue_id is passed as issue_pk in the URL conf for nested routes
            # fetch issue safely using that issue_id, if not found return 404
            issue = get_object_or_404(Issue, pk=issue_id)
            # add issue object to context so that serializer can associate comment with the correct issue
            context["issue"] = issue
        
        # return the modified context to be used by serializers
        return context  # context contains {"request": request, "format": format, "view": view, "issue": issue (only for create action)}
