from django.shortcuts import render

# Create your views here.
# File: student/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import csv
import io
from datetime import datetime

from school.models import Student, Class, House, Programme, AcademicYear, Term
from account.models import User
from .forms import StudentForm, BulkUploadForm, PromotionForm, StudentSearchForm
from .utils import process_bulk_student_upload, promote_students, demote_students


class IsAdminOrTeacherMixin(UserPassesTestMixin):
    """Mixin to ensure only admin or teacher users can access views"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_admin or self.request.user.is_teacher
            or self.request.user.is_superuser
        )


class StudentListView(LoginRequiredMixin, IsAdminOrTeacherMixin, ListView):
    """List all students with filtering and search capabilities"""
    model = Student
    template_name = 'student/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        queryset = Student.objects.select_related(
            'current_class', 'house', 'current_class__programme'
        ).filter(is_active=True)

        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(student_id__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        # Filter by class
        class_filter = self.request.GET.get('class', '')
        if class_filter:
            queryset = queryset.filter(current_class_id=class_filter)

        # Filter by house
        house_filter = self.request.GET.get('house', '')
        if house_filter:
            queryset = queryset.filter(house_id=house_filter)

        # Filter by programme
        programme_filter = self.request.GET.get('programme', '')
        if programme_filter:
            queryset = queryset.filter(
                current_class__programme_id=programme_filter)

        # Filter by year admitted
        year_filter = self.request.GET.get('year_admitted', '')
        if year_filter:
            queryset = queryset.filter(year_admitted=year_filter)

        return queryset.order_by('current_class__level', 'last_name', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = StudentSearchForm(self.request.GET)
        context['classes'] = Class.objects.all().order_by('level', 'name')
        context['houses'] = House.objects.all().order_by('name')
        context['programmes'] = Programme.objects.all().order_by('name')
        context['years'] = Student.objects.values_list(
            'year_admitted', flat=True
        ).distinct().order_by('-year_admitted')

        # Statistics
        context['total_students'] = Student.objects.filter(
            is_active=True).count()
        context['students_by_class'] = Student.objects.filter(is_active=True).values(
            'current_class__level'
        ).annotate(count=Count('id')).order_by('current_class__level')

        return context


class StudentDetailView(LoginRequiredMixin, IsAdminOrTeacherMixin, DetailView):
    """Detailed view of a single student"""
    model = Student
    template_name = 'student/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        return Student.objects.select_related(
            'current_class', 'house', 'current_class__programme', 'user'
        )


class StudentCreateView(LoginRequiredMixin, IsAdminOrTeacherMixin, CreateView):
    """Create a new student"""
    model = Student
    form_class = StudentForm
    template_name = 'student/student_form.html'
    success_url = reverse_lazy('student:student_list')

    def form_valid(self, form):
        """Create user account along with student profile"""
        try:
            with transaction.atomic():
                # Save student first to generate student_id
                student = form.save()

                # Create user account
                from account.models import create_student_with_user
                result = create_student_with_user(
                    first_name=student.first_name,
                    last_name=student.last_name,
                    year_admitted=student.year_admitted,
                    email=student.email,
                    gender=student.gender,
                    date_of_birth=student.date_of_birth,
                    phone=student.phone,
                    address=student.address,
                    ghana_card_number=student.ghana_card_number,
                    current_class=student.current_class,
                    house=student.house,
                    guardian_name=student.guardian_name,
                    guardian_phone=student.guardian_phone,
                    guardian_email=student.guardian_email,
                    relationship_to_guardian=student.relationship_to_guardian
                )

                messages.success(
                    self.request,
                    f'Student {student.get_full_name()} created successfully! '
                    f'Username: {result["username"]}, Password: {result["password"]}'
                )
                return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Error creating student: {str(e)}')
            return self.form_invalid(form)


class StudentUpdateView(LoginRequiredMixin, IsAdminOrTeacherMixin, UpdateView):
    """Update student information"""
    model = Student
    form_class = StudentForm
    template_name = 'student/student_form.html'

    def get_success_url(self):
        return reverse('student:student_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request, 'Student information updated successfully!')
        return super().form_valid(form)


class StudentDeleteView(LoginRequiredMixin, IsAdminOrTeacherMixin, DeleteView):
    """Soft delete a student (set is_active=False)"""
    model = Student
    template_name = 'student/student_confirm_delete.html'
    success_url = reverse_lazy('student:student_list')

    def delete(self, request, *args, **kwargs):
        """Soft delete - set is_active to False instead of actual deletion"""
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()

        # Also deactivate associated user account
        if self.object.user:
            self.object.user.is_active = False
            self.object.user.save()

        messages.success(
            request, f'Student {self.object.get_full_name()} has been deactivated.')
        return redirect(self.success_url)


class BulkUploadView(LoginRequiredMixin, IsAdminOrTeacherMixin, FormView):
    """Bulk upload students from CSV file"""
    form_class = BulkUploadForm
    template_name = 'student/bulk_upload.html'
    success_url = reverse_lazy('student:student_list')

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        default_class = form.cleaned_data.get('default_class')
        default_house = form.cleaned_data.get('default_house')

        try:
            # Process the CSV file
            result = process_bulk_student_upload(
                csv_file,
                default_class=default_class,
                default_house=default_house
            )

            messages.success(
                self.request,
                f'Successfully uploaded {result["success_count"]} students. '
                f'{result["error_count"]} errors encountered.'
            )

            if result["errors"]:
                # Store errors in session for display
                self.request.session['upload_errors'] = result["errors"]

        except Exception as e:
            messages.error(self.request, f'Error processing upload: {str(e)}')
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload_errors'] = self.request.session.pop(
            'upload_errors', [])
        return context


@login_required
def download_template(request):
    """Download CSV template for bulk upload"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_upload_template.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
        'email', 'phone', 'address', 'ghana_card_number', 'year_admitted',
        'class_name', 'house_name', 'guardian_name', 'guardian_phone',
        'guardian_email', 'relationship_to_guardian'
    ])

    # Add sample data
    writer.writerow([
        'John', 'Doe', 'Smith', 'M', '2008-05-15',
        'john.smith@email.com', '0244123456', '123 Main St, Accra',
        'GHA-123456789-0', '2024', '1A', 'Blue House',
        'Jane Smith', '0244987654', 'jane.smith@email.com', 'Mother'
    ])

    return response


# Also replace the PromotionView with this corrected version
class PromotionView(LoginRequiredMixin, IsAdminOrTeacherMixin, FormView):
    """Promote students to the next class/level"""
    form_class = PromotionForm
    template_name = 'student/promotion.html'
    success_url = reverse_lazy('student:student_list')

    def form_valid(self, form):
        from_class = form.cleaned_data['from_class']
        to_class = form.cleaned_data['to_class']
        selected_students = form.cleaned_data['students']

        try:
            result = promote_students(selected_students, to_class)

            messages.success(
                self.request,
                f'Successfully promoted {result["success_count"]} students from '
                f'{from_class} to {to_class}.'
            )

            if result["errors"]:
                for error in result["errors"]:
                    messages.warning(self.request, error)

        except Exception as e:
            messages.error(self.request, f'Error during promotion: {str(e)}')
            return self.form_invalid(form)

        return super().form_valid(form)


@login_required
def ajax_get_students_by_class(request):
    """AJAX endpoint to get students by class for promotion/demotion"""
    class_id = request.GET.get('class_id')
    if class_id:
        students = Student.objects.filter(
            current_class_id=class_id, is_active=True
        ).values('id', 'first_name', 'last_name', 'student_id')

        return JsonResponse({
            'students': list(students)
        })

    return JsonResponse({'students': []})


@login_required
def student_statistics(request):
    """Display student statistics dashboard"""
    context = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'students_by_level': Student.objects.filter(is_active=True).values(
            'current_class__level'
        ).annotate(count=Count('id')).order_by('current_class__level'),
        'students_by_gender': Student.objects.filter(is_active=True).values(
            'gender'
        ).annotate(count=Count('id')),
        'students_by_house': Student.objects.filter(is_active=True).values(
            'house__name'
        ).annotate(count=Count('id')).order_by('house__name'),
        'recent_admissions': Student.objects.filter(is_active=True).order_by(
            '-created_at'
        )[:10]
    }

    return render(request, 'student/statistics.html', context)


class InactiveStudentsView(LoginRequiredMixin, IsAdminOrTeacherMixin, ListView):
    """List inactive/deactivated students"""
    model = Student
    template_name = 'student/inactive_students.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        return Student.objects.filter(is_active=False).order_by('-updated_at')


@login_required
def reactivate_student(request, pk):
    """Reactivate a deactivated student"""
    if not (request.user.is_admin or request.user.is_superuser):
        messages.error(
            request, 'You do not have permission to reactivate students.')
        return redirect('student:student_list')

    student = get_object_or_404(Student, pk=pk)
    student.is_active = True
    student.save()

    # Reactivate user account if exists
    if student.user:
        student.user.is_active = True
        student.user.save()

    messages.success(
        request, f'Student {student.get_full_name()} has been reactivated.')
    return redirect('student:student_detail', pk=pk)
