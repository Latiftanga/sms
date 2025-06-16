from django.core.management.base import BaseCommand
from account.models import User


class Command(BaseCommand):
    help = 'Create a superuser account'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True,
                            help='Username for superuser')
        parser.add_argument('--email', help='Email for superuser')
        parser.add_argument('--password', help='Password for superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options.get('email', '')
        password = options.get('password')

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(
                    f'User with username "{username}" already exists.')
            )
            return

        if not password:
            password = self.getpass('Password: ')

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS(f'Superuser "{username}" created successfully.')
        )

    def getpass(self, prompt):
        import getpass
        return getpass.getpass(prompt)
