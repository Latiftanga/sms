# Generated by Django 5.2.3 on 2025-06-16 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programme',
            name='code',
            field=models.CharField(blank=True, max_length=5, unique=True),
        ),
    ]
