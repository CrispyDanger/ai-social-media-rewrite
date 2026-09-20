from rest_framework.pagination import PageNumberPagination


class SpacePagination(PageNumberPagination):
    page_size = 20
