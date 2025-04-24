from django.apps import AppConfig


class NdioAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ndio_app'

def ready(self):
    """
    Override the ready() method to import the signals module and
    register the signals with the appropriate models.
    """
    import ndio_app.signals