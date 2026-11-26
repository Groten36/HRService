from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin


class OptionalLoginRequiredMixin(LoginRequiredMixin):
    """Wymaga logowania tylko, gdy ustawienie `login_setting` jest True."""

    login_setting = None

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, self.login_setting, True):
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
