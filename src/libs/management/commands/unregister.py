from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('models', type=str, nargs='+',
                            help='models')
        parser.add_argument('-app', '--app',
                            help='App')

    def handle(self, *args, **kwargs):
        arg = kwargs['models']
        try:
            # app, model = arg.split('.')
            app = kwargs['app']
            models = kwargs['models']
            print(app, models)
        except:
            self.stdout.write('argument must be app.Model')

        ####
        # createTypes(app_label, model)
        # createFilters(app_label, model)
        # createSerializers(app_label, model)
        # createMutaions(app_label, model)
        # createSchema(app_label, model)
        for model in models:
            model_name = model
            line = f"from {app}.graphqls.schemas.{model_name} import {model_name}Queries, {model_name}Mutations"

            if os.path.exists(f"{app}/graphqls/defaults.py"):
                file = open(f"{app}/graphqls/defaults.py", "r")
                content = file.read()
                file.close()
                if(line in content):
                    print(
                        f"\x1b[5;30;42m...... {model} is registered successfully\x1b[0m ")
                    f = open(f"{app}/graphqls/defaults.py", "+w")
                    content = content.replace(line, "")
                    content = content.replace(f"{model}Queries,", "")
                    content = content.replace(f"{model}Mutations,", "")
                    f.write(content)
                    f.close()
                else:
                    print(
                        f"\x1b[32;3;30m...... {model} is not registered\x1b[0m ")
                # if content.count(f"{model_name}Querie") == 0:
                #     print("dmlkqsmdlkqsmdlk")

                #     content = content[0:content.index(
                #         f"{app.upper()}Queries(")] + content[:content.index(
                #             f"{app.upper()}Queries(")]
                #     f.write(content)

                # if content.count(f"{model_name}Mutations"):
                #     content.index(f"{app.upper()}Mutations(")
