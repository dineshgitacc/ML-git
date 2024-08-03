from django.apps import AppConfig


class InferenceConfig(AppConfig):
    name = 'inference'
    def ready(self):
        from inference.controller import Scheduler
        Scheduler.start()