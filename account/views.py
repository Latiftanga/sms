from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomLoginForm


class CustomLoginView(LoginView):
    """Custom login view with enhanced functionality"""
    form_class = CustomLoginForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect based on user type"""
        user = self.request.user
        if user.is_superuser or user.is_admin:
            return reverse_lazy('admin:admin_dashboard')
        elif user.is_teacher:
            return reverse_lazy('teacher:dashboard')
        elif user.is_student:
            return reverse_lazy('student:dashboard')
        return reverse_lazy('student:dashboard')

    def form_valid(self, form):
        """Add success message on login"""
        user = form.get_user()
        messages.success(
            self.request,
            f'Welcome back, {user.get_short_name() or user.username}!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Add error message on invalid login"""
        messages.error(
            self.request,
            'Invalid username or password. Please try again.'
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


@csrf_protect
@never_cache
def login_view(request):
    """Alternative function-based login view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                f'Welcome back, {user.get_short_name() or user.username}!'
            )

            # Redirect based on user type
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()

    context = {
        'form': form,
        'title': 'Login'
    }
    return render(request, 'auth/login.html', context)


@login_required
def logout_view(request):
    """Function-based logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    profile = user.get_profile()

    context = {
        'user': user,
        'profile': profile,
        'title': 'My Profile'
    }
    return render(request, 'auth/profile.html', context)


@login_required
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(
                request, 'Password must be at least 8 characters long.')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:login')

    context = {
        'title': 'Change Password'
    }
    return render(request, 'auth/change_password.html', context)
