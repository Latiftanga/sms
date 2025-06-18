"""Constants used throughout the student management module"""

# Student status choices
STUDENT_STATUS_ACTIVE = 'active'
STUDENT_STATUS_INACTIVE = 'inactive'
STUDENT_STATUS_GRADUATED = 'graduated'
STUDENT_STATUS_TRANSFERRED = 'transferred'

STUDENT_STATUS_CHOICES = [
    (STUDENT_STATUS_ACTIVE, 'Active'),
    (STUDENT_STATUS_INACTIVE, 'Inactive'),
    (STUDENT_STATUS_GRADUATED, 'Graduated'),
    (STUDENT_STATUS_TRANSFERRED, 'Transferred'),
]

# CSV upload settings
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
MAX_STUDENTS_PER_UPLOAD = 1000
ALLOWED_FILE_EXTENSIONS = ['.csv']

# Pagination settings
STUDENTS_PER_PAGE = 20
MAX_STUDENTS_PER_PAGE = 100

# Student ID generation settings
STUDENT_ID_PREFIX = 'STU'
STUDENT_ID_LENGTH = 15

# Export settings
EXPORT_FORMATS = ['csv', 'xlsx', 'pdf']
MAX_EXPORT_RECORDS = 5000

# Search settings
MIN_SEARCH_LENGTH = 2
SEARCH_FIELDS = [
    'first_name', 'last_name', 'student_id', 'email',
    'phone', 'guardian_name', 'guardian_phone'
]

# Validation settings
MIN_AGE = 10
MAX_AGE = 25
MIN_YEAR_ADMITTED = 2000

# File paths
STUDENT_PHOTO_UPLOAD_PATH = 'students/photos/'
BULK_UPLOAD_TEMP_PATH = 'temp/uploads/'
