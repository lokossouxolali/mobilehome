from django.apps import AppConfig

class FactAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fact_app'

    def ready(self):
        import fact_app.signals  # Importe le module signals
