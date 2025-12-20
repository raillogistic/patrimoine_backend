from graphene_django.filter import DjangoFilterConnectionField
from graphene.utils.str_converters import to_snake_case
from libs.graphql.filters import from_global_filter, from_global_filter_for_relay


class OrderedDjangoFilterConnectionField(DjangoFilterConnectionField):
    @classmethod
    def resolve_queryset(
        cls, connection, iterable, info, args, filtering_args, filterset_class
    ):

        new_args = from_global_filter_for_relay(
            filterset_class.__dict__['base_filters'], args, filterset_class._meta.model)
        # print(get_model_field(cls._meta.model, field_name),type(filterset_class))
        qs = super().resolve_queryset(
            connection, iterable, info, new_args, filtering_args, filterset_class
        )
        order = args.get("ordering", None)

        if order:
            if isinstance(order, str):
                snake_order = to_snake_case(order)
            else:
                snake_order = [to_snake_case(o) for o in order]

            # annotate counts for ordering
            for order_arg in snake_order:
                order_arg = order_arg.lstrip("-")
                annotation_name = f"annotate_{order_arg}"
                annotation_method = getattr(qs, annotation_name, None)
                if annotation_method:
                    qs = annotation_method()

            # override the default distinct parameters
            # as they might differ from the order_by params
            qs = qs.order_by(*snake_order).distinct()
        return qs
