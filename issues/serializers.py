from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from .models import Issue, Comment


# get the currently default Django User model
User = get_user_model()


# serializer for user registration
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    # extra field for confirming password
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User

        # fields exposed in registration
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
        ]

        # fields that are write-only (not returned in API responses)
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, data):  
        """
        Custom validation to check if passwords match.
        """
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data  # return the validated data to be used in create()
    
    # custom validation for email field to ensure uniqueness
    def validate_email(self, value):
        """
        Ensure email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
        

    def create(self, validated_data):
        """
        Create user properly with hashed password.
        """

        # remove password2 (not part of User model)
        validated_data.pop("password2")

        # create user using Django's create_user() method
        # this will handle hashing the password and saving the user instance
        user = User.objects.create_user(**validated_data)

        return user  # return the created user instance to be used in the view's response if needed




# serializer for listing users 
class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users.
    Shows only username and full name.
    """
    # custom field to combine first and last name 
    full_name = serializers.SerializerMethodField()  

    class Meta:
        model = User
        fields = ["username", "full_name"]

    # method to compute full name from first and last name
    def get_full_name(self, obj):  
        """
        Combine first_name and last_name.
        """
        return f"{obj.first_name} {obj.last_name}".strip()  




# serializer for Issue model
class IssueSerializer(serializers.ModelSerializer):  
    """
    IssueSerializer is used for:
    - creating issues
    - updating issues (reporter only, enforced via permissions)
    - listing issues
    - retrieving issue details
    """

    # show reporter as username in API response
    # ReadOnlyField means client cannot send or modify it
    reporter = serializers.ReadOnlyField(source="reporter.username")

    # allows assigning a user by sending their UUID primary key
    # queryset used to validate the user exists
    # required=False means it is not mandatory during creation
    # allow_null=True means it can be empty
    assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:

        model = Issue

        # fields exposed to API
        fields = [
            "id",
            "title",
            "description",
            "reporter",
            "assignee",
            "status",
            "priority",
            "is_archived",
            "created_at",
            "updated_at",
        ]
        # fields cannot be modified
        read_only_fields = (
            "id",
            "status",  # reporter cannot change status directly
            "is_archived",  # cannot archive via normal update
            "created_at",
            "updated_at",
        )

    # runs when a new issue is created via POST /api/issues/
    def create(self, validated_data):
        # get the current user from the request context
        request = self.context["request"]
        # force current user to be the reporter
        validated_data["reporter"] = request.user
        # call the default create method to save the issue instance
        return super().create(validated_data)
    
    # runs when updating an issue via PATCH /api/issues/{id}/
    def update(self, instance, validated_data):
        # prevent any updates if the issue is archived
        if instance.is_archived:
            raise serializers.ValidationError("Archived issues cannot be modified.")
        # allow normal updates for non-archived issues
        return super().update(instance, validated_data)





class AssignIssueSerializer(serializers.Serializer):
    """
    Used only for assigning an issue to a user.
    this is NOT a ModelSerializer because we only need one field.
    """

    # expect client to send assignee ID in the request body
    assignee_id = serializers.IntegerField()

    # custom validation logic
    def validate(self, data):
        # get issue object from context (passed from view)
        issue = self.context["issue"]

        # prevent assigning archived issue
        if issue.is_archived:
            raise serializers.ValidationError("Cannot assign an archived issue.")
        
        # try fetching user from database
        try:
            user = User.objects.get(id=data["assignee_id"])  
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        
        # set the user object as assignee in the validated data to be used in the view
        data["assignee"] = user  

        return data  




class ChangeStatusSerializer(serializers.Serializer):
    """
    Used only for changing issue status.
    """

    # only allow values defined in Issue.Status choices
    status = serializers.ChoiceField(choices=Issue.Status.choices)

    def validate(self, data):
        # get issue object from context (passed from view)
        issue = self.context["issue"]

        # prevent status change if archived
        if issue.is_archived:
            raise serializers.ValidationError("Cannot modify an archived issue.")
        
        # prevent status change if no assignee exists
        if not issue.assignee:
            raise serializers.ValidationError("Issue must have an assignee before changing status.")

        return data



class CommentSerializer(serializers.ModelSerializer):
    """
    Used for:
    - creating comments
    - updating comments
    - listing comments
    """

    # show author's username (read-only)
    author = serializers.ReadOnlyField(source="author.username")
    # issue will be set automatically from view, so it's read-only here
    issue = serializers.UUIDField(read_only=True)

    class Meta:

        model = Comment

        fields = [
            "id",
            "issue",
            "author",
            "content",
            "created_at",
        ]
        # fields cannot be modified
        read_only_fields = (
            "id",
            "author",
            "created_at",
        )

    # runs when creating a comment
    def create(self, validated_data):
        # get request from context to access current user
        request = self.context["request"]  # request has
        # get issue object from context (passed from view)
        issue = self.context["issue"]

        # prevent commenting on archived issues
        if issue.is_archived:
            raise serializers.ValidationError("Cannot comment on archived issue.")
        
        # force author to be current user
        validated_data["author"] = request.user
        # associate comment with the correct issue
        validated_data["issue"] = issue
        return super().create(validated_data)
    
    # runs when updating a comment
    def update(self, instance, validated_data):
        # prevent editing comment if issue is archived
        if instance.issue.is_archived:
            raise serializers.ValidationError("Cannot edit comment of archived issue.")
        return super().update(instance, validated_data)
