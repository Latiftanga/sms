from django.contrib import admin
from django import forms
from django.utils import timezone
import string
import secrets
from .models import School, User

# Custom form for creating admin users
class SchoolAdminForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('user_id', 'email', 'school')
    
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_admin = True
        user.is_staff = True
        if commit:
            user.save()
        return user

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_type', 'region', 'district', 'headmaster_name', 'is_active')
    list_filter = ('school_type', 'region', 'ownership', 'is_active')
    search_fields = ('name', 'district', 'town', 'headmaster_name', 'email')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'school_type', 'ownership', 'motto')
        }),
        ('Registration', {
            'fields': ('emis_code', 'ges_number', 'establishment_date')
        }),
        ('Location', {
            'fields': ('region', 'district', 'town', 'digital_address', 'physical_address')
        }),
        ('Contact Details', {
            'fields': ('headmaster_name', 'email', 'phone_primary', 'phone_secondary', 'website')
        }),
        ('Additional Information', {
            'fields': ('logo', 'has_boarding', 'is_active')
        }),
    )
    
    def create_admin_user(self, request, queryset):
        """Action to create an admin user for a selected school"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one school to create an admin for", level='error')
            return
        
        school = queryset[0]
        
        # Generate a unique user ID for the admin
        user_id = f"ADM{school.id}{timezone.now().strftime('%y%m%d%H%M')}"
        
        # Generate random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(10))
        
        # Create admin user
        admin_user = User.objects.create_user(
            user_id=user_id, 
            password=password
        )
        
        admin_user.is_admin = True
        admin_user.is_staff = True
        admin_user.school = school
        admin_user.save()
        
        # Message with credentials
        self.message_user(
            request, 
            f"Admin created for {school.name}. User ID: {user_id}, Password: {password}",
            level='success'
        )
    
    create_admin_user.short_description = "Create admin user for selected school"
    actions = ['create_admin_user']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'email', 'school', 'is_active', 'is_admin', 'is_teacher', 'is_student')
    list_filter = ('is_active', 'is_admin', 'is_teacher', 'is_student', 'school')
    search_fields = ('user_id', 'email')
    
    # Use different forms for add vs change
    add_form = SchoolAdminForm
    
    # Different fieldsets for add vs change
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_id', 'email', 'school', 'password1', 'password2'),
        }),
    )
    
    fieldsets = (
        (None, {'fields': ('user_id', 'email', 'password')}),
        ('School', {'fields': ('school',)}),
        ('Permissions', {'fields': ('is_active', 'is_admin', 'is_staff', 'is_teacher', 'is_student', 'is_guardian')}),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Use a different form for adding vs. changing pages.
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)