import functools

from django import template

register = template.Library()


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


def rgetattr_(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("__"))


@register.filter(name="get")
def get(d, k):
    res = rgetattr(d, k, None)
    try:
        if d.get(k, "-"):
            return d.get(k, "-")
    except Exception as E:
        pass
    if res is None:
        return " - "
    return res


@register.filter(name="get_field")
def get_field(d, k):
    res = rgetattr_(d, k, None)
    if res is None:
        return " - "
    return res


@register.filter(name="or")
def resolve_or(d, k):
    if d is None:
        return k
    if type(d) == str:
        if len(d.trim()) == 0:
            return k
    return d


@register.filter(name="add_len")
def resolve_add_len(list, add):
    if list is None:
        return 0

    return len(list) + 1
