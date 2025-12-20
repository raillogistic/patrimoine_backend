from django.apps import apps
from django.contrib import admin

app_models = apps.get_app_config("immo").get_models()

# print([m for m in app_models])
for model in [m for m in app_models]:
    admin.site.register(model)
