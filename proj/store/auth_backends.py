from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(BaseBackend):
    """
    Allows authentication by either email address OR username.
    Works seamlessly with Django Admin (/admin/) and custom login forms.
    """
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        identifier = email or username or kwargs.get('username') or kwargs.get('email')
        if not identifier or not password:
            return None
        
        try:
            # Case-insensitive match on either username or email
            user = User.objects.filter(
                Q(email__iexact=identifier) | Q(username__iexact=identifier)
            ).first()
            if user and user.check_password(password):
                return user
        except Exception:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
