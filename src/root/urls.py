import logging
import sys

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView, graphene_settings
from graphene_file_upload.django import FileUploadGraphQLView
from graphql.error import GraphQLError

from libs.graphql.schema.project_schema import (
    authGraphqlUrl,
    closedGraphqlUrl,
    custom_schema,
    graphql_url,
    openGraphqlUrl,
    schema,
)
from libs.models.backup import download_database_sql

from . import views


class SentryGraphQLView(GraphQLView):
    def resolve(self, next, root, info, **args):
        try:
            return next(root, info, **args)
        except:
            err = sys.exc_info()
            logging.error(err)
            return err[1]

    def execute_graphql_request(self, *args, **kwargs):
        """Extract any exceptions and send them to Sentry"""
        result = super().execute_graphql_request(*args, **kwargs)
        if result.errors:
            for error in result.errors:
                try:
                    raise error.original_error
                except Exception as e:
                    raise
                    # err = sys.exc_info()
                    # logging.error(err)

        return result


# SentryGraphQLView


class PrivateGraphQLUpladView(
    LoginRequiredMixin,
    FileUploadGraphQLView,
    # SentryGraphQLView,
):
    pass


class GQLView(GraphQLView):
    def __init__(self, *args, **kwargs):
        # note the extra list level
        kwargs.update({"middleware": [graphene_settings.MIDDLEWARE]})
        super().__init__(*args, **kwargs)


urlpatterns = [
    # path("gql", csrf_exempt(PrivateGraphQLUpladView.as_view(batch=False))),
    graphql_url("gql", throw_error=False),
    graphql_url("graphiql", throw_error=False, isopen=True, graphiql=True),
    # openGraphqlUrl("graphiql", throw_error=True),
    # closedGraphqlUrl("gql", throw_error=False),
    authGraphqlUrl("auth"),
    # path(r"graphiql", SentryGraphQLView.as_view(graphiql=True, schema=schema)),
    ##############################
    path("admin/", admin.site.urls),
    path("export/csv/<url>", views.export),
    # path("models/", include("models.urls")),
    path(r"not_found", csrf_exempt(views.not_found), name="not_found"),
    path("login/", csrf_exempt(views.login), name="login"),
    path("export/csv/<url>", views.export),
    path("upload/", csrf_exempt(views.upload)),
    path("data/import", csrf_exempt(views.import_model)),
    # apps
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = urlpatterns + static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
