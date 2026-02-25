from rest_framework.pagination import PageNumberPagination


class IssuePagination(PageNumberPagination):
    """
    Pagination for Issue list.
    """
    page_size = 10  # default page size
    page_size_query_param = "page_size"  # allows clients to set page size using query parameter
    max_page_size = 50  # maximum page size to prevent abuse


class UserPagination(PageNumberPagination):
    """
    Pagination for User list.
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CommentPagination(PageNumberPagination):
    """
    Pagination for Comment list.
    """
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50