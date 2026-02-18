from rest_framework import permissions

# custom permission for Issue object
class IsReporterOrReadOnly(permissions.BasePermission):  
    """
    IsReporterOrReadOnly controls:
    - Update
    - Archive
    - Assign
    - Status change
    """

    # param request: the HTTP request, obj: the Issue instance, view: current viewset, 
    def has_object_permission(self, request, view, obj): 

        # SAFE METHODS = GET, HEAD, OPTIONS
        # anyone authenticated can read
        if request.method in permissions.SAFE_METHODS:
            return True

        # if trying to update (PUT/PATCH)
        if view.action == "update" or view.action == "partial_update":
            # only returns True if current user is the reporter of the issue
            return obj.reporter == request.user

        # if trying to archive the issue
        if view.action == "archive":  # archive action is defined in the viewset
            return obj.reporter == request.user

        # if trying to assign the issue to someone
        if view.action == "assign":  
            return obj.reporter == request.user

        # if trying to change status of the issue
        if view.action == "change_status":  
            # only assignee can change status
            return obj.assignee == request.user  
        
        # default deny for any other actions not explicitly handled above
        return False  



# custom permission for Comment object
class IsCommentAuthor(permissions.BasePermission):
    """
    Only comment author can edit or delete comment.
    """

    def has_object_permission(self, request, view, obj):

        # anyone authenticated can read
        if request.method in permissions.SAFE_METHODS:
            return True

        # only author can modify
        return obj.author == request.user
