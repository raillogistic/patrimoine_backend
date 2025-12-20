from django.core.management.base import BaseCommand
import os
import shutil


def move_file(from_app, to_app, model, folder):
    try:
        to_directory = f"{to_app}/graphqls/{folder}/"
        if not os.path.isdir(to_directory):
            os.mkdir(to_directory)
        shutil.move(f"{from_app}/graphqls/{folder}/{model}.py",
                    f"{to_app}/graphqls/{folder}/{model}.py")
    except:
        pass


class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('models', type=str, nargs='+',
                            help='Indicates the app.model you want to create graphql for')

        parser.add_argument('-from', '--from',
                            help='App move model from')

        parser.add_argument('-to', '--to',
                            help='App move model from')

    def handle(self, *args, **kwargs):
        models = kwargs['models']
        from_app = kwargs['from']
        to_app = kwargs['to']
        for m in models:
            move_file(from_app, to_app, m, "serializers")
            move_file(from_app, to_app, m, "types")
            move_file(from_app, to_app, m, "filters")
            move_file(from_app, to_app, m, "mutations")
            move_file(from_app, to_app, m, "schemas")
            pass
        if not os.path.exists(f"{to_app}/graphqls/defaults.py"):
            f = open(f"{to_app}/graphqls/defaults.py", "x")
