
from graphene import Mutation
import graphene
from libs.graphql.graphene_django_extras.registry import get_global_registry
from libs.graphql.graphene_django_extras.converter import construct_fields
from graphene.types.utils import yank_fields_from_attrs


class BatchMutation(Mutation):

    def __init__(
        self,
        model,
        basic_mutation,
    ):
        self.basic_mutation = basic_mutation
        self.model = model

    def mutate(self, info, input, quantity=1):
        res = BatchMutation(ok=True)
        try:
            for l in range(quantity):
                l = {"input": {**input}}
                res = self.basic_mutation.create(self, info, **l)
        except Exception as e:
            return GraphQLError(str(e))
            # created = OurLivraison.objects.create(**l)
        return res
