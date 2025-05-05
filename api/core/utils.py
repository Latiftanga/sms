# utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_credentials_email(email, username, password, student_name, student_id, school_name):
    """
    Send login credentials to the user's email

    Args:
        email (str): Recipient email address
        username (str): User's login username
        password (str): User's password
        student_name (str): Full name of the student
        student_id (str): Student ID
        school_name (str): Name of the school
    """
    subject = f"Your Login Credentials for {school_name}"

    # Create both HTML and plain text versions
    html_message = render_to_string('emails/credentials_email.html', {
        'student_name': student_name,
        'student_id': student_id,
        'username': username,
        'password': password,
        'school_name': school_name,
        'login_url': settings.LOGIN_URL,
    })

    plain_message = f"""
Hello {student_name},

Your account for {school_name} has been created successfully.

Student ID: {student_id}
Username: {username}
Password: {password}

Please log in at {settings.LOGIN_URL} and change your password immediately.

This is an automated message, please do not reply.
    """

    # Send the email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )
