import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from graphene import relay

# from raillogistic.graphene.graphene import CustomDjangoObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter.filterset import FilterSet
from graphql_relay import to_global_id
from libs.graphql.types import CustomConnection, CustomDjangoObjectType


class UserFilterClass(FilterSet):
    class Meta:
        fields = {}


from django.contrib.auth.models import User
from libs.graphql.schema.types import ProjectTypes
from libs.models.fields import get_reversed_onetoone_fields


def get():
    res = {}
    for f in get_reversed_onetoone_fields(User):
        model = f.related_model
        _type = ProjectTypes.get(f"{model.__name__}Type", None)
        if _type:
            res[f.name] = graphene.Field(_type)
    return res
    # res[t.rela] =


# _class = type("UserRelatedClasses", (graphene.ObjectType,), {**get()})


class UserType(CustomDjangoObjectType):
    permissions = graphene.List(graphene.String)
    groups = graphene.List(graphene.String)
    permission_by_model = graphene.List(graphene.String)
    name = graphene.String()
    designation = graphene.String()
    # id = graphene.ID()

    class Meta:
        name = "User"
        connection_class = CustomConnection()
        interfaces = (relay.Node,)

        model = get_user_model()
        filterset_class = UserFilterClass

    # def resolve_id(self, info):
    #     return to_global_id(self.id)

    def resolve_name(self, info):
        if len(self.first_name) == 0 and len(self.last_name) == 0:
            return self.username
        return f"{self.first_name} {self.last_name}"

    def resolve_designation(self, info):
        if len(self.first_name) == 0 and len(self.last_name) == 0:
            return self.username
        return f"{self.first_name} {self.last_name}"

    def resolve_groups(self, info):
        return self.groups.all().values_list("name", flat=True)

    def resolve_permissions(self, info):
        return self.get_all_permissions()
