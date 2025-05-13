from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Employee
from import_export.admin import ExportMixin, ImportExportModelAdmin
from import_export import resources

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('employee_id', 'employee_name', 'employee_department', 'employee_type', 'shift_type')
    search_fields = ('employee_name', 'employee_id', 'father_name')
    list_filter = ('employee_department', 'employee_type', 'shift_type', 'is_getting_sunday', 'is_getting_ot')

from .models import GatePass

@admin.register(GatePass)
class GatePassAdmin(SimpleHistoryAdmin):
    list_display = ('employee', 'out_time', 'approved_by', 'action_taken')
    search_fields = ('employee__employee_name', 'approved_by')
    list_filter = ('action_taken',)

from .models import ShiftAssignment

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(SimpleHistoryAdmin):
    list_display = ('employee', 'shift_type', 'start_date', 'end_date')
    list_filter = ('shift_type',)
    search_fields = ('employee__employee_name', 'employee__employee_id')


from .models import ODSlip

@admin.register(ODSlip)
class ODSlipAdmin(SimpleHistoryAdmin):
    list_display = ('employee', 'od_date', 'extra_hours', 'extra_days', 'approved_by')
    search_fields = ('employee__employee_name', 'approved_by')
    list_filter = ('od_date',)

from .models import SundayReplacement

@admin.register(SundayReplacement)
class SundayReplacementAdmin(SimpleHistoryAdmin):
    list_display = ('sunday_date', 'replacement_date', 'department')
    list_filter = ('department',)
    date_hierarchy = 'sunday_date'
    search_fields = ('department',)

from .models import Holiday

@admin.register(Holiday)
class HolidayAdmin(SimpleHistoryAdmin):
    list_display = ('holiday_name', 'holiday_date', 'department')
    list_filter = ('department', 'holiday_date')
    search_fields = ('holiday_name',)
    date_hierarchy = 'holiday_date'

from .models import ManualPunch

@admin.register(ManualPunch)
class ManualPunchAdmin(SimpleHistoryAdmin):
    list_display = ('employee', 'punch_in_time', 'punch_out_time', 'approved_by', 'reason')
    search_fields = ('employee__employee_name', 'approved_by', 'reason')
    list_filter = ('approved_by',)
    date_hierarchy = 'punch_in_time'

from .models import ProcessedAttendance

@admin.register(ProcessedAttendance)
class ProcessedAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'processed_date')
    search_fields = ('employee__employee_name',)
    list_filter = ('month', 'year', 'employee')
    ordering = ('-processed_date',)