import graphene
import graphql_jwt
from django.contrib.auth.models import Permission, User
from django.core.mail import send_mail
from libs.utils.get_user import get_current_user


class EmailMutation(graphene.Mutation):
    class Input:
        body = graphene.String()
        title = graphene.String()
        to = graphene.List(graphene.String)

    ok = graphene.Boolean()

    def mutate(self, info, body, title, to):
        # message = (title, body, 'miliakhaled@gmail.com', to)
        send_mail(
            title,
            body,
            "erp@rail-logistic.dz",
            to,
            fail_silently=False,
        )

        # message1 = ('Subject here', 'Here is the message',
        # 'miliakhaked@gmail.com', ["miliakhaled@gmail.com"])
        # v = send_mass_mail((message, message), fail_silently=False)
        return EmailMutation(ok=True)


class CustomProfileInput(graphene.InputObjectType):
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    username = graphene.String()
    password = graphene.String()
    job = graphene.String(required=False)
    structure = graphene.ID(required=False)
    user_type = graphene.String()
    worker = graphene.String()


class EmailMutations(graphene.ObjectType):
    send_mail = EmailMutation.Field()


class ChangePasswordMutation(graphene.Mutation):
    class Input:
        user = graphene.ID(required=True)
        new_password = graphene.String(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, user, new_password):
        try:
            u = User.objects.get(pk=user)
            if u is not None:
                u.set_password(new_password)
                u.save()
        except Exception as ex:
            print("error", ex)
            return ChangePasswordMutation(ok=False)
        return ChangePasswordMutation(ok=True)


class ChangeUsernameMutation(graphene.Mutation):
    class Input:
        user = graphene.ID(required=True)
        new_username = graphene.String(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, user, new_username):
        try:
            u = User.objects.get(pk=user)
            if u is not None:
                u.username = new_username
                u.save()
        except Exception as ex:
            print("error", ex)
            return ChangeUsernameMutation(ok=False)
        return ChangeUsernameMutation(ok=True)


class EmailMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Input:
        to = graphene.String()

    def mutate(self, info, to):
        send_mail(
            "Test",
            "Test Body",
            "erp@rail-logistic.dz",
            (to,),
            fail_silently=False,
        )

        # message1 = ('Subject here', 'Here is the message',
        #             'miliakhaked@gmail.com', ["miliakhaled@gmail.com"])
        # v = send_mass_mail((message, message), fail_silently=False)
        return EmailMutation(ok=True)


class AuthMutations(graphene.ObjectType):
    send_mail = EmailMutation.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token = graphql_jwt.Revoke.Field()
    change_password = ChangePasswordMutation.Field()
    change_username = ChangeUsernameMutation.Field()
    send_email = EmailMutation.Field()
