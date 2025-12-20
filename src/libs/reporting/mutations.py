import importlib
import os

import graphene
from django.apps import apps
from django.conf import settings
from libs.utils import resources
from libs.utils.get_user import get_current_request
from libs.utils.resources import StyledResource


class ExportFieldType(graphene.InputObjectType):
    name = graphene.String()
    title = graphene.String()


class ExportVariableType(graphene.InputObjectType):
    name = graphene.String()
    value = graphene.String()


class ExportPaginationType(graphene.InputObjectType):
    page = graphene.Int()
    rowPerPage = graphene.Int()
    ordering = graphene.String()


def create_resource(django_model, model_fields, order, props, headers):
    class model_resource(StyledResource):
        class Meta:
            map_properties = props
            model = django_model
            # fields = model_fields
            fields = model_fields
            export_order = order

        def get_export_headers(self):
            return [props[w] if w in props else w for w in headers]

    return model_resource()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pop_pagination(data):
    params = [
        "first",
        "last",
        "after",
        "before",
    ]
    for p in params:
        if p in data:
            data.pop(p)


from io import BytesIO

from django.http import HttpResponse
from libs.graphql.schema.filters import ProjectFilters


class CreateSimpleReport(graphene.Mutation):
    class Input:
        model = graphene.String(required=True)
        app = graphene.String(required=True)
        filename = graphene.String(required=False)
        fields = graphene.List(ExportFieldType)
        variables = graphene.List(ExportVariableType)
        rename_properties = graphene.List(ExportVariableType, required=False)
        pagination = graphene.Argument(ExportPaginationType, required=False)
        ext = graphene.String(required=False)
        ordering = graphene.String(required=False)

    url = graphene.String()

    def mutate(
        self,
        info,
        app,
        model,
        fields,
        pagination=None,
        filename="exported",
        rename_properties=[],
        variables=[],
        ext="csv",
        ordering="-id",
    ):
        model = apps.get_model(app, model)
        build_props = dict(
            zip(
                list(map(lambda x: x.name, rename_properties)),
                list(map(lambda x: x.value, rename_properties)),
            )
        )
        resource = create_resource(
            model,
            list(map(lambda x: x.name, fields)),
            list(map(lambda x: x.name, fields)),
            build_props,
            list(map(lambda x: x.title, fields)),
        )
        if not os.path.isdir(os.path.join(settings.MEDIA_ROOT, f"export/")):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, f"export/"))

        file = open(
            os.path.join(settings.MEDIA_ROOT, f"export/{filename}"),
            "w" if ext == "csv" else "wb",
        )
        # page = 0
        # rowPerPage = model.objects.count()

        # # extract pagination
        # if pagination:
        #     page, rowPerPage, ordering = attrgetter(
        #         "page", "rowPerPage", "ordering")(pagination)
        # build variables to match django model filtering
        build_variables = dict(
            zip(
                list(map(lambda x: x.name, variables)),
                list(map(lambda x: x.value, variables)),
            )
        )
        pop_pagination(build_variables)
        queryset = model.objects.all()
        filterclass = ProjectFilters[f"{model.__name__}Filters"]
        # importlib.import_module(
        #     f"{app}.graphqls.filters.{model.__name__}")
        queryset = filterclass(
            data=build_variables, queryset=queryset, request=info.context
        ).qs.order_by(ordering)
        # [page * rowPerPage: page * rowPerPage + rowPerPage]
        # queryset = queryset.filter(
        #     **build_variables).order_by(ordering)[page * rowPerPage: page * rowPerPage + rowPerPage]
        if ext == "csv":
            pass
            file.write(resource.export(queryset=queryset).csv)

        elif ext == "xlsx":
            dataset = resource.export(queryset=queryset)
            workbook = resource.after_export(queryset, dataset, title="dqdsqd")
            workbook.save(file)
            # output.seek(0)
            # resource.export(queryset=queryset).xls
            # # file.write()
            # response = HttpResponse(
            #     output,
            #     content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            # )
            # response["Content-Disposition"] = (
            #     'attachment; filename="your_model_export.xlsx"'
            # )
            # return response

            # file.write(resource.export(queryset=queryset).xls)
        file.close()
        return CreateSimpleReport(url=f"export/csv/{os.path.basename(file.name)}")


class Reporting(graphene.ObjectType):
    reporting = CreateSimpleReport.Field()
