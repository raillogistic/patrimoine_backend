from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse
from django.utils.cache import patch_vary_headers
from graphql_jwt.exceptions import JSONWebTokenError
from graphql_jwt.utils import get_http_authorization


class JSONWebTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = authenticate(request)
        # Avoid JWT authentication for Admin site and GraphQL queries
        if not any(p in request.path_info for p in settings.IGNORE_GQL_AUTH):
            try:
                user = authenticate(request=request)
            except JSONWebTokenError as err:
                return JsonResponse(
                    {
                        "errors": [{"message": str(err)}],
                    },
                    status=401,
                )
            if user is not None:
                request.user = request._cached_user = user
                response = self.get_response(request)
                patch_vary_headers(response, ("Authorization",))
                return response

        else:
            response = self.get_response(request)
            patch_vary_headers(response, ("Authorization",))
            return response
        return JsonResponse(
            {
                "errors": [{"message": str("not authenticated")}],
            },
            status=401,
        )
