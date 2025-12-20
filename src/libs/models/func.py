import math

from django.core.management.color import no_style
from django.db import connection, connections
from django.db.models import Avg, Count, Q, Sum


def sum_of(instance, related, field):
    """sum of related subfield"""
    res = getattr(instance, related).aggregate(sum=Sum(field)).get("sum", 0) or 0
    return round(res, 2)


def avg_of(instance, related, field):
    res = (
        getattr(
            instance,
            related,
        )
        .aggregate(avg=Avg(field))
        .get("avg", 0)
        or 0
    )
    return round(res, 2)


def count_of_filter(queryset, related_field, value, exp=""):
    """Filter by counting related_field , expression = "gte","lte" or ""=equal"""
    try:
        lookup = "count" if exp == "" else f"count__{exp}"
        return queryset.annotate(
            count=Count(
                related_field,
            )
        ).filter(Q(**{lookup: value}))
    except Exception as E:
        print(E)


def sum_of_filter(queryset, related_field, value, exp=""):
    """Filt by counting reversed fields , exp = "gte","lte" or ""=equal"""
    lookup = "sum" if exp == "" else f"sum__{exp}"

    return queryset.annotate(
        sum=Sum(
            related_field,
        )
    ).filter(Q(**{lookup: value}))


from django.conf import settings
from libs.utils.utils import rgetattrdict


def get_seq(instance, field="num", filters={}):
    if not getattr(instance, field):
        last = (
            instance._meta.model.objects.exclude(**{field: None})
            .filter(date__year=instance.date.year)
            .filter(**filters)
            .order_by(f"-{field}")
            .first()
        )

        if last and getattr(last, field) is not None:
            return getattr(last, field) + 1
        else:
            return rgetattrdict(
                settings.SEQUENCES,
                f"{instance.date.year}.{instance._meta.model.__name__}",
                1,
            )


from django.apps import apps


def all_apps():
    res = []
    all_ = apps.app_configs.keys()
    others = [
        "django_extensions",
        "django_filters",
        "polymorphic",
        "simple_history",
        "field_history",
        "humanize",
        "rest_framework",
        "refresh_token",
        "corsheaders",
        "admin",
        "auth",
        "contenttypes",
        "sessions",
        "messages",
        "staticfiles",
        "graphene_django",
        "corsheaders",
        "libs",
        "User",
    ]
    for a in all_:
        if a in others:
            continue
        res.append(a)
    return res


def all_models(app_name):
    if not app_name:
        return []
    models = []
    for m in list(apps.all_models[app_name].values()):
        model = apps.get_model(app_name, m.__name__)
        if getattr(model, "__name__", False):
            models.append(m)
    return models


def get_model(app, model):
    return apps.get_model(app, model)


def query(table):
    return f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id)+1 FROM {table}), 1), false);"


def sql(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchone()
    return row


def fix(seq):
    sequence_sql = connection.ops.sequence_reset_sql(no_style(), seq)
    with connection.cursor() as cursor:
        for sql in sequence_sql:
            cursor.execute(sql)


def fix_seq():
    for app in all_apps():
        try:
            fix(all_models(app))
        except Exception as E:
            print("exception", E)


def fix_model(app, name):
    model = apps.get_model(app, name)
    fix([model])


def clone_to_different_model(source_instance, target_model, exclude_fields=None):
    """
    Clone fields from a source instance to a target model instance.

    :param source_instance: The instance to clone from.
    :param target_model: The model class to clone to.
    :param exclude_fields: Fields to exclude during cloning.
    :return: The new instance of the target model.
    """
    exclude_fields = exclude_fields or []
    # Get the fields of the base model shared by both models
    base_fields = {field.name for field in source_instance._meta.fields}
    target_fields = {field.name for field in target_model._meta.fields}
    shared_fields = base_fields.intersection(target_fields) - set(exclude_fields)

    # Create an instance of the target model
    new_instance = target_model()
    for field in shared_fields:
        if field == "polymorphic_ctype" or "ptr" in field:
            continue
        setattr(new_instance, field, getattr(source_instance, field))

    return new_instance


"""
# Create an instance of ModelA
model_a_instance = ModelA.objects.create(
    common_field1="Test Value",
    common_field2=42,
    specific_field_a="Specific to ModelA"
)

# Clone ModelA instance to ModelB
model_b_instance = clone_to_different_model(
    source_instance=model_a_instance,
    target_model=ModelB,
    exclude_fields=['id']  # Exclude fields like `id` or other fields if needed
)

# Add specific field values for the target model if needed
model_b_instance.specific_field_b = '2025-01-21'
model_b_instance.save()

print(model_b_instance.common_field1)  # Output: Test Value
print(model_b_instance.common_field2)  # Output: 42
print(model_b_instance.specific_field_b)  # Output: 2025-01-21

"""


def clone_instance(instance, exclude_fields=None):
    """
    Clone a model instance, optionally excluding certain fields.

    :param instance: The model instance to clone.
    :param exclude_fields: List of field names to exclude during cloning.
    :return: The cloned instance.
    """
    exclude_fields = exclude_fields or []
    model = instance.__class__
    clone = model()

    for field in instance._meta.fields:
        if field.name not in exclude_fields and field.name != instance._meta.pk.name:
            setattr(clone, field.name, getattr(instance, field.name))

    clone.save()

    # Clone Many-to-Many fields
    for field in instance._meta.many_to_many:
        if field.name not in exclude_fields:
            related_manager = getattr(instance, field.name)
            getattr(clone, field.name).set(related_manager.all())

    return clone


## example
# original_instance = YourModel.objects.get(pk=1)
# cloned_instance = clone_instance(original_instance, exclude_fields=['created_at', 'updated_at'])
