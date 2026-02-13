from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        Override pagination to bypass it if pagination query parameters are missing.
        This method checks if the request contains either a "page" parameter or the custom
        page size query parameter. If neither is present, pagination is bypassed and all results
        are returned.
        """

        qp = request.query_params
        if "page" not in qp and self.page_size_query_param not in qp:
            return None  # bypass pagination for this request
        return super().paginate_queryset(queryset, request, view)
