from django.core.management.base import BaseCommand
from django.utils import timezone
import os
from django.apps import apps
from models.queries.models import get_fields_and_properties


def createDefaults(app, model):
    model_name = model.__name__
    line = f"from {app}.graphqls.schemas.{model_name} import {model_name}Queries, {model_name}Mutations"
    if os.path.exists(f"{app}/graphqls/defaults.py"):
        file = open(f"{app}/graphqls/defaults.py", "r")
        content = file.read()
        if (line in content):
            print(
                f"\x1b[5;30;42m...... {model} is already registered \x1b[0m ")
            file.close()
            return

        else:
            f = open(f"{app}/graphqls/defaults.py", "r")
            content = f.read()
            content = line + "\n" + content
            add_query = f"{model_name}Queries,"
            add_mutation = f"{model_name}Mutations,"
            index_of_query = content.index("Queries(")
            index_of_mutation = content.index("Mutations(")

            content = content[0:index_of_query + len("Queries(")] + add_query + \
                content[index_of_query +
                        len("Queries("):]

            content = content[0:index_of_mutation + len(add_query) + len("Mutations(")] + add_mutation + \
                content[index_of_mutation +
                        len("Mutations(") + len(add_query):]

            # content = content[content.index(
            #     f"{app.upper()}Queries("):content.index(
            #     f"{app.upper()}Queries("):] + "xx"

            f = open(f"{app}/graphqls/defaults.py", "+w")

            f.write(content)

            # if content.count(f"{model_name}Querie") == 0:
            #     print("dmlkqsmdlkqsmdlk")

            #     content = content[0:content.index(
            #         f"{app.upper()}Queries(")] + content[:content.index(
            #             f"{app.upper()}Queries(")]
            #     f.write(content)

            # if content.count(f"{model_name}Mutations"):
            #     content.index(f"{app.upper()}Mutations(")
            f.close()

    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/defaults.py has been created\x1b[0m ")


class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('models', type=str, nargs='+',
                            help='models')
        parser.add_argument('-app', '--app',
                            help='App')
        parser.add_argument('-all', '--all', action='store_true',
                            help='Create an admin account')

    def handle(self, *args, **kwargs):
        arg = kwargs['models']
        try:
            # app, model = arg.split('.')
            app_label = kwargs['app']
            models = kwargs['models']
            ALL = kwargs['all']

        except:
            self.stdout.write('argument must be app.Model')
        # if ALL:
        #     app_models = apps.get_app_config(app_label).get_models()
        #     for model in app_models:

        ####
        for model_label in models:
            model = apps.get_model(app_label, model_label)
            # createTypes(app_label, model)
            # createFilters(app_label, model)
            # createSerializers(app_label, model)
            # createMutaions(app_label, model)
            # createSchema(app_label, model)
            createDefaults(app_label, model)


# ./manage.py register FirstProgramTask  --app maintenance
