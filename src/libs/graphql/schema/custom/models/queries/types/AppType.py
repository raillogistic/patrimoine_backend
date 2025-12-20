import graphene


class AppType(graphene.ObjectType):
    name = graphene.String()
    models = graphene.List(
        "libs.graphql.schema.custom.models.queries.types.ModelType.ModelType"
    )
