from django.apps import AppConfig


class RacetrackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'racetrack'

    def ready(self):
        import racetrack.signals  # noqa

