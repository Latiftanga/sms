# Mixins for view permissions
class AdminRequiredMixin:
    """Mixin for views that require admin access"""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and
                (request.user.is_admin or request.user.is_superuser)):
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class TeacherRequiredMixin:
    """Mixin for views that require teacher access"""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and
                (request.user.is_teacher or request.user.is_admin or
                 request.user.is_superuser)):
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)
