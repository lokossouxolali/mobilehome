from django.apps import AppConfig
import importlib

class FactAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fact_app'

    def ready(self):
        importlib.import_module('fact_app.signals')
