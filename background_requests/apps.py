from django.apps import AppConfig


class RequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'background_requests'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import background_requests.signals
