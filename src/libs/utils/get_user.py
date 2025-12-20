from __future__ import absolute_import, division, print_function
from django.utils.cache import patch_vary_headers
from django.contrib.auth import authenticate
from graphql import GraphQLError

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def get_current_request():
    # return 1
    """ returns the request object for this thread """
    return getattr(_thread_locals, "request", None)

from libs.utils.utils import rgetattr

def get_current_profile():
    request = get_current_request()
    if request:
        return rgetattr(getattr(request, "user", None),'profile',None)

def get_current_user():
    """ returns the current user, if exist, otherwise returns None """
    request = get_current_request()
    if request:
        return getattr(request, "user", None)


class ThreadLocalMiddleware(object):
    """ Simple middleware that adds the request object in thread local stor    age."""

    # def process_request(self, request):
    #     _thread_locals.request = request

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # print("*********")
        user = authenticate(request=request)
        # print(user)
        _thread_locals.request = request
        return self.get_response(request)

    def process_response(self, request, response):
        # user = authenticate(request)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return self.get_response(request)


def can(*permissions):
    def wrapped_decorator(func):
        def inner(cls, info, *args, **kwargs):

            if not info.context:
                raise GraphQLError("Permission Denied.")

            user = info.context.user
            if not user.is_authenticated:
                raise GraphQLError("Permission Denied.")

            # An admin (Django superusers) can do everything.
            if user.is_superuser:
                return func(cls, info, **kwargs)
            # A user CAN perform an action, if he has ANY of the requested permissions.
            user_permissions = list(
                user.get_all_permissions()
            )
            print(user_permissions)
            if any(permission in user_permissions for permission in permissions):
                return func(cls, info, **kwargs)
            raise GraphQLError("Permission Denied.")

        return inner

    return wrapped_decorator
