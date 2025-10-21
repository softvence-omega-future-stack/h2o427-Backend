from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with email instead of username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Try to get the user by email
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Try by username as fallback
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        
        # Check the password
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
