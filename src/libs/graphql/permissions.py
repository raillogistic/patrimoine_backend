from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import resolve_url
from graphql import GraphQLError
from libs.utils.get_user import get_current_profile, get_current_user


def user_pass(test_func):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(*args, **kwargs):
            # print(args, kwargs)
            if test_func(args[0].context.user):
                return view_func(*args, **kwargs)
            raise GraphQLError("no_permissions")


def user_passes_test(
    test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if test_func(args[0].context.user):
                return view_func(args[0].context, *args, **kwargs)
            raise GraphQLError("no_permissions")
            # path = request.build_absolute_uri()
            # resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # # If the login url is the same scheme and net location then just
            # # use the path as the "next" url.
            # login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            # current_scheme, current_netloc = urlparse(path)[:2]
            # if (not login_scheme or login_scheme == current_scheme) and (
            #     not login_netloc or login_netloc == current_netloc
            # ):
            #     path = request.get_full_path()
            # from django.contrib.auth.views import redirect_to_login

            # return redirect_to_login(path, resolved_login_url, redirect_field_name)

        return _wrapper_view

    return decorator


def login_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def check_permission(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            print(permission_name, get_current_user().has_perm(permission_name))
            # Check if the user has the required permission
            if get_current_user().has_perm(permission_name):
                # User has the permission, proceed to the view
                return view_func(*args, **kwargs)
            else:
                raise GraphQLError("vous n'êtes pas autorisé à effectuer cette action")
                # User does not have the permission, return forbidden response
                # return HttpResponseForbidden("You do not have permission to access this resource.")

        return wrapper

    return decorator
    # not use wrappedFunc() becaues Because this function runs at the this time


# def check_permission(perm, ):
#     def check_perms(user):
#         if isinstance(perm, str):
#             perms = (perm,)
#         else:
#             perms = perm
#         # First check if the user has the permission (even anon users)
#         if user.has_perms(perms):
#             return True
#         # In case the 403 handler should be called raise the exception
#         # if raise_exception:
#         #     raise PermissionDenied
#         # As the last resort, show the login form
#         return user_pass(check_perms)


def permission_required(perm, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """

    def check_perms(user):
        if isinstance(perm, str):
            perms = (perm,)
        else:
            perms = perm
        # First check if the user has the permission (even anon users)
        # print(user)
        # if user.is_superuser:
        #     return True
        if user.has_perms(perms):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)


def is_owner(qs, profile):
    return qs.filter(owner=profile)


def get_all_sub_departments(top_department):
    all_sub_departments = []

    def traverse_department(department):
        nonlocal all_sub_departments
        all_sub_departments.append(department)

        for sub_department in department.structures.all():
            traverse_department(sub_department)

    traverse_department(top_department)
    return all_sub_departments


def sub_structures(qs, profile):
    return qs.filter(structure__in=get_all_sub_departments(profile.structure))


def get_sub_structures(qs, profile, accessor):
    return qs.filter(Q(**{accessor: get_all_sub_departments(profile.structure)}))


def same_structure(qs, profile):
    return qs.filter(structure=profile.structure)
