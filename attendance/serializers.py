# serializers.py
from rest_framework import serializers
from .models import (
    Employee, GatePass, ShiftAssignment, 
    ODSlip, SundayReplacement, Holiday, ManualPunch
)

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class GatePassSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    
    class Meta:
        model = GatePass
        fields = '__all__'
        extra_kwargs = {
            'employee': {'write_only': True}
        }

class ShiftAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    
    class Meta:
        model = ShiftAssignment
        fields = '__all__'
        extra_kwargs = {
            'employee': {'write_only': True}
        }

class ODSlipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    
    class Meta:
        model = ODSlip
        fields = '__all__'
        extra_kwargs = {
            'employee': {'write_only': True}
        }

class SundayReplacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SundayReplacement
        fields = '__all__'

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'

class ManualPunchSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    
    class Meta:
        model = ManualPunch
        fields = '__all__'
        extra_kwargs = {
            'employee': {'write_only': True}
        }

from rest_framework import serializers
from .models import ProcessedAttendance

class ProcessedAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    
    class Meta:
        model = ProcessedAttendance
        fields = ['id', 'employee', 'employee_name', 'month', 'year', 'processed_date', 'attendance_data']
        read_only_fields = ['processed_date']