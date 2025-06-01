# core/forms.py
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from .models import School, User


def validate_image_file(file):
    """Utility function to validate image files"""
    if not file:
        return True

    # Check if this is a new uploaded file
    if hasattr(file, 'content_type') and hasattr(file, 'size'):
        # Check file size (limit to 5MB)
        max_size = getattr(settings, 'SCHOOL_SETTINGS', {}).get(
            'MAX_LOGO_SIZE', 5 * 1024 * 1024)
        if file.size > max_size:
            raise ValidationError(
                f"File size cannot exceed {max_size // (1024*1024)}MB.")

        # Check file type
        allowed_types = ['image/jpeg', 'image/png',
                         'image/gif', 'image/webp', 'image/jpg']
        if file.content_type not in allowed_types:
            raise ValidationError(
                "File must be an image (JPG, PNG, GIF, or WebP).")

        # Additional check for file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_name = file.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                "File must have a valid image extension (jpg, png, gif, webp).")

    return True


class LoginForm(forms.Form):
    """Login form for all user types"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True,
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Check if user exists
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    raise ValidationError('This account has been deactivated.')
            except User.DoesNotExist:
                raise ValidationError('Invalid username or password.')

        return cleaned_data


class SchoolSettingsForm(forms.ModelForm):
    """Comprehensive school settings form"""

    class Meta:
        model = School
        fields = [
            'name', 'school_type', 'ownership', 'emis_code', 'ges_number',
            'establishment_date', 'region', 'district', 'town',
            'digital_address', 'physical_address', 'headmaster_name',
            'email', 'phone_primary', 'phone_secondary', 'website',
            'logo', 'motto', 'has_boarding', 'is_active'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter school name'
            }),
            'school_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ownership': forms.Select(attrs={
                'class': 'form-select'
            }),
            'emis_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EMIS-000000'
            }),
            'ges_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GES registration number'
            }),
            'establishment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'region': forms.Select(attrs={
                'class': 'form-select'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter district'
            }),
            'town': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter town/city'
            }),
            'digital_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., UW-0123-4567'
            }),
            'physical_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter physical address'
            }),
            'headmaster_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter headmaster/principal name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'school@example.com'
            }),
            'phone_primary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+233-XX-XXX-XXXX'
            }),
            'phone_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+233-XX-XXX-XXXX (Optional)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.schoolwebsite.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'motto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter school motto'
            }),
            'has_boarding': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        labels = {
            'name': 'School Name',
            'school_type': 'School Type',
            'ownership': 'Ownership Type',
            'emis_code': 'EMIS Code',
            'ges_number': 'GES Registration Number',
            'establishment_date': 'Date of Establishment',
            'region': 'Region',
            'district': 'District',
            'town': 'Town/City',
            'digital_address': 'Ghana Post Digital Address',
            'physical_address': 'Physical Address',
            'headmaster_name': 'Headmaster/Principal Name',
            'email': 'Email Address',
            'phone_primary': 'Primary Phone',
            'phone_secondary': 'Secondary Phone',
            'website': 'Website URL',
            'logo': 'School Logo',
            'motto': 'School Motto',
            'has_boarding': 'Offers Boarding Facilities',
            'is_active': 'School is Active'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default values for T. I. Ahmadiyya SHS Wa
        if not self.instance.pk:  # New instance
            self.fields['name'].initial = "T. I. Ahmadiyya Senior High School, Wa"
            self.fields['school_type'].initial = "shs"
            self.fields['ownership'].initial = "mission"
            self.fields['region'].initial = "upper_west"
            self.fields['district'].initial = "Wa Municipal"
            self.fields['town'].initial = "Wa"
            self.fields['email'].initial = "info@ahmadiyyashs-wa.edu.gh"

        # Add help texts
        self.fields['emis_code'].help_text = "Educational Management Information System code assigned by GES"
        self.fields['digital_address'].help_text = "Ghana Post GPS address (e.g., UW-0123-4567)"
        self.fields['logo'].help_text = "Upload school logo (PNG, JPG, JPEG, GIF, or WebP format, max 5MB)"

        # Make certain fields required
        self.fields['name'].required = True
        self.fields['school_type'].required = True
        self.fields['ownership'].required = True
        self.fields['region'].required = True
        self.fields['district'].required = True
        self.fields['town'].required = True
        self.fields['headmaster_name'].required = True
        self.fields['email'].required = True
        self.fields['phone_primary'].required = True

    def clean_establishment_date(self):
        date = self.cleaned_data.get('establishment_date')
        if date and date > timezone.now().date():
            raise ValidationError(
                "Establishment date cannot be in the future.")
        return date

    def clean_emis_code(self):
        emis_code = self.cleaned_data.get('emis_code')
        if emis_code:
            # Check for duplicate EMIS codes
            existing = School.objects.filter(emis_code=emis_code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    "A school with this EMIS code already exists.")
        return emis_code

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')

        # If no logo is provided or it's False (checkbox unchecked), return it as is
        if not logo:
            return logo

        # Validate the image file
        try:
            validate_image_file(logo)
        except ValidationError as e:
            raise ValidationError(str(e))

        return logo


class ContactInfoForm(forms.ModelForm):
    """Separate form for quick contact info updates"""

    class Meta:
        model = School
        fields = ['email', 'phone_primary', 'phone_secondary', 'website']

        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'school@example.com'
            }),
            'phone_primary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+233-XX-XXX-XXXX'
            }),
            'phone_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+233-XX-XXX-XXXX (Optional)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.schoolwebsite.com'
            })
        }


class QuickSettingsForm(forms.Form):
    """Form for quick settings toggles"""

    has_boarding = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
