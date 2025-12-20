import os

from .utils import get_modelbyname, get_parent_model, sorted_models, userapps


def createFolder(folder):
    try:
        to_directory = f"{folder}"
        if not os.path.isdir(to_directory):
            os.mkdir(to_directory)
    except Exception as e:
        print("xx", e)


def createFile(path):
    if os.path.exists(f"{path}"):
        return True
    file = open(f"{path}", "+w")
    file.close()


def read_file(path):
    # if doens't exist, create it
    if not os.path.exists(f"{path}"):
        createFile(path)
        return ""
    file = open(f"{path}", "r")
    content = file.read()
    file.close()
    return content


def write_filters(app):
    content = read_file(f"{app.name}/graphqls/filters.py")
    file = open(f"{app.name}/graphqls/filters.py", "+w")
    imports = f"""
from django.db.models import Q
from {app.name} import models
from django_filters import FilterSet,CharFilter,BooleanFilter
"""

    add = ""
    for model in app.get_models():
        parent = get_parent_model(model)
        if f"{model.__name__}CustomFilters" not in content:
            import_base = (
                f"from {parent._meta.app_label}.graphqls.filters import {parent.__name__}CustomFilters "
                if parent and parent._meta.abstract is not True
                else ""
            )
            add = f"""
{add}

#######  {model.__name__}  #########
{import_base}
{model.__name__.lower()}_quick = {{}}
{model.__name__.lower()}_filters = {{}}
class {model.__name__}CustomFilters({parent.__name__ + "CustomFilters," if import_base else ""}FilterSet):
    pass
"""
    if len(add) > 0:
        file.write(f"""
{imports if "from django_filters import FilterSet,CharFilter,BooleanFilter" not in content else ""}
{content}
{add}        
""")
    else:
        file.write(content)


def write_types(app):
    content = read_file(f"{app.name}/graphqls/types.py")

    # res = content
    file = open(f"{app.name}/graphqls/types.py", "+w")
    imports = "import graphene"
    # if "import graphene" not in res:
    #     res = f"{imports}" + "\n" + f"{res}"
    add = ""

    for model in app.get_models():
        if f"{model.__name__}CustomType" not in content:
            base = model.__bases__[0]
            import_base = ""

            if (
                base.__name__ == "HistoricalChanges"
                or base.__name__ == "Model"
                or base.__name__ == "PolymorphicModel"
                or base._meta.abstract is True
            ):
                inherit = "object"
            else:
                base_app = base.__module__.split(".")[0]
                if base_app == "simple_history":
                    continue

                inherit = f"{base.__name__}CustomType"
                import_base = (
                    f"from {base_app}.graphqls.types import {base.__name__}CustomType"
                    if base_app != model._meta.app_label
                    else ""
                )
            add = f"""
{add}
#######  {model.__name__}  #########
{import_base}
class {model.__name__}CustomType({inherit}):
    pass
"""

    if len(add) > 0:
        file.write(f"""
{imports if "import graphene" not in content else ""}
{content}
{add}        
""")
    else:
        file.write(content)


def write_serializers(app):
    content = read_file(f"{app.name}/graphqls/serializers.py")

    # res = content
    file = open(f"{app.name}/graphqls/serializers.py", "+w")
    imports = "from libs.graphql.serializers import CustomSerializer"
    # if "import graphene" not in res:
    #     res = f"{imports}" + "\n" + f"{res}"
    add = ""

    for model in app.get_models():
        if f"{model.__name__}CustomSerializer" not in content:
            base = model.__bases__[0]
            import_base = ""

            if (
                base.__name__ == "HistoricalChanges"
                or base.__name__ == "Model"
                or base.__name__ == "PolymorphicModel"
                or base._meta.abstract is True
            ):
                inherit = "CustomSerializer"
            else:
                base_app = base.__module__.split(".")[0]
                if base_app == "simple_history":
                    continue

                inherit = f"{base.__name__}CustomSerializer"
                import_base = (
                    f"from {base_app}.graphqls.serializers import {base.__name__}CustomSerializer"
                    if base_app != model._meta.app_label
                    else ""
                )
            add = f"""
{add}
#######  {model.__name__}  #########
{import_base}
class {model.__name__}CustomSerializer({inherit}):
    pass
"""

    if len(add) > 0:
        file.write(f"""
{imports if "from libs.graphql.serializers import CustomSerializer" not in content else ""}
{content}
{add}        
""")
    else:
        file.write(content)


###############################################
def write_resolver(app):
    def resolver(model):
        return f"""
def resolve_{model.__name__.lower()}_query(info,qs,**kwargs):
    return qs
"""

    content = read_file(f"{app.name}/graphqls/resolvers.py")
    file = open(f"{app.name}/graphqls/resolvers.py", "+w")
    imports = """
from django.core.exceptions import PermissionDenied
"""
    add = ""
    for model in app.get_models():
        if f"resolve_{model.__name__.lower()}_query" not in content:
            add = f"""
{add}
{resolver(model)}
"""
    if len(add) > 0:
        file.write(f"""
{imports if "from django.core.exceptions import PermissionDenied" not in content else ""}
{content}
{add}
""")
    else:
        file.write(content)


# def write_quick(app):
#     def resolver(model):
#         return f"{model.__name__.lower()}_quick = {{}}\n"

#     content = read_file(f"{app.name}/graphqls/quick.py")
#     file = open(f"{app.name}/graphqls/quick.py", "+w")
#     imports = """
# """
#     add = ""
#     for model in app.get_models():
#         if f"{model.__name__.lower()}_quick" not in content:
#             add = (
#                 add
#                 + f"""
# {resolver(model)}
# """
#             )
#     if len(add) > 0:
#         file.write(f"""
# {content}
# {add}
# """)
#     else:
#         file.write(content)
##############################################


def write_app_custom_schema(app):
    def resolver(app):
        return f"""
class {app.capitalize()}CustomQueries(graphene.ObjectType):
    pass

############################

class {app.capitalize()}CustomMutations(graphene.ObjectType):
    pass
"""

    exist = createFile(f"{app.name}/graphqls/custom_schema.py")
    if exist:
        return

    file = open(f"{app.name}/graphqls/custom_schema.py", "+w")
    file.write(f"""
import graphene
{resolver(app.name)}
""")


from django.conf import settings


def write_global_schema():
    def resolver():
        return f"""

"""

    root = ""
    urls = f"{settings.ROOT_URLCONF}".split(".")
    path = None
    if len(urls) > 0:
        path = urls[0]
    if path is None:
        return
    exist = createFile(f"{path}/global_schema.py")
    if exist:
        return

    file = open(f"{path}/global_schema.py", "+w")
    file.write(f"""
import graphene

class GlobalQueries(graphene.ObjectType):
    pass

class GlobalMutations(graphene.ObjectType):
    pass


""")


###############################################
def write_mutations(app):
    def resolver(model):
        reverse_fields = {
            f.name: f
            for f in model._meta.get_fields()
            if f.auto_created and not f.concrete
        }

        fields = list(
            filter(lambda x: x.name != "id" and x.name != "owner", model._meta.fields)
        )
        res = ""
        for name, field in reverse_fields.items():
            if name == "owner":
                continue
            if name == "polymorphic_ctype":
                continue

            res = res + f"#'{name}' : '{field.related_model.__name__}',\n"

        for field in fields:
            if field.name == "owner":
                continue
            if field.name == "polymorphic_ctype":
                continue
            if type(field).__name__ == "ForeignKey":
                res = res + f"#'{field.name}' : '{field.related_model.__name__}',\n"
            if type(field).__name__ == "OneToOneField":
                res = res + f"#'{field.name}' : '{field.related_model.__name__}',\n"

        return f"""
class {model.__name__}CustomMutation:
    nested = {{
        {res}
    }}
"""

    content = read_file(f"{app.name}/graphqls/mutations.py")
    file = open(f"{app.name}/graphqls/mutations.py", "+w")
    imports = """
"""
    add = ""
    for model in app.get_models():
        if f"{model.__name__}CustomMutation" not in content:
            add = f"""
{add}
{resolver(model)}
"""
    if len(add) > 0:
        file.write(f"""
{content}
{add}
""")
    else:
        file.write(content)


def updateGraphqlFiles():
    apps = list(filter(lambda app: app.name != "libs", userapps()))
    for app in apps:
        write_filters(app)
        write_types(app)
        write_resolver(app)
        # write_quick(app)
        write_app_custom_schema(app)
        write_mutations(app)
        write_serializers(app)


def setupApps():
    write_global_schema()
    for model in sorted_models():
        apps = list(filter(lambda app: app.name != "libs", userapps()))
        for app in apps:
            ## create apps
            createFolder(f"{app.name}/graphqls")
            createFile(f"{app.name}/graphqls/filters.py")
            createFile(f"{app.name}/graphqls/mutations.py")
            createFile(f"{app.name}/graphqls/types.py")
            createFile(f"{app.name}/graphqls/resolvers.py")
            createFile(f"{app.name}/graphqls/serializers.py")
