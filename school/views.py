from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone

from .models import (
    School, AcademicYear, Term, Programme, House,
    Subject, Class, Student, Teacher
)
from .forms import (
    SchoolConfigurationForm, AcademicYearForm,
    ProgrammeForm, HouseForm, SubjectForm, ClassForm, QuickSetupForm
)
from account.models import User


def is_admin_user(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_admin or user.is_superuser)


@login_required
@user_passes_test(is_admin_user)
def school_configuration_view(request):
    """School configuration view"""
    school = School.get_current_school()

    if request.method == 'POST':
        form = SchoolConfigurationForm(
            request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'School configuration updated successfully.')
            return redirect('admin:configuration')
    else:
        form = SchoolConfigurationForm(instance=school)

    context = {
        'form': form,
        'school': school,
        'title': 'School Configuration'
    }
    return render(request, 'school/configuration.html', context)


@login_required
@user_passes_test(is_admin_user)
def quick_setup_view(request):
    """Quick setup view for new installations"""
    if request.method == 'POST':
        form = QuickSetupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update school information
                    school = School.get_current_school()
                    school.name = form.cleaned_data['school_name']
                    school.code = form.cleaned_data['school_code']
                    school.save()

                    # Create academic year
                    year = form.cleaned_data['academic_year']
                    academic_year, created = AcademicYear.objects.get_or_create(
                        year=year,
                        defaults={
                            'start_date': timezone.datetime(year, 9, 1).date(),
                            'end_date': timezone.datetime(year + 1, 8, 31).date(),
                            'is_current': True
                        }
                    )

                    # Create programmes
                    programme_data = {
                        'general_arts': 'General Arts',
                        'business': 'Business',
                        'general_science': 'General Science',
                        'visual_arts': 'Visual Arts',
                        'home_economics': 'Home Economics',
                        'technical': 'Technical',
                    }

                    for prog_code in form.cleaned_data['create_programmes']:
                        Programme.objects.get_or_create(
                            name=programme_data[prog_code]
                        )

                    # Create houses
                    house_data = {
                        'red': ('Red House', '#DC2626'),
                        'blue': ('Blue House', '#2563EB'),
                        'green': ('Green House', '#16A34A'),
                        'yellow': ('Yellow House', '#EAB308'),
                    }

                    for house_code in form.cleaned_data['create_houses']:
                        name, color = house_data[house_code]
                        House.objects.get_or_create(
                            name=name,
                            defaults={'color': color}
                        )

                    # Create admin user
                    username = form.cleaned_data['admin_username']
                    password = form.cleaned_data['admin_password']
                    email = form.cleaned_data['admin_email']

                    if not User.objects.filter(username=username).exists():
                        User.objects.create_user(
                            username=username,
                            password=password,
                            email=email,
                            is_admin=True,
                            is_staff=True
                        )

                    messages.success(
                        request, 'School setup completed successfully!')
                    return redirect('school:configuration')

            except Exception as e:
                messages.error(request, f'Setup failed: {str(e)}')
    else:
        form = QuickSetupForm()

    context = {
        'form': form,
        'title': 'Quick Setup'
    }
    return render(request, 'school/quick_setup.html', context)


# Academic Year Views
class AcademicYearListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AcademicYear
    template_name = 'school/years/list.html'
    context_object_name = 'academic_years'

    def test_func(self):
        return is_admin_user(self.request.user)


class AcademicYearCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'school/years/form.html'
    success_url = reverse_lazy('admin:academic_years')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Academic year created successfully.')
        return super().form_valid(form)


class AcademicYearUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'schools/academic/year/form.html'
    success_url = reverse_lazy('admin:academic_years')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Academic year updated successfully.')
        return super().form_valid(form)


class AcademicYearDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AcademicYear
    template_name = 'school/years/confirm_delete.html'
    success_url = reverse_lazy('admin:academic_years')

    def test_func(self):
        return is_admin_user(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Academic year deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Programme Views
class ProgrammeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Programme
    template_name = 'school/programmes/list.html'
    context_object_name = 'programmes'

    def test_func(self):
        return is_admin_user(self.request.user)


class ProgrammeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Programme
    form_class = ProgrammeForm
    template_name = 'school/programmes/form.html'
    success_url = reverse_lazy('school:programmes')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Programme created successfully.')
        return super().form_valid(form)


class ProgrammeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Programme
    form_class = ProgrammeForm
    template_name = 'school/programmes/form.html'
    success_url = reverse_lazy('school:programmes')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Programme updated successfully.')
        return super().form_valid(form)


class ProgrammeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Programme
    template_name = 'school/programmes/confirm_delete.html'
    success_url = reverse_lazy('school:programmes')

    def test_func(self):
        return is_admin_user(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Programme deleted successfully.')
        return super().delete(request, *args, **kwargs)


# House Views
class HouseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = House
    template_name = 'school/houses/list.html'
    context_object_name = 'houses'

    def test_func(self):
        return is_admin_user(self.request.user)


class HouseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = House
    form_class = HouseForm
    template_name = 'school/houses/form.html'
    success_url = reverse_lazy('school:houses')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'House created successfully.')
        return super().form_valid(form)


class HouseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = House
    form_class = HouseForm
    template_name = 'school/houses/form.html'
    success_url = reverse_lazy('school:houses')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'House updated successfully.')
        return super().form_valid(form)


class HouseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = House
    template_name = 'school/houses/detail.html'
    context_object_name = 'house'

    def test_func(self):
        return is_admin_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.get_object()
        context['students'] = house.students.filter(
            is_active=True).order_by('student_id')
        context['student_count'] = context['students'].count()

        # Group students by class level
        context['students_by_level'] = {}
        for student in context['students']:
            if student.current_class:
                level = student.current_class.get_level_display()
                if level not in context['students_by_level']:
                    context['students_by_level'][level] = []
                context['students_by_level'][level].append(student)

        return context


class HouseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = House
    template_name = 'school/houses/confirm_delete.html'
    success_url = reverse_lazy('school:houses')

    def test_func(self):
        return is_admin_user(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'House deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Subject Views
class SubjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Subject
    template_name = 'school/subjects/list.html'
    context_object_name = 'subjects'

    def test_func(self):
        return is_admin_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add subject counts by type
        context['core_count'] = Subject.objects.filter(
            subject_type='core').count()
        context['elective_count'] = Subject.objects.filter(
            subject_type='elective').count()
        context['extracurricular_count'] = Subject.objects.filter(
            subject_type='extracurricular').count()
        return context


class SubjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'school/subjects/form.html'
    success_url = reverse_lazy('school:subjects')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Subject created successfully.')
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'school/subjects/form.html'
    success_url = reverse_lazy('school:subjects')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Subject updated successfully.')
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subject
    template_name = 'school/subjects/confirm_delete.html'
    success_url = reverse_lazy('school:subjects')

    def test_func(self):
        return is_admin_user(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subject deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Class Views
class ClassListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Class
    template_name = 'school/classes/list.html'
    context_object_name = 'classes'

    def test_func(self):
        return is_admin_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group classes by level
        classes_by_level = {}
        for cls in context['classes']:
            level = cls.get_level_display()
            if level not in classes_by_level:
                classes_by_level[level] = []
            classes_by_level[level].append(cls)
        context['classes_by_level'] = classes_by_level
        return context


class ClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = 'school/classes/form.html'
    success_url = reverse_lazy('school:classes')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Class created successfully.')
        return super().form_valid(form)


class ClassUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = 'school/classes/form.html'
    success_url = reverse_lazy('school:classes')

    def test_func(self):
        return is_admin_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Class updated successfully.')
        return super().form_valid(form)


class ClassDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Class
    template_name = 'school/classes/detail.html'
    context_object_name = 'class_obj'

    def test_func(self):
        return is_admin_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = self.get_object()
        context['students'] = class_obj.students.filter(
            is_active=True).order_by('student_id')
        context['student_count'] = context['students'].count()
        context['capacity_percentage'] = (
            context['student_count'] / class_obj.capacity * 100) if class_obj.capacity > 0 else 0
        return context


class ClassDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Class
    template_name = 'school/classes/confirm_delete.html'
    success_url = reverse_lazy('school:classes')

    def test_func(self):
        return is_admin_user(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Class deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_admin_user)
def setup_school_view(request):
    """Setup dashboard showing current status"""
    school = School.get_current_school()

    # Get counts
    academic_years_count = AcademicYear.objects.count()
    programmes_count = Programme.objects.count()
    houses_count = House.objects.count()
    subjects_count = Subject.objects.count()
    classes_count = Class.objects.count()
    students_count = Student.objects.filter(is_active=True).count()
    teachers_count = Teacher.objects.filter(is_active=True).count()

    # Check current academic year and term
    current_academic_year = AcademicYear.objects.filter(
        is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    context = {
        'school': school,
        'academic_years_count': academic_years_count,
        'programmes_count': programmes_count,
        'houses_count': houses_count,
        'subjects_count': subjects_count,
        'classes_count': classes_count,
        'students_count': students_count,
        'teachers_count': teachers_count,
        'current_academic_year': current_academic_year,
        'current_term': current_term,
        'title': 'Setup Dashboard'
    }
    return render(request, 'school/setup_school.html', context)
