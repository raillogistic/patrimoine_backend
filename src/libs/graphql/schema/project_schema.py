import graphene
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from graphene_file_upload.django import FileUploadGraphQLView

from .files import setupApps, updateGraphqlFiles

# create apropriate graphql files if they not exist
setupApps()
# update files based on model changing
updateGraphqlFiles()


from libs.graphql.schema.custom.models.queries.models import (
    ModelQueries,
    ModelsMutations,
)
from libs.graphql.schema.custom.reporting import DashboardQueries
from libs.reporting.mutations import Reporting

from .custom.auth.mutations import AuthMutations
from .custom.auth.queries import AuthQueries
from .mutations import Mutations, get_custom_mutations
from .queries import Queries, get_custom_queries
from .utils import get_class_by_name

ProjectQueries = type(
    "ProjectQueries",
    (
        *tuple([_class for name, _class in Queries.items()]),
        *get_custom_queries(),
        ModelQueries,
        DashboardQueries,
        AuthQueries,
    ),
    {"dummy": graphene.String()},
)
ProjectMutations = type(
    "ProjectMutations",
    (
        *tuple([_class for name, _class in Mutations.items()]),
        *get_custom_mutations(),
        ModelsMutations,
        AuthMutations,
        Reporting,
    ),
    {"dummy": graphene.String()},
)


import logging
import sys


class PrivateGraphQLUpladView(
    LoginRequiredMixin,
    FileUploadGraphQLView,
    # SentryGraphQLView,
):
    pass


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


class PrivateGraphQLUpladViewWithErrors(
    LoginRequiredMixin,
    FileUploadGraphQLView,
    SentryGraphQLView,
):
    pass


schema = graphene.Schema(
    query=ProjectQueries, mutation=ProjectMutations, auto_camelcase=False
)


def openGraphqlUrl(url, throw_error=False):
    if throw_error:
        return path(f"{url}", SentryGraphQLView.as_view(graphiql=True, schema=schema))
    return path(f"{url}", GraphQLView.as_view(graphiql=True, schema=schema))


def closedGraphqlUrl(url, throw_error=False):
    if throw_error:
        return path(
            f"{url}",
            csrf_exempt(
                PrivateGraphQLUpladViewWithErrors.as_view(graphiql=True, schema=schema)
            ),
        )
    return path(
        f"{url}",
        csrf_exempt(PrivateGraphQLUpladView.as_view(graphiql=True, schema=schema)),
    )


def graphql_url(url, isopen=False, throw_error=False, graphiql=False):
    graphqlClass = GraphQLView
    if isopen is True:
        graphqlClass = SentryGraphQLView if throw_error else GraphQLView
    else:
        graphqlClass = (
            PrivateGraphQLUpladViewWithErrors
            if throw_error
            else PrivateGraphQLUpladView
        )
    return path(
        f"{url}",
        csrf_exempt(graphqlClass.as_view(graphiql=graphiql, schema=schema)),
    )


def custom_schema(
    url, isopen=False, throw_error=False, graphiql=False, queries=[], mutations=[]
):
    custom_mutation = {}
    for m in mutations:
        try:
            custom_mutation[m] = ProjectMutations.__dict__["_meta"].__dict__["fields"][
                m
            ]
        except:
            pass
    custom_queries = {}
    for m in queries:
        try:
            custom_queries[m] = ProjectQueries.__dict__["_meta"].__dict__["fields"][m]
        except:
            pass

    CustomProjectMutations = type(
        "CustomProjectMutations",
        (graphene.ObjectType,),
        custom_mutation,
    )
    CustomProjectQueries = type(
        "CustomProjectQueries",
        (graphene.ObjectType,),
        custom_queries,
    )

    schema = graphene.Schema(
        query=CustomProjectQueries if len(custom_queries) > 0 else None,
        mutation=CustomProjectMutations if len(custom_mutation) > 0 else None,
        auto_camelcase=False,
    )

    graphqlClass = GraphQLView
    if isopen is True:
        graphqlClass = SentryGraphQLView if throw_error else GraphQLView
    else:
        graphqlClass = (
            PrivateGraphQLUpladViewWithErrors
            if throw_error
            else PrivateGraphQLUpladView
        )
    return path(
        f"{url}",
        csrf_exempt(graphqlClass.as_view(graphiql=graphiql, schema=schema)),
    )


from libs.graphql.schema.custom.auth.mutations import AuthMutations
from libs.graphql.schema.custom.auth.queries import AuthQueries

authSchema = graphene.Schema(
    auto_camelcase=False, query=AuthQueries, mutation=AuthMutations
)


def authGraphqlUrl(p):
    return path(p, csrf_exempt(GraphQLView.as_view(schema=authSchema, batch=False)))
