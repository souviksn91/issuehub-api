from rest_framework import permissions


class IsReporterOrReadOnly(permissions.BasePermission):
    """
    Custom permission for Issue object.
    Controls:
    - Update
    - Archive
    - Assign
    - Status change
    """

    def has_object_permission(self, request, view, obj):
        """
        obj = the Issue instance
        view = current viewset
        """

        # SAFE METHODS = GET, HEAD, OPTIONS
        # Anyone authenticated can read
        if request.method in permissions.SAFE_METHODS:
            return True

        # If trying to update (PUT/PATCH)
        if view.action == "update" or view.action == "partial_update":
            return obj.reporter == request.user

        # Archive action
        if view.action == "archive":
            return obj.reporter == request.user

        # Assign action
        if view.action == "assign":
            return obj.reporter == request.user

        # Change status action
        if view.action == "change_status":
            return obj.assignee == request.user

        return False




class IsCommentAuthor(permissions.BasePermission):
    """
    Only comment author can edit or delete comment.
    """

    def has_object_permission(self, request, view, obj):

        # Anyone authenticated can read
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only author can modify
        return obj.author == request.user
