import graphene


class RelatedFieldType(graphene.ObjectType):
    model = graphene.Field(
        "libs.graphql.schema.custom.models.queries.types.ModelType.ModelType"
    )
    fields = graphene.List(
        "libs.graphql.schema.custom.models.queries.types.FieldType.FieldType"
    )
