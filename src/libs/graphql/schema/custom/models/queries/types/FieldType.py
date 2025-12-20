import graphene


class FieldType(graphene.ObjectType):
    name = graphene.String()
    _type = graphene.String()
    column = graphene.String()
    related = graphene.Field(
        "libs.graphql.schema.custom.models.queries.types.RelatedFieldType.RelatedFieldType"
    )
    null = graphene.Boolean()
    verbose_name = graphene.String()
    model = graphene.String()
