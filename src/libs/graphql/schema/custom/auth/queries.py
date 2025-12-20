import graphene
from django.contrib.auth import get_user_model

from .types import UserType


class AuthQueries(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(
        UserType, include=graphene.List(graphene.String), quick=graphene.String()
    )
    # mysetting = graphene.Field(
    #     "libs.graphql.schema.types.ProfileSettingType",
    #     profile=graphene.ID(required=True),
    # )

    # def resolve_mysetting(self, info, profile):
    #     if str(profile) == str(get_current_user().profile.pk):
    #         return ProfileSetting.objects.get(profile=profile)

    def resolve_users(
        self,
        info,
    ):
        return get_user_model().objects.all().filter()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in!")
        return user
