import graphene


class ModelType(graphene.ObjectType):
    app = graphene.String()
    name = graphene.String()
    fields = graphene.List(
        "libs.graphql.schema.custom.models.queries.types.FieldType.FieldType"
    )
