# File: student/exceptions.py
"""Custom exceptions for the student management module"""


class StudentManagementError(Exception):
    """Base exception for student management errors"""
    pass


class StudentValidationError(StudentManagementError):
    """Raised when student data validation fails"""
    pass


class BulkUploadError(StudentManagementError):
    """Raised when bulk upload operations fail"""
    pass


class StudentNotFoundError(StudentManagementError):
    """Raised when a student cannot be found"""
    pass


class PromotionError(StudentManagementError):
    """Raised when student promotion fails"""
    pass


class InvalidCSVError(BulkUploadError):
    """Raised when CSV file format is invalid"""
    pass


class DuplicateStudentError(StudentValidationError):
    """Raised when attempting to create duplicate student"""
    pass
