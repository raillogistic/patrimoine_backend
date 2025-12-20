from libs.graphql.serializers import CustomSerializer
from libs.models.fields import get_reversed_m2m_names
from rest_framework.serializers import PrimaryKeyRelatedField

# transactions = PrimaryKeyRelatedField(label='Factures/Transactions', many=True, queryset=Transaction.objects.all(), required=False)
from .utils import get_class_by_name, userapps


def createSerializer(model):
    def createMeta():
        attr = {"model": model, "fields": "__all__"}
        meta_class = type("MetaClass", (), attr)
        return meta_class

    m2ms = {}
    for m in get_reversed_m2m_names(model):
        m2ms[m.name] = PrimaryKeyRelatedField(
            label=m.field.verbose_name,
            many=True,
            queryset=m.model.objects.all(),
            required=False,
            write_only=True,
        )

    model_name = model.__name__
    class_name = f"{model_name}Serializer"
    inherit_from = get_class_by_name(
        f"{model._meta.app_label}.graphqls.serializers",
        f"{model.__name__}CustomSerializer",
    )
    return type(class_name, (inherit_from,), {"Meta": createMeta(), **m2ms})


from libs.utils.utils import register_module

from .utils import sorted_models

module_name = __name__
ProjectSerializers = {}

for model in sorted_models():
    if getattr(model._meta, "abstract", False):
        continue
    _mutations = []
    cls = createSerializer(
        model,
    )
    ProjectSerializers[model.__name__] = cls
    register_module(
        module_name,
        cls,
        f"{model.__name__}Serializer",
    )

__all__ = ProjectSerializers
