# Generated by Django 5.2 on 2025-07-26 05:28

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0017_salaryadvance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notrunningday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, choices=[('HR', 'Human Resources'), ('CNC', 'CNC'), ('FORGING', 'FORGING'), ('HAMMER', 'HAMMER'), ('STORE', 'STORE'), ('TOOL ROOM', 'TOOL ROOM'), ('TURNING', 'TURNING'), ('ACCOUNTS', 'ACCOUNTS'), ('RM', 'RM'), ('ENGINEERING', 'ENGINEERING'), ('LAB', 'LAB'), ('FI', 'FI'), ('MAINTENANCE', 'MAINTENANCE'), ('Quality', 'Quality'), ('SECURITY', 'SECURITY'), ('DISPATCH', 'DISPATCH'), ('ELECTRICAL', 'ELECTRICAL'), ('FI-MARKING', 'FI-MARKING'), ('FI-FINAL INSPECTION', 'FI-FINAL INSPECTION'), ('FI-D MAGNET', 'FI-D MAGNET'), ('CANTEEN', 'CANTEEN'), ('HAMMER', 'HAMMER'), ('HEAT TREATMENT', 'HEAT TREATMENT'), ('FI-PACKING & LOADING', 'FI-PACKING & LOADING'), ('FI-VISUAL', 'FI-VISUAL'), ('MATERIAL MOVEMENT', 'MATERIAL MOVEMENT'), ('MPI', 'MPI'), ('RING ROLLING', 'RING ROLLING'), ('SHOT BLAST', 'SHOT BLAST'), ('TURNING', 'TURNING'), ('Other', 'Other')], help_text='Leave blank if notrunning is for ALL departments', max_length=32, null=True)),
                ('notrunning_date', models.DateField(help_text='Date of the holiday')),
                ('resion', models.CharField(help_text='Reason for not run (e.g., power cut)', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalNotrunningday',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('department', models.CharField(blank=True, choices=[('HR', 'Human Resources'), ('CNC', 'CNC'), ('FORGING', 'FORGING'), ('HAMMER', 'HAMMER'), ('STORE', 'STORE'), ('TOOL ROOM', 'TOOL ROOM'), ('TURNING', 'TURNING'), ('ACCOUNTS', 'ACCOUNTS'), ('RM', 'RM'), ('ENGINEERING', 'ENGINEERING'), ('LAB', 'LAB'), ('FI', 'FI'), ('MAINTENANCE', 'MAINTENANCE'), ('Quality', 'Quality'), ('SECURITY', 'SECURITY'), ('DISPATCH', 'DISPATCH'), ('ELECTRICAL', 'ELECTRICAL'), ('FI-MARKING', 'FI-MARKING'), ('FI-FINAL INSPECTION', 'FI-FINAL INSPECTION'), ('FI-D MAGNET', 'FI-D MAGNET'), ('CANTEEN', 'CANTEEN'), ('HAMMER', 'HAMMER'), ('HEAT TREATMENT', 'HEAT TREATMENT'), ('FI-PACKING & LOADING', 'FI-PACKING & LOADING'), ('FI-VISUAL', 'FI-VISUAL'), ('MATERIAL MOVEMENT', 'MATERIAL MOVEMENT'), ('MPI', 'MPI'), ('RING ROLLING', 'RING ROLLING'), ('SHOT BLAST', 'SHOT BLAST'), ('TURNING', 'TURNING'), ('Other', 'Other')], help_text='Leave blank if notrunning is for ALL departments', max_length=32, null=True)),
                ('notrunning_date', models.DateField(help_text='Date of the holiday')),
                ('resion', models.CharField(help_text='Reason for not run (e.g., power cut)', max_length=100)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical notrunningday',
                'verbose_name_plural': 'historical notrunningdays',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
