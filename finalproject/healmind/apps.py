from django.apps import AppConfig

class HealmindConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "healmind"

    def ready(self):
        pass
