from django.db import models
from simple_history.models import HistoricalRecords
from datetime import datetime
import pytz

class Employee(models.Model):
    EMPLOYEE_TYPES = (
        ('FT', 'Full Time'),
        ('PT', 'Part Time'),
        ('CT', 'Contract'),
    )

    DEPARTMENTS = (
        ('HR', 'Human Resources'),
        ('CNC', 'CNC'),
        ('FORGING', 'FORGING'),
        ('HAMMER', 'HAMMER'),
        ('STORE', 'STORE'),
        ('TOOL ROOM', 'TOOL ROOM'),
        ('TURNING', 'TURNING'),
        ('ACCOUNTS', 'ACCOUNTS'),
        ('RM', 'RM'),
        ('ENGINEERING', 'ENGINEERING'),
        ('LAB', 'LAB'),
        ('FI', 'FI'),
        ('MAINTENANCE', 'MAINTENANCE'),
        ('Quality', 'Quality'),
        ('SECURITY', 'SECURITY'),
        ('DISPATCH', 'DISPATCH'),
        ('ELECTRICAL', 'ELECTRICAL'),

        ('FI-MARKING', 'FI-MARKING'),
        ('FI-FINAL INSPECTION', 'FI-FINAL INSPECTION'),
        ('FI-D MAGNET', 'FI-D MAGNET'),
        ('CANTEEN', 'CANTEEN'),
        ('HAMMER', 'HAMMER'),
        ('HEAT TREATMENT', 'HEAT TREATMENT'),
        ('FI-PACKING & LOADING', 'FI-PACKING & LOADING'),
        ('FI-VISUAL', 'FI-VISUAL'),
        ('MATERIAL MOVEMENT', 'MATERIAL MOVEMENT'),

        ('MPI', 'MPI'),('RING ROLLING', 'RING ROLLING'),('SHOT BLAST', 'SHOT BLAST'),('TURNING', 'TURNING'),
        ('Other', 'Other'),

    )

    SHIFT_TYPES = (
        ('DAY', 'Day Shift'),
        ('NIGHT', 'Night Shift'),
        ('ROT', 'Rotational Shift'),
    )

    POSITION_CHOICES = (
        ('INCHARGE', 'Incharge'),
        ('MAINTENANCE', 'Maintenance'),
        ('QA', 'QA'),
        ('NPD', 'NPD'),
        ('FORMAN', 'Forman'),
        ('EXECUTIVE', 'Executive'),
        ('Supervisor', 'Supervisor'),
        ('QUALITY ENGINEER', 'Quality Engineer'),
        ('OPERATOR', 'Operator'),
        ('PROGRAMMER', 'Programmer'),
        ('HEAD', 'Head'),
        ('Designer', 'Designer'),
        ('Loader', 'Loader'),
        ('Chaker', 'Chaker'),
        ('Packer', 'Packer'),
        ('Visual', 'Visual'),
        ('Helper', 'Helper'),
        ('Developer', 'Developer'),
        ('Quality Head', 'Quality Head'),
        ('SAFETY & SECURITY INCHARGE', 'SAFETY & SECURITY INCHARGE'),
    )


    employee_id = models.CharField(max_length=10, unique=True)
    employee_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    employee_type = models.CharField(max_length=2, choices=EMPLOYEE_TYPES)
    employee_department = models.CharField(max_length=32, choices=DEPARTMENTS)
    position = models.CharField(max_length=30, choices=POSITION_CHOICES)
    is_getting_sunday = models.BooleanField(default=True)
    is_getting_ot = models.BooleanField(default=False)
    no_of_cl = models.PositiveIntegerField(default=0)
    working_time_in = models.TimeField()
    working_time_out = models.TimeField()
    working_hours = models.DecimalField(max_digits=5, decimal_places=2)
    shift_type = models.CharField(max_length=5, choices=SHIFT_TYPES)

    salary = models.DecimalField(max_digits=10, decimal_places=2)
    incentive = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Designates whether the employee is active or inactive")
    

    history = HistoricalRecords()  # <- to track all changes

    def __str__(self):
        return f"{self.employee_name} ({self.employee_id})"


class GatePass(models.Model):
    ACTION_CHOICES = (
        ('FD', 'Full Day'),
        ('HD', 'Half Day Cut'),
        ('FD_CUT', 'Full Day Cut'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='gate_passes')
    date = models.DateField()  # New date field
    out_time = models.TimeField()
    approved_by = models.CharField(max_length=100)
    action_taken = models.CharField(max_length=7, choices=ACTION_CHOICES)
    reason = models.CharField(max_length=255, blank=True, null=True)

    history = HistoricalRecords()  # track history here too

    def __str__(self):
        return f"Gate Pass - {self.employee.employee_name} ({self.out_time})"
    
class ShiftAssignment(models.Model):
    SHIFT_CHOICES = (
        ('DAY', 'Day Shift'),
        ('NIGHT', 'Night Shift'),
        ('ROT', 'Rotational Shift'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shift_assignments')
    shift_type = models.CharField(max_length=5, choices=SHIFT_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    working_time_in = models.TimeField()
    working_time_out = models.TimeField()

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.employee.employee_name} - {self.shift_type} ({self.start_date} to {self.end_date})"


class ODSlip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='od_slips')
    od_date = models.DateField()
    extra_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # example: 2.5 hours
    extra_days = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)    # example: 1.0 day
    approved_by = models.CharField(max_length=100)
    reason = models.CharField(max_length=255, blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"OD Slip - {self.employee.employee_name} on {self.od_date}"

class SundayReplacement(models.Model):
    department = models.CharField(
        max_length=32,
        choices=Employee.DEPARTMENTS,
        blank=True,
        null=True,
        help_text="Leave empty if applicable for ALL departments. When set, ALL employees in this department MUST work on the replacement date."
    )
    sunday_date = models.DateField(help_text="Original Sunday date being replaced - attendance is mandatory on this date")
    replacement_date = models.DateField(help_text="New working day instead of Sunday")

    history = HistoricalRecords()

    def __str__(self):
        dept = self.department if self.department else "All Departments"
        return f"Sunday {self.sunday_date} replaced by {self.replacement_date} for {dept}"


class Holiday(models.Model):
    department = models.CharField(
        max_length=32,
        choices=Employee.DEPARTMENTS,
        blank=True,
        null=True,
        help_text="Leave blank if holiday is for ALL departments"
    )
    holiday_date = models.DateField(help_text="Date of the holiday")
    holiday_name = models.CharField(max_length=100, help_text="Reason for holiday (e.g., Diwali, Independence Day)")

    history = HistoricalRecords()

    def __str__(self):
        dept = self.department if self.department else "All Departments"
        return f"Holiday: {self.holiday_name} on {self.holiday_date} for {dept}"


from datetime import datetime
from django.utils import timezone

class ManualPunch(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='manual_punches')
    punch_in_time = models.DateTimeField(
        null=True, blank=True, help_text="Manual Clock-in time (leave blank if missing)"
    )
    punch_out_time = models.DateTimeField(
        null=True, blank=True, help_text="Manual Clock-out time (leave blank if missing)"
    )
    reason = models.CharField(max_length=255, help_text="Reason for adding manual punch")
    approved_by = models.CharField(max_length=100, help_text="Name of the approver (e.g., supervisor, HR)")

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # Convert naive datetimes to aware datetimes in IST before saving
        ist = pytz.timezone('Asia/Kolkata')
        
        if self.punch_in_time and not timezone.is_aware(self.punch_in_time):
            self.punch_in_time = ist.localize(self.punch_in_time)
            
        if self.punch_out_time and not timezone.is_aware(self.punch_out_time):
            self.punch_out_time = ist.localize(self.punch_out_time)
            
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Manual Punch for {self.employee.employee_name} on {self.punch_in_time.date() if self.punch_in_time else self.punch_out_time.date()}"


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
    

class ProcessedAttendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='processed_attendances')
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.PositiveSmallIntegerField()
    processed_date = models.DateTimeField(auto_now_add=True)
    
    # Store the complete processed data as JSON
    attendance_data = models.JSONField()
    
    class Meta:
        unique_together = ('employee', 'month', 'year')
        verbose_name = 'Processed Attendance'
        verbose_name_plural = 'Processed Attendances'
        
    def __str__(self):
        return f"{self.employee.employee_name} - {self.month}/{self.year}"
    
from django.core.exceptions import ValidationError

class ProcessedSalary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    data = models.JSONField()  # Stores all the salary calculation details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        verbose_name_plural = 'Processed Salaries'
        indexes = [
            models.Index(fields=['month', 'year']),
            models.Index(fields=['employee']),
        ]

    def clean(self):
        if self.month < 1 or self.month > 12:
            raise ValidationError("Month must be between 1 and 12")
        
    def __str__(self):
        return f"{self.employee.employee_name} - {self.month}/{self.year}"