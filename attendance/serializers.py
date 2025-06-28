# serializers.py
from rest_framework import serializers
from .models import (
    Employee, GatePass, ShiftAssignment, 
    ODSlip, SundayReplacement, Holiday, ManualPunch,EmployeeDocument,SalaryAdvance
)

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'
        read_only_fields = ('employee', 'uploaded_at')
    
    def validate(self, data):
        # Ensure no one tries to override the employee
        if 'employee' in data:
            raise serializers.ValidationError("Employee cannot be set directly")
        return data
    
    def create(self, validated_data):
        # Get employee from context (set by the view)
        employee = self.context['employee']
        validated_data['employee'] = employee
        return super().create(validated_data)

class EmployeeSerializer(serializers.ModelSerializer):
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {
            'profile_picture': {'write_only': True}
        }
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return self.context['request'].build_absolute_uri(obj.profile_picture.url)
        return None
    
class EmployeeSerializerdocu(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'employee_name', 'employee_department', 'position']

class EmployeeDocumentSerializerdoc(serializers.ModelSerializer):
    employee = EmployeeSerializerdocu(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_active=True),
        source='employee',
        write_only=True,
        required=True
    )
    filename = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 
            'employee', 
            'employee_id', 
            'document_type', 
            'document_file', 
            'uploaded_at', 
            'description',
            'filename'
        ]
        read_only_fields = ['uploaded_at']

    def get_filename(self, obj):
        return obj.filename

    

class EmployeeSerializeradvance(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'employee_name', 'employee_id']  # Add other relevant fields

class SalaryAdvanceSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializeradvance(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        source='employee',
        write_only=True
    )
    
    class Meta:
        model = SalaryAdvance
        fields = '__all__'

class BulkSalaryAdvanceSerializer(serializers.ListSerializer):
    child = SalaryAdvanceSerializer()

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