import requests
from datetime import datetime, timedelta, time
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from dateutil import rrule
from decimal import Decimal
from .models import Employee,Holiday,ShiftAssignment,SundayReplacement,GatePass,ODSlip,ManualPunch
from django.db.models.functions import Cast
from django.db.models import DateTimeField
from django.db import models
from .models import ProcessedAttendance
from datetime import date
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils import timezone
from datetime import timezone as datetime_timezone  # Python's built-in timezone
from django.utils import timezone as django_timezone  # Django's timezone utilities
import pytz  # Required for India timezone
from django.utils.timezone import localtime
ist = pytz.timezone('Asia/Kolkata')

class ProcessAttendanceAPI(APIView):
    def post(self, request):
        # Step 1: Get input parameters
        month = request.data.get('month')
        year = request.data.get('year')
        save_data = request.data.get('save', False)
        
        if not month or not year:
            return Response(
                {"error": "Month and year are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "Invalid month or year"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 2: Get all employees
        employees = Employee.objects.all()
        
        # Step 3: Get date range for processing
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year+1, 1, 1).date()
        else:
            end_date = datetime(year, month+1, 1).date()
        
        # Step 4: Fetch all relevant data in bulk for performance
        gate_passes = GatePass.objects.filter(
            employee__in=employees,
            date__gte=start_date,
            date__lt=end_date
        ).select_related('employee')
        
        shift_assignments = ShiftAssignment.objects.filter(
            employee__in=employees,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('employee')

        
        
        od_slips = ODSlip.objects.filter(
            employee__in=employees,
            od_date__gte=start_date,
            od_date__lt=end_date
        ).select_related('employee')
        
        sunday_replacements = SundayReplacement.objects.filter(
            Q(department__isnull=True) | Q(department__in=[emp.employee_department for emp in employees]),
            sunday_date__gte=start_date,
            sunday_date__lt=end_date
        )
        
        holidays = Holiday.objects.filter(
            Q(department__isnull=True) | Q(department__in=[emp.employee_department for emp in employees]),
            holiday_date__gte=start_date,
            holiday_date__lt=end_date
        )
        offset = timedelta(hours=5, minutes=30)

        # Replace the manual punch filtering with this:
        manual_punches = ManualPunch.objects.filter(
            employee__in=employees
        ).filter(
            Q(punch_in_time__date__gte=start_date, punch_in_time__date__lt=end_date + timedelta(days=1)) |
            Q(punch_out_time__date__gte=start_date, punch_out_time__date__lt=end_date + timedelta(days=1))
        ).select_related('employee')

        # Apply +5:30 manually
        for punch in manual_punches:
            punch.punch_in_time = punch.punch_in_time + offset if punch.punch_in_time else None
            punch.punch_out_time = punch.punch_out_time + offset if punch.punch_out_time else None
        
        # Step 5: Fetch punch logs from all machines
        punch_logs = self.fetch_punch_logs(start_date, end_date)
        
        # Step 6: Process attendance for each employee
        results = []
        for employee in employees:
            employee_data = self.process_employee_attendance(
                employee,
                start_date,
                end_date,
                gate_passes,
                shift_assignments,
                od_slips,
                sunday_replacements,
                holidays,
                manual_punches,
                punch_logs
            )
            results.append(employee_data)
        # NEW: Save the data if requested
        if save_data:
            self.save_processed_data(results, month, year)
        
        return Response(results, status=status.HTTP_200_OK)
    
    def save_processed_data(self, results, month, year):
        saved_records = []
        for employee_data in results:
            try:
                employee = Employee.objects.get(employee_id=employee_data['employee_id'])
                
                # Create or update processed attendance record
                record, created = ProcessedAttendance.objects.update_or_create(
                    employee=employee,
                    month=month,
                    year=year,
                    defaults={
                        'attendance_data': json.loads(json.dumps(employee_data, cls=DjangoJSONEncoder))
                    }
                )
                saved_records.append(record.id)
            except Employee.DoesNotExist:
                continue
            except Exception as e:
                print(f"Error saving attendance for employee {employee_data['employee_id']}: {str(e)}")
                continue
        
        return saved_records
    
    def fetch_punch_logs(self, start_date, end_date):
        # List of all biometric machines
        machines = [
            {'serial': 'CRJP232260279', 'username': 'Api', 'password': 'Api@123#$'},
            {'serial': 'CRJP224060053', 'username': 'Api', 'password': 'Api@123#$'},
            # Add other machines here
        ]
        
        all_logs = []
        
        # Adjust date range to include next day for night shift employees
        extended_end_date = end_date + timedelta(days=1)
        
        for machine in machines:
            try:
                # Prepare SOAP request
                url = "http://ampletrail.com/ssbforge/iclock/WebAPIService.asmx?op=GetTransactionsLog"
                headers = {
                    'Content-Type': 'text/xml; charset=utf-8',
                    'SOAPAction': 'http://tempuri.org/GetTransactionsLog',
                    'API-Key': '11'
                }
                
                # Format dates for SOAP request
                from_datetime = start_date.strftime('%Y-%m-%dT%H:%M:%S')
                to_datetime = extended_end_date.strftime('%Y-%m-%dT%H:%M:%S')
                
                xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetTransactionsLog xmlns="http://tempuri.org/">
      <FromDateTime>{from_datetime}</FromDateTime>
      <ToDateTime>{to_datetime}</ToDateTime>
      <SerialNumber>{machine['serial']}</SerialNumber>
      <UserName>{machine['username']}</UserName>
      <UserPassword>{machine['password']}</UserPassword>
      <strDataList></strDataList>
    </GetTransactionsLog>
  </soap:Body>
</soap:Envelope>"""
                
                # Make the request
                response = requests.post(url, headers=headers, data=xml_body)
                response.raise_for_status()
                
                # Parse the response (simplified - in real implementation use proper XML parsing)
                logs = self.parse_punch_logs_response(response.text)
                all_logs.extend(logs)
                
            except Exception as e:
                # Log error but continue with other machines
                print(f"Error fetching logs from machine {machine['serial']}: {str(e)}")
                continue
        
        # Sort all logs by datetime
        all_logs.sort(key=lambda x: x['datetime'])
        return all_logs
    
    def parse_punch_logs_response(self, xml_response):
        logs = []
        india_timezone = pytz.timezone('Asia/Kolkata')  # Define India Standard Time
        lines = xml_response.split('\n')
        for line in lines:
            if '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        emp_id = parts[0]
                        datetime_str = parts[1]
                        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                        # Make the datetime timezone-aware using datetime.timezone.utc
                        dt = django_timezone.make_aware(dt, timezone=india_timezone)
                        logs.append({
                            'employee_id': emp_id,
                            'datetime': dt
                        })
                    except ValueError:
                        continue
        return logs
    
    
    def process_employee_attendance(self, employee, start_date, end_date, gate_passes, 
                                  shift_assignments, od_slips, sunday_replacements, 
                                  holidays, manual_punches, punch_logs):
        # Initialize result structure
        result = {
            'employee_id': employee.employee_id,
            'employee_name': employee.employee_name,
            'department': employee.employee_department,
            'employee_type': employee.employee_type,
            'shift_type': employee.shift_type,
            'month': start_date.month,
            'year': start_date.year,
            'daily_attendance': [],
            'total_days_in_month': 0,
            'total_working_days': 0,
            'total_present_days': 0,
            'total_absent_days': 0,
            'total_leave_days': 0,
            'sundays_in_month': 0,  # Added this line for total Sundays in month
            'gets_sundays_off': employee.is_getting_sunday,  # Added this line
            'total_holiday_days': 0,
            'extra_days': {  # New field for tracking OD and other special days
                'od_display': '',  # <-- changed to string
                'od_days': Decimal('0.0'),
                'od_hours': Decimal('0.0'),  # Added this line for total OD hours
                'gate_pass_deductions': Decimal('0.0'),
                'total': Decimal('0.0')
            },
            'total_working_hours': Decimal('0.0'),
            'total_overtime_hours': Decimal('0.0'),
            'od_slips': [] 
            
        }

        replaced_sundays = 0
        regular_sundays = 0
        replacement_holidays = 0

        # Initialize counters
        present_days = Decimal('0.0')
        absent_days = Decimal('0.0')
        half_days = Decimal('0.0')


        def round_overtime(overtime_hours):
            """
            Round overtime to nearest 30 minutes (0.5 hours) but always round up
            if there's any overtime (minimum 0.5 hours)
            """
            if overtime_hours <= 0:
                return Decimal('0.0')
            
            # Convert to minutes
            total_minutes = overtime_hours * 60
            
            # Round up to nearest 30 minutes
            rounded_minutes = math.ceil(total_minutes / 30) * 30
            
            # Convert back to hours
            rounded_hours = Decimal(str(rounded_minutes / 60))
            return min(rounded_hours, Decimal('4.0'))

        def adjust_manual_punch_time(punch_time, is_manual):
            """Adjust manual punch time by subtracting 5:30 hours if it's a manual punch"""
            if is_manual and punch_time:
                return punch_time - timedelta(hours=5, minutes=30)
            return punch_time
                
        # Get employee's punch logs
        emp_logs = [log for log in punch_logs if log['employee_id'] == employee.employee_id]
        # In your process_employee_attendance method, add debug logging:
        # Get employee's manual punches
        emp_manual_punches = [mp for mp in manual_punches if mp.employee_id == employee.id]
        # First pass: Count special days before processing daily attendance
        for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1)):
            date = day.date()
            
            # Check for Sunday replacements
            if date.weekday() == 6:  # Sunday
                replacement = next((sr for sr in sunday_replacements 
                                if (sr.department is None or sr.department == employee.employee_department) 
                                and sr.sunday_date == date), None)
                
                if replacement:
                    replaced_sundays += 1
                    # Count the replacement date as a holiday
                    replacement_holidays += 1
                elif employee.is_getting_sunday:
                    regular_sundays += 1
        
        # Process each day in the month
        for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1)):
            date = day.date()
            
            # Initialize day record
            day_record = {
                'date': date,
                'day_type': 'Working Day',
                'shift_type': employee.shift_type,
                'scheduled_in': employee.working_time_in,
                'scheduled_out': employee.working_time_out,
                'actual_in': None,
                'actual_out': None,
                'is_manual_in': False,
                'is_manual_out': False,
                'manual_reason': None,
                'status': 'Absent',
                'working_hours': Decimal('0.0'),
                'overtime_hours': Decimal('0.0'),
                'gate_pass': None,
                'is_holiday': False,
                'holiday_name': None,
                'is_sunday_replaced': False,
                'replacement_date': None,
                'is_od': False,
                'od_hours': Decimal('0.0'),
                'od_days': Decimal('0.0'),
                'remarks': '',
                'night_shift_valid': None,  # New field to track night shift validity
                'is_half_day': False,  # Add this new field
                'day_value': Decimal('0.0'),  # New field: 1.0, 0.5 or 0.0
            }
            
            # Check if this is a rotational shift and if there's an assignment
            if employee.shift_type == 'ROT':
                assignment = next((sa for sa in shift_assignments 
                                 if sa.employee_id == employee.id and 
                                 sa.start_date <= date <= sa.end_date), None)
                if assignment:
                    day_record['shift_type'] = assignment.shift_type
                    day_record['scheduled_in'] = assignment.working_time_in
                    day_record['scheduled_out'] = assignment.working_time_out
            
            # Check if this is a holiday
            dept_holidays = [h for h in holidays 
                           if (h.department is None or h.department == employee.employee_department) 
                           and h.holiday_date == date]
            if dept_holidays:
                day_record['is_holiday'] = True
                day_record['holiday_name'] = dept_holidays[0].holiday_name
                day_record['day_type'] = 'Holiday'
                day_record['status'] = 'Holiday'
                result['total_holiday_days'] += 1
                result['daily_attendance'].append(day_record)
                continue
            
            # Check if this is a Sunday
            # In the process_employee_attendance method, replace the Sunday checking block with this:

            # Check if this is a Sunday
            if date.weekday() == 6:  # Sunday
                # Check for Sunday replacement first - this takes precedence
                replacement = next((sr for sr in sunday_replacements 
                                if (sr.department is None or sr.department == employee.employee_department) 
                                and sr.sunday_date == date), None)
                
                if replacement:
                    day_record['is_sunday_replaced'] = True
                    day_record['replacement_date'] = replacement.replacement_date
                    day_record['day_type'] = 'Sunday Replacement'
                    # For replaced Sundays, attendance is mandatory for all
                    day_record['status'] = 'Working on Replacement Day'
                elif employee.is_getting_sunday:
                    day_record['day_type'] = 'Sunday'
                    day_record['status'] = 'Sunday'
                    result['daily_attendance'].append(day_record)
                    continue
                else:
                    day_record['day_type'] = 'Sunday'
            
            # Check for OD slip
            od_slip = next((od for od in od_slips 
                          if od.employee_id == employee.id and od.od_date == date), None)
            if od_slip:
                day_record['is_od'] = True
                day_record['od_hours'] = od_slip.extra_hours
                day_record['od_days'] = od_slip.extra_days
                day_record['status'] = 'On Duty'
                result['extra_days']['od_days'] += Decimal(str(od_slip.extra_days))
                result['extra_days']['od_hours'] += Decimal(str(od_slip.extra_hours))  # Add OD hour
                result['od_slips'].append({
                    'date': od_slip.od_date,
                    'hours': od_slip.extra_hours,
                    'days': od_slip.extra_days,
                    'reason': od_slip.reason,
                    'approved_by': od_slip.approved_by
                })

                # Build the od_display string
                od_display = []
                if od_slip.extra_days:
                    od_display.append(f"{int(od_slip.extra_days)}d")
                if od_slip.extra_hours:
                    od_display.append(f"{int(od_slip.extra_hours)}h")
                day_record['remarks'] = f"OD - {' '.join(od_display)}"
                
                if od_display:
                    if result['extra_days']['od_display']:
                        # Append to existing if already present
                        result['extra_days']['od_display'] += " + " + ' '.join(od_display)
                    else:
                        result['extra_days']['od_display'] = ' '.join(od_display)

              
                total_od_days = int(result['extra_days']['od_days'])
                total_od_hours = int(result['extra_days']['od_hours'])
                # Convert hours and days to a combined string like "1d 5h"
                od_display = []
                if total_od_days > 0:
                    od_display.append(f"{total_od_days}d")
                if total_od_hours > 0:
                    od_display.append(f"{total_od_hours}h")
                
                result['extra_days']['od_display'] = ' '.join(od_display) if od_display else ''
                

            
            # Check for gate pass
            gate_pass = next((gp for gp in gate_passes 
                    if gp.employee_id == employee.id and gp.date == date), None)
            if gate_pass:
                day_record['gate_pass'] = {
                    'date': gate_pass.date,
                    'out_time': gate_pass.out_time,
                    'approved_by': gate_pass.approved_by,
                    'action_taken': gate_pass.action_taken,
                    'reason': gate_pass.reason
                }
                
                if gate_pass.action_taken == 'FD':
                    day_record['status'] = 'Present (Full Day Gate Pass)'
                    result['total_present_days'] += Decimal('1.0')  # <-- Add this line
                elif gate_pass.action_taken == 'HD':
                    day_record['status'] = 'Half Day (Gate Pass)'
                    day_record['working_hours'] = employee.working_hours / 2
                    # Change present days count to 0.5 for half days
                    result['total_present_days'] += Decimal('0.5')
                elif gate_pass.action_taken == 'FD_CUT':
                    day_record['status'] = 'Absent (Full Day Cut Gate Pass)'
                    result['extra_days']['gate_pass_deductions'] += Decimal('1.0')
                    day_record['remarks'] = f'Gate Pass - Full Day Cut (-1 day) - {gate_pass.reason}'
                elif gate_pass.action_taken == 'HD_CUT':
                    day_record['status'] = 'Half Day (Gate Pass Cut)'
                    result['extra_days']['gate_pass_deductions'] += Decimal('0.5')
                    day_record['remarks'] = f'Gate Pass - Half Day Cut (-0.5 day) - {gate_pass.reason}'
                    day_record['working_hours'] = employee.working_hours / 2
                    # Change present days count to 0.5 for half day cuts
                    result['total_present_days'] += Decimal('0.5')
            
            # Get all punches for this day
            day_start = django_timezone.make_aware(datetime.combine(date, time.min))
            day_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time.min))
            
            # For night shift, include next day's morning punches
            if day_record['shift_type'] == 'NIGHT':
                day_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time(23, 59, 59)))
            
            day_punches = []
            for log in emp_logs:
                log_time = log['datetime']
                # Ensure both datetimes are timezone-aware for comparison
                if django_timezone.is_aware(day_start) and not django_timezone.is_aware(log_time):
                    log_time = django_timezone.make_aware(log_time)
                elif not django_timezone.is_aware(day_start) and django_timezone.is_aware(log_time):
                    day_start = django_timezone.make_aware(day_start)
                    day_end = django_timezone.make_aware(day_end)
                
                if day_start <= log_time < day_end:
                    day_punches.append(log)
            
            # Add manual punches
            manual_in = next((
                mp for mp in emp_manual_punches 
                if mp.punch_in_time and 
                (
                    mp.punch_in_time.date() == date or 
                    (
                        mp.punch_in_time.date() == date + timedelta(days=1) and 
                        mp.punch_in_time.time() < time(12, 0)
                    )
                )
            ), None)

            if manual_in:
    # Ensure the manual punch time is timezone-aware
                punch_in_time = django_timezone.make_aware(manual_in.punch_in_time) if not django_timezone.is_aware(manual_in.punch_in_time) else manual_in.punch_in_time
                day_punches.append({
                    'employee_id': employee.employee_id,
                    'datetime': punch_in_time,
                    'is_manual': True
                })
                day_record['is_manual_in'] = True
                day_record['manual_reason'] = manual_in.reason

            
            manual_out = next((
                mp for mp in emp_manual_punches 
                if mp.punch_out_time and 
                (
                    mp.punch_out_time.date() == date or 
                    (
                        mp.punch_out_time.date() == date + timedelta(days=1) and 
                        mp.punch_out_time.time() < time(12, 0)
                    )
                )
            ), None)

            if manual_out:
                # Ensure the manual punch time is timezone-aware
                punch_out_time = django_timezone.make_aware(manual_out.punch_out_time) if not django_timezone.is_aware(manual_out.punch_out_time) else manual_out.punch_out_time
                day_punches.append({
                    'employee_id': employee.employee_id,
                    'datetime': punch_out_time,
                    'is_manual': True
                })
                day_record['is_manual_out'] = True
                day_record['manual_reason'] = manual_out.reason
                        
            # Sort punches by time
            day_punches.sort(key=lambda x: x['datetime'])
            
            # Process punches based on shift type
            if day_record['shift_type'] in ['DAY', 'ROT']:
                # For day shift, first punch is IN, last is OUT
                if len(day_punches) >= 2:
                    day_record['actual_in'] = day_punches[0]['datetime'].time()
                    day_record['actual_out'] = day_punches[-1]['datetime'].time()
                    day_record['status'] = 'Present'
                    
                    # Calculate working hours
                    in_dt = day_punches[0]['datetime']
                    out_dt = day_punches[-1]['datetime']
                    worked_hours = (out_dt - in_dt).total_seconds() / 3600
                    day_record['working_hours'] = Decimal(str(round(worked_hours, 2)))

                    # NEW: Check for early departure (before 4 PM for day shift)
                    if out_dt.time() < time(16, 0) and not gate_pass:
                        day_record['status'] = 'Half Day (Early Departure)'
                        day_record['working_hours'] = Decimal(str(round(worked_hours/2, 2)))
                        day_record['remarks'] = 'Left before 4 PM without gate pass'
                        # Count as half day
                        result['total_present_days'] += Decimal('0.5')
                    else:
                        result['total_present_days'] += Decimal('1.0')

                    
                    
                    # Calculate overtime if eligible
                    if employee.is_getting_ot and not day_record['is_od']:
                        scheduled_out_dt = django_timezone.make_aware(datetime.combine(date, day_record['scheduled_out']))
                        if out_dt.tzinfo is None:
                            out_dt = timezone.make_aware(out_dt)  # Only make it aware if it is naive
                        if day_record['is_manual_out']:
                            out_dt = adjust_manual_punch_time(out_dt, True)
                        if scheduled_out_dt.tzinfo is None:
                            scheduled_out_dt = timezone.make_aware(scheduled_out_dt)  # Same for scheduled_out_dt
                        if out_dt > scheduled_out_dt:
                            overtime = (out_dt - scheduled_out_dt).total_seconds() / 3600
                            rounded_overtime = round_overtime(overtime)
                            day_record['overtime_hours'] = rounded_overtime
                            result['total_overtime_hours'] += rounded_overtime
                    
                    # NEW: Handle single punch case
                elif len(day_punches) == 1 and not gate_pass:
                    punch_time = day_punches[0]['datetime'].time()
                    day_record['actual_in'] = punch_time
                    day_record['status'] = 'Half Day (Single Punch)'
                    day_record['remarks'] = 'Only one punch recorded without gate pass'
                    # Count as half day
                    result['total_present_days'] += Decimal('0.5')
                    # Estimate working hours as half day
                    day_record['working_hours'] = employee.working_hours / 2
            
            elif day_record['shift_type'] == 'NIGHT':
                # For night shift, we need to look at punches from current evening to next morning
                night_start = django_timezone.make_aware(datetime.combine(date, time(16, 0)))  # 4 PM
                night_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time(12, 0))) 
                
                # Get all punches in this extended window
                night_punches = [log for log in emp_logs if night_start <= log['datetime'] < night_end]
                if manual_in:
                    night_punches.append({
                        'employee_id': employee.employee_id,
                        'datetime': manual_in.punch_in_time,
                        'is_manual': True
                    })
                if manual_out:
                    night_punches.append({
                        'employee_id': employee.employee_id,
                        'datetime': manual_out.punch_out_time,
                        'is_manual': True
                    })
                
                if len(night_punches) >= 2:
                    # Sort by time
                    night_punches.sort(key=lambda x: x['datetime'])
                    
                    # First punch is IN, last is OUT
                    in_punch = night_punches[0]['datetime']
                    out_punch = night_punches[-1]['datetime']
                    
                    # Calculate if this is a valid night shift
                    is_valid_night_shift = (
                        in_punch.time() >= time(16, 0) and  # 4 PM or later
                        out_punch.time() <= time(12, 0) and  # Noon or earlier
                        (out_punch - in_punch).total_seconds() >= 8 * 3600  # At least 8 hours
                    )
                    
                    day_record['night_shift_valid'] = is_valid_night_shift
                    
                    if is_valid_night_shift:
                        day_record['actual_in'] = in_punch.time()
                        day_record['actual_out'] = out_punch.time()
                        day_record['status'] = 'Present'
                        
                        # Calculate working hours
                        worked_hours = (out_punch - in_punch).total_seconds() / 3600
                        day_record['working_hours'] = Decimal(str(round(worked_hours, 2)))

                         # NEW: Check for early departure (before 4 AM for night shift)
                        if out_punch.time() < time(4, 0) and not gate_pass:
                            day_record['status'] = 'Half Day (Early Departure)'
                            day_record['working_hours'] = Decimal(str(round(worked_hours/2, 2)))
                            day_record['remarks'] = 'Left before 4 AM without gate pass'
                            # Count as half day
                            result['total_present_days'] += Decimal('0.5')
                        else:
                            result['total_present_days'] += Decimal('1.0')
                        
                        # Calculate overtime if eligible
                        if employee.is_getting_ot and not day_record['is_od']:
                            scheduled_out_dt = django_timezone.make_aware(datetime.combine(
                                date + timedelta(days=1),
                                day_record['scheduled_out']
                            ))
                            out_punch = night_punches[-1]['datetime']
                            if day_record['is_manual_out']:
                                out_punch = adjust_manual_punch_time(out_punch, True)
                            # Ensure out_punch is timezone-aware
                            if not django_timezone.is_aware(out_punch):
                                out_punch = django_timezone.make_aware(out_punch)
                            if out_punch > scheduled_out_dt:
                                overtime = (out_punch - scheduled_out_dt).total_seconds() / 3600
                                rounded_overtime = round_overtime(overtime)
                                day_record['overtime_hours'] = rounded_overtime
                                result['total_overtime_hours'] += rounded_overtime
                    else:
                        day_record['remarks'] = 'Night shift validation failed - check timings'
                else:
                    # NEW: Handle single punch case for night shift
                    if len(night_punches) == 1 and not gate_pass:
                        punch_time = night_punches[0]['datetime'].time()
                        day_record['actual_in'] = punch_time
                        day_record['status'] = 'Half Day (Single Punch)'
                        day_record['remarks'] = 'Only one punch recorded without gate pass'
                        # Count as half day
                        result['total_present_days'] += Decimal('0.5')
                        # Estimate working hours as half day
                        day_record['working_hours'] = employee.working_hours / 2
                    else:
                        day_record['remarks'] = f'Insufficient punches found ({len(night_punches)}) for night shift'
            
             # Determine day value based on status - MODIFIED SECTION
            if day_record['status'] == 'Present':
                day_record['day_value'] = Decimal('1.0')
                present_days += Decimal('1.0')
            elif day_record['status'].startswith('Half Day'):
                day_record['day_value'] = Decimal('0.5')
                present_days += Decimal('0.5')
                half_days += Decimal('0.5')
            elif day_record['status'] == 'Absent':
                day_record['day_value'] = Decimal('0.0')
                absent_days += Decimal('1.0')
            elif day_record['status'] == 'Holiday':
                day_record['day_value'] = Decimal('0.0')
            elif day_record['status'] == 'Sunday' and employee.is_getting_sunday:
                day_record['day_value'] = Decimal('0.0')


            # ... (rest of day processing)

            result['daily_attendance'].append(day_record)

        # Calculate total working days - MODIFIED CALCULATION
        total_days_in_month = (end_date - start_date).days
        regular_sundays = sum(
            1 for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1))
            if day.date().weekday() == 6 and  # Sunday
            not any(sr for sr in sunday_replacements 
                if (sr.department is None or sr.department == employee.employee_department) 
                and sr.sunday_date == day.date())
        )
         # Count half days as 0.5 in working days
        half_day_count = sum(1 for day in result['daily_attendance'] if day.get('is_half_day', False))

        result['total_days_in_month'] = (
           total_days_in_month
        )
         # Calculate total extra days at the end
        result['extra_days']['total'] = (
            result['extra_days']['od_days'] -
            result['extra_days']['gate_pass_deductions']
        )
        sundays_in_month = sum(
            1 for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1))
            if day.date().weekday() == 6  # Sunday
        )
        result['sundays_in_month'] = sundays_in_month
       

        
        # Calculate total working days (excluding holidays, Sundays unless replaced)
        result['total_working_days'] = (
            total_days_in_month - 
            regular_sundays - 
            result['total_holiday_days'] +
            replaced_sundays
        )
        result['total_present_days'] = present_days
        result['total_absent_days'] = absent_days+half_days
        result['total_half_days'] = half_days  # New field for tracking
        
        
        return result
    

# views.py
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Employee, GatePass, ShiftAssignment, 
    ODSlip, SundayReplacement, Holiday, ManualPunch
)
from .serializers import (
    EmployeeSerializer, GatePassSerializer, 
    ShiftAssignmentSerializer, ODSlipSerializer,
    SundayReplacementSerializer, HolidaySerializer,
    ManualPunchSerializer
)
import django_filters

# Custom filters for each model
class EmployeeFilter(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(field_name='employee_id', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee_name', lookup_expr='icontains')
    employee_department = django_filters.CharFilter(field_name='employee_department')
    employee_type = django_filters.CharFilter(field_name='employee_type')
    shift_type = django_filters.CharFilter(field_name='shift_type')
    
    class Meta:
        model = Employee
        fields = ['employee_id', 'employee_name', 'employee_department', 'employee_type', 'shift_type']

class GatePassFilter(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(field_name='employee__employee_id', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee__employee_name', lookup_expr='icontains')
    date = django_filters.DateFromToRangeFilter(field_name='date')
    action_taken = django_filters.CharFilter(field_name='action_taken')
    
    class Meta:
        model = GatePass
        fields = ['employee_id', 'employee_name', 'date', 'action_taken']

class ShiftAssignmentFilter(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(field_name='employee__employee_id', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee__employee_name', lookup_expr='icontains')
    shift_type = django_filters.CharFilter(field_name='shift_type')
    start_date = django_filters.DateFromToRangeFilter(field_name='start_date')
    end_date = django_filters.DateFromToRangeFilter(field_name='end_date')
    
    class Meta:
        model = ShiftAssignment
        fields = ['employee_id', 'employee_name', 'shift_type', 'start_date', 'end_date']

class ODSlipFilter(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(field_name='employee__employee_id', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee__employee_name', lookup_expr='icontains')
    od_date = django_filters.DateFromToRangeFilter(field_name='od_date')
    
    class Meta:
        model = ODSlip
        fields = ['employee_id', 'employee_name', 'od_date']

class SundayReplacementFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department')
    sunday_date = django_filters.DateFromToRangeFilter(field_name='sunday_date')
    replacement_date = django_filters.DateFromToRangeFilter(field_name='replacement_date')
    
    class Meta:
        model = SundayReplacement
        fields = ['department', 'sunday_date', 'replacement_date']

class HolidayFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department')
    holiday_date = django_filters.DateFromToRangeFilter(field_name='holiday_date')
    holiday_name = django_filters.CharFilter(field_name='holiday_name', lookup_expr='icontains')
    
    class Meta:
        model = Holiday
        fields = ['department', 'holiday_date', 'holiday_name']

class ManualPunchFilter(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(field_name='employee__employee_id', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee__employee_name', lookup_expr='icontains')
    date = django_filters.DateFilter(field_name='punch_in_time', lookup_expr='date')
    date_range = django_filters.DateFromToRangeFilter(field_name='punch_in_time', lookup_expr='date')
    
    class Meta:
        model = ManualPunch
        fields = ['employee_id', 'employee_name', 'date', 'date_range']

# ViewSets for each model
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().select_related()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ['employee_id', 'employee_name', 'father_name']
    ordering_fields = ['employee_id', 'employee_name', 'employee_department']
    ordering = ['employee_id']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)  # Console output
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_details = serializer.errors
            print("Validation errors:", error_details)
            logger.error("Validation error during Employee creation: %s", error_details)
            return Response(error_details, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class EmployeeViewSet1(viewsets.ModelViewSet):
    queryset = Employee.objects.all().select_related()
    serializer_class = EmployeeSerializer
    pagination_class = None  # <-- disables pagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ['employee_id', 'employee_name', 'father_name']
    ordering_fields = ['employee_id', 'employee_name', 'employee_department']
    ordering = ['employee_id']

class EmployeeViewSet2(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    pagination_class = None  # disables pagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ['employee_id', 'employee_name', 'father_name']
    ordering_fields = ['employee_id', 'employee_name', 'employee_department']
    ordering = ['employee_id']

    def get_queryset(self):
        return Employee.objects.filter(shift_type='ROT').select_related()

class GatePassViewSet(viewsets.ModelViewSet):
    queryset = GatePass.objects.all().select_related('employee')
    serializer_class = GatePassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = GatePassFilter
    search_fields = ['employee__employee_id', 'employee__employee_name', 'approved_by']
    ordering_fields = ['date', 'out_time', 'employee__employee_name']
    ordering = ['-date']

class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ShiftAssignment.objects.all().select_related('employee')
    serializer_class = ShiftAssignmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ShiftAssignmentFilter
    search_fields = ['employee__employee_id', 'employee__employee_name']
    ordering_fields = ['start_date', 'end_date', 'employee__employee_name']
    ordering = ['-start_date']

class ODSlipViewSet(viewsets.ModelViewSet):
    queryset = ODSlip.objects.all().select_related('employee')
    serializer_class = ODSlipSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ODSlipFilter
    search_fields = ['employee__employee_id', 'employee__employee_name', 'approved_by']
    ordering_fields = ['od_date', 'employee__employee_name']
    ordering = ['-od_date']

class SundayReplacementViewSet(viewsets.ModelViewSet):
    queryset = SundayReplacement.objects.all()
    serializer_class = SundayReplacementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SundayReplacementFilter
    ordering_fields = ['sunday_date', 'replacement_date']
    ordering = ['-sunday_date']

class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = HolidayFilter
    search_fields = ['holiday_name']
    ordering_fields = ['holiday_date']
    ordering = ['-holiday_date']

class ManualPunchViewSet(viewsets.ModelViewSet):
    queryset = ManualPunch.objects.all().select_related('employee')
    serializer_class = ManualPunchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ManualPunchFilter
    search_fields = ['employee__employee_id', 'employee__employee_name', 'approved_by']
    ordering_fields = ['punch_in_time', 'punch_out_time']
    ordering = ['-punch_in_time']


from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ProcessedAttendance
from .serializers import ProcessedAttendanceSerializer
from django.core.cache import cache
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

class ProcessedAttendanceAPIView(generics.ListAPIView):
    serializer_class = ProcessedAttendanceSerializer
    permission_classes = []
    
    def get_queryset(self):
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        employee_id = self.request.query_params.get('employee_id')
        
        if not month or not year:
            return ProcessedAttendance.objects.none()
            
        # Create cache key
        cache_key = f"attendance_{year}_{month}"
        if employee_id:
            cache_key += f"_{employee_id}"
            
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Returning cached data for {cache_key}")
            return cached_data
            
        # Build the query
        query = Q(month=month, year=year)
        if employee_id:
            query &= Q(employee_id=employee_id)
            
        # Optimize the queryset
        queryset = ProcessedAttendance.objects.filter(query).select_related(
            'employee'
        ).only(
            'id', 'month', 'year', 'attendance_data', 
            'employee__id', 'employee__employee_name'
        )
        
        # Cache the queryset
        cache.set(cache_key, queryset, timeout=settings.CACHE_TTL)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            month = int(request.query_params.get('month'))
            year = int(request.query_params.get('year'))
            
            if not (1 <= month <= 12):
                return Response(
                    {"error": "Month must be between 1 and 12"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            queryset = self.get_queryset()
            
            # Directly return all the results without pagination
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid month or year parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )


class MissedPunchReportAPI(APIView):
    def post(self, request):
        # Get input parameters
        month = request.data.get('month')
        year = request.data.get('year')
        specific_date = request.data.get('date')
        
        # Validate input
        if not (month and year) and not specific_date:
            return Response(
                {"error": "Either month/year or specific date is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if specific_date:
                # Process single date
                date_obj = datetime.strptime(specific_date, '%Y-%m-%d').date()
                start_date = date_obj
                end_date = date_obj + timedelta(days=1)
            else:
                # Process entire month
                month = int(month)
                year = int(year)
                if month < 1 or month > 12:
                    raise ValueError
                start_date = datetime(year, month, 1).date()
                if month == 12:
                    end_date = datetime(year+1, 1, 1).date()
                else:
                    end_date = datetime(year, month+1, 1).date()
        except ValueError:
            return Response(
                {"error": "Invalid date format or month/year values"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all employees
        employees = Employee.objects.all()
        
        # Fetch all relevant data in bulk for performance
        gate_passes = GatePass.objects.filter(
            employee__in=employees,
            date__gte=start_date,
            date__lt=end_date
        ).select_related('employee')
        
        shift_assignments = ShiftAssignment.objects.filter(
            employee__in=employees,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('employee')

        od_slips = ODSlip.objects.filter(
            employee__in=employees,
            od_date__gte=start_date,
            od_date__lt=end_date
        ).select_related('employee')
        
        sunday_replacements = SundayReplacement.objects.filter(
            Q(department__isnull=True) | Q(department__in=[emp.employee_department for emp in employees]),
            sunday_date__gte=start_date,
            sunday_date__lt=end_date
        )
        
        holidays = Holiday.objects.filter(
            Q(department__isnull=True) | Q(department__in=[emp.employee_department for emp in employees]),
            holiday_date__gte=start_date,
            holiday_date__lt=end_date
        )
        
        # Replace the manual punch filtering with this:
        manual_punches = ManualPunch.objects.filter(
            employee__in=employees
        ).filter(
            Q(punch_in_time__date__gte=start_date, punch_in_time__date__lt=end_date + timedelta(days=1)) |
            Q(punch_out_time__date__gte=start_date, punch_out_time__date__lt=end_date + timedelta(days=1))
        ).select_related('employee')
        
        # Fetch punch logs from all machines
        punch_logs = self.fetch_punch_logs(start_date, end_date)
        
        # Process each employee to find missed punches
        missed_punch_data = []
        
        for employee in employees:
            # Process each day in the date range
            for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1)):
                date = day.date()
                
                # Skip holidays
                dept_holidays = [h for h in holidays 
                               if (h.department is None or h.department == employee.employee_department) 
                               and h.holiday_date == date]
                if dept_holidays:
                    continue
                
                # Skip Sundays for employees who get Sundays off
                if date.weekday() == 6 and employee.is_getting_sunday:
                    replacement = next((sr for sr in sunday_replacements 
                                    if (sr.department is None or sr.department == employee.employee_department) 
                                    and sr.sunday_date == date), None)
                    if not replacement:
                        continue
                
                # Check for OD slip (employee is on official duty)
                od_slip = next((od for od in od_slips 
                              if od.employee_id == employee.id and od.od_date == date), None)
                if od_slip:
                    continue
                
                # Check for gate pass (already accounted for)
                gate_pass = next((gp for gp in gate_passes 
                              if gp.employee_id == employee.id and gp.date == date), None)
                if gate_pass:
                    continue
                
                # Get employee's shift for this day
                shift_type = employee.shift_type
                scheduled_in = employee.working_time_in
                scheduled_out = employee.working_time_out
                
                if shift_type == 'ROT':
                    assignment = next((sa for sa in shift_assignments 
                                     if sa.employee_id == employee.id and 
                                     sa.start_date <= date <= sa.end_date), None)
                    if assignment:
                        shift_type = assignment.shift_type
                        scheduled_in = assignment.working_time_in
                        scheduled_out = assignment.working_time_out
                
                # Get employee's punch logs for this day
                day_start = django_timezone.make_aware(datetime.combine(date, time.min))
                day_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time.min))
                
                # For night shift, include next day's morning punches
                if shift_type == 'NIGHT':
                    day_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time(23, 59, 59)))
                
                day_punches = []
                for log in punch_logs:
                    if log['employee_id'] == employee.employee_id:
                        log_time = log['datetime']
                        if django_timezone.is_aware(day_start) and not django_timezone.is_aware(log_time):
                            log_time = django_timezone.make_aware(log_time)
                        elif not django_timezone.is_aware(day_start) and django_timezone.is_aware(log_time):
                            day_start = django_timezone.make_aware(day_start)
                            day_end = django_timezone.make_aware(day_end)
                        
                        if day_start <= log_time < day_end:
                            day_punches.append(log)
                
                # Add manual punches
                emp_manual_punches = [mp for mp in manual_punches if mp.employee_id == employee.id]
                manual_in = next((mp for mp in emp_manual_punches 
                                if mp.punch_in_time and mp.punch_in_time.date() == date), None)
                if manual_in:
                    punch_in_time = django_timezone.make_aware(manual_in.punch_in_time) if not django_timezone.is_aware(manual_in.punch_in_time) else manual_in.punch_in_time
                    day_punches.append({
                        'employee_id': employee.employee_id,
                        'datetime': punch_in_time,
                        'is_manual': True
                    })
                
                manual_out = next((mp for mp in emp_manual_punches 
                                 if mp.punch_out_time and mp.punch_out_time.date() == date), None)
                if manual_out:
                    punch_out_time = django_timezone.make_aware(manual_out.punch_out_time) if not django_timezone.is_aware(manual_out.punch_out_time) else manual_out.punch_out_time
                    day_punches.append({
                        'employee_id': employee.employee_id,
                        'datetime': punch_out_time,
                        'is_manual': True
                    })
                
                # Sort punches by time
                day_punches.sort(key=lambda x: x['datetime'])
                
                # Determine missed punch status
                missed_punch_details = None
                
                if shift_type in ['DAY', 'ROT']:
                    if len(day_punches) == 0:
                        # No punches at all
                        missed_punch_details = {
                            'date': date,
                            'missed_type': 'BOTH',
                            'details': 'No punch in or out recorded'
                        }
                    elif len(day_punches) == 1:
                        # Only one punch (could be in or out)
                        punch_time = day_punches[0]['datetime'].time()
                        if punch_time < time(12, 0):
                            # Morning punch (missing out punch)
                            missed_punch_details = {
                                'date': date,
                                'missed_type': 'OUT',
                                'details': 'Only punch in recorded at {}'.format(punch_time.strftime('%H:%M'))
                            }
                        else:
                            # Afternoon punch (missing in punch)
                            missed_punch_details = {
                                'date': date,
                                'missed_type': 'IN',
                                'details': 'Only punch out recorded at {}'.format(punch_time.strftime('%H:%M'))
                            }
                
                elif shift_type == 'NIGHT':
                    if len(day_punches) == 0:
                        # No punches at all
                        missed_punch_details = {
                            'date': date,
                            'missed_type': 'BOTH',
                            'details': 'No punch in or out recorded for night shift'
                        }
                    elif len(day_punches) == 1:
                        punch_time = day_punches[0]['datetime'].time()
                        if punch_time >= time(16, 0):
                            # Evening punch (missing out punch next morning)
                            missed_punch_details = {
                                'date': date,
                                'missed_type': 'OUT',
                                'details': 'Only night shift punch in recorded at {}'.format(punch_time.strftime('%H:%M'))
                            }
                        else:
                            # Morning punch (missing in punch previous evening)
                            missed_punch_details = {
                                'date': date,
                                'missed_type': 'IN',
                                'details': 'Only night shift punch out recorded at {}'.format(punch_time.strftime('%H:%M'))
                            }
                
                if missed_punch_details:
                    missed_punch_data.append({
                        'employee_id': employee.employee_id,
                        'employee_name': employee.employee_name,
                        'department': employee.employee_department,
                        'date': missed_punch_details['date'],
                        'missed_type': missed_punch_details['missed_type'],
                        'details': missed_punch_details['details'],
                        'shift_type': shift_type,
                        'scheduled_in': scheduled_in.strftime('%H:%M') if scheduled_in else None,
                        'scheduled_out': scheduled_out.strftime('%H:%M') if scheduled_out else None
                    })
        
        return Response(missed_punch_data, status=status.HTTP_200_OK)
    
    def fetch_punch_logs(self, start_date, end_date):
        # (Same implementation as in your ProcessAttendanceAPI)
        # List of all biometric machines
        machines = [
            {'serial': 'CRJP232260279', 'username': 'Api', 'password': 'Api@123#$'},
            {'serial': 'CRJP224060053', 'username': 'Api', 'password': 'Api@123#$'},
            # Add other machines here
        ]
        
        all_logs = []
        
        # Adjust date range to include next day for night shift employees
        extended_end_date = end_date + timedelta(days=1)
        
        for machine in machines:
            try:
                # Prepare SOAP request
                url = "http://ampletrail.com/ssbforge/iclock/WebAPIService.asmx?op=GetTransactionsLog"
                headers = {
                    'Content-Type': 'text/xml; charset=utf-8',
                    'SOAPAction': 'http://tempuri.org/GetTransactionsLog',
                    'API-Key': '11'
                }
                
                # Format dates for SOAP request
                from_datetime = start_date.strftime('%Y-%m-%dT%H:%M:%S')
                to_datetime = extended_end_date.strftime('%Y-%m-%dT%H:%M:%S')
                
                xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetTransactionsLog xmlns="http://tempuri.org/">
      <FromDateTime>{from_datetime}</FromDateTime>
      <ToDateTime>{to_datetime}</ToDateTime>
      <SerialNumber>{machine['serial']}</SerialNumber>
      <UserName>{machine['username']}</UserName>
      <UserPassword>{machine['password']}</UserPassword>
      <strDataList></strDataList>
    </GetTransactionsLog>
  </soap:Body>
</soap:Envelope>"""
                
                # Make the request
                response = requests.post(url, headers=headers, data=xml_body)
                response.raise_for_status()
                
                # Parse the response (simplified - in real implementation use proper XML parsing)
                logs = self.parse_punch_logs_response(response.text)
                all_logs.extend(logs)
                
            except Exception as e:
                # Log error but continue with other machines
                print(f"Error fetching logs from machine {machine['serial']}: {str(e)}")
                continue
        
        # Sort all logs by datetime
        all_logs.sort(key=lambda x: x['datetime'])
        return all_logs
    
    def parse_punch_logs_response(self, xml_response):
        # (Same implementation as in your ProcessAttendanceAPI)
        logs = []
        india_timezone = pytz.timezone('Asia/Kolkata')  # Define India Standard Time
        lines = xml_response.split('\n')
        for line in lines:
            if '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        emp_id = parts[0]
                        datetime_str = parts[1]
                        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                        # Make the datetime timezone-aware using datetime.timezone.utc
                        dt = django_timezone.make_aware(dt, timezone=india_timezone)
                        logs.append({
                            'employee_id': emp_id,
                            'datetime': dt
                        })
                    except ValueError:
                        continue
        return logs
    

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProcessedAttendance, Employee,ProcessedSalary
import math
from datetime import datetime

class SalaryCalculationAPI(APIView):
    """
    API endpoint for calculating employee salaries based on attendance data.
    Handles large datasets efficiently with optimized queries.
    """
    def post(self, request, format=None):
        """
        Save processed salary data for a month/year
        """
        month = request.data.get('month')
        year = request.data.get('year')
        results = request.data.get('results', [])
        
        if not month or not year:
            return Response(
                {"error": "Both month and year parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "Invalid month or year format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if data already exists for this month/year
        if ProcessedSalary.objects.filter(month=month, year=year).exists():
            return Response(
                {"error": "Salary data already processed for this month/year"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create salary records in bulk
        salary_records = []
        for result in results:
            try:
                employee = Employee.objects.get(employee_id=result['employee_id'])
                salary_records.append(ProcessedSalary(
                    employee=employee,
                    month=month,
                    year=year,
                    data=result
                ))
            except Employee.DoesNotExist:
                continue  # Or collect these missing employees for error reporting

        
        try:
            ProcessedSalary.objects.bulk_create(salary_records)
            return Response(
                {"message": f"Successfully saved {len(salary_records)} salary records"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, format=None):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        if not month or not year:
            return Response(
                {"error": "Both month and year parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "Invalid month or year format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start timing for performance measurement
        start_time = datetime.now()
        
        # Bulk fetch all processed attendance for the month/year to minimize DB queries
        attendance_records = ProcessedAttendance.objects.filter(
            month=month,
            year=year
        ).select_related('employee')
        
        # Get all employee IDs in one query
        employee_ids = attendance_records.values_list('employee__employee_id', flat=True)
        
        # Bulk fetch all relevant employees to minimize DB queries
        employees = Employee.objects.filter(
            employee_id__in=employee_ids
        ).only(
            'employee_id', 'employee_name', 'employee_department', 'salary',
            'is_getting_sunday', 'is_getting_ot', 'no_of_cl', 'employee_type','working_hours'
        )
        
        # Create a dictionary for quick employee lookup
        employee_dict = {emp.employee_id: emp for emp in employees}
        
        results = []
        
        for record in attendance_records:
            employee = employee_dict.get(record.employee.employee_id)
            if not employee:
                continue
                
            attendance_data = record.attendance_data
            
            # Calculate salary components
            salary_breakdown = self.calculate_salary(employee, attendance_data)
            
            results.append({
                "employee_id": employee.employee_id,
                "employee_name": employee.employee_name,
                "department": employee.employee_department,
                "employee_type": employee.employee_type,
                "month": month,
                "year": year,
                "total_month_days": attendance_data.get('total_days_in_month', 30),
                "total_working_days": attendance_data.get('total_working_days', 0),
                "present_days": attendance_data.get('total_present_days', 0),
                "sundays": attendance_data.get('sundays_in_month', 0),
                "absent_days": attendance_data.get('total_absent_days', 0),
                "leave_days": attendance_data.get('total_leave_days', 0),
                "holiday_days": attendance_data.get('total_holiday_days', 0),
                "od_days": attendance_data.get('extra_days', {}).get('od_days', 0),
                "od_hours": attendance_data.get('extra_days', {}).get('od_hours', 0),
                "overtime_hours": attendance_data.get('total_overtime_hours', 0),
                "actual_salary": float(employee.salary),
                **salary_breakdown
            })
        
        # End timing and log performance
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Processed {len(results)} salaries in {processing_time} seconds")
        
        return Response({
            "month": month,
            "year": year,
            "count": len(results),
            "processing_time_seconds": processing_time,
            "results": results
        })
    
    def calculate_salary(self, employee, attendance_data):
        """
        Calculate all salary components based on employee data and attendance.
        Handles CL days by:
        1. Subtracting CL from absent days and adding to present days
        2. Only considering the CL days the employee actually has (no_of_cl)
        3. Deducting Sundays after adjusting for CL
        """
        # Initialize all components with 0
        salary_components = {
            "gross_salary": 0,
            "basic_salary": 0,
            "hra": 0,
            "medical_allowance": 0,
            "conveyance_allowance": 0,
            "pf": 0,
            "esic": 0,
            "incentive": 0,
            "overtime_payment": 0,
            "od_payment": 0,
            "total_salary": 0
        }
        
        if not employee.salary or employee.salary <= 0:
            return salary_components
        
        total_days = int(attendance_data.get('total_days_in_month', 30))
        present_days = int(float(attendance_data.get('total_present_days', 0)))
        absent_days = int(float(attendance_data.get('total_absent_days', 0))) 
        sundays = int(attendance_data.get('sundays_in_month', 0))
        print(f'sunday{sundays}')
        leave_days = int(float(attendance_data.get('total_leave_days', 0)))
        per_day_salary = float(employee.salary) / total_days
        
        # Handle CL days - subtract from absent and add to present
        available_cl = employee.no_of_cl  # Total CL available to the employee
        working_hours = employee.working_hours  # Total CL available to the employee
        cl_used = min(available_cl, absent_days)  # Can't use more CL than absent days
        
        # Adjust present and absent days based on CL usage 
        adjusted_present = present_days + cl_used
        adjusted_absent = absent_days - cl_used
        
        # Calculate eligible sundays based on adjusted absent days
        eligible_sundays = sundays if employee.is_getting_sunday else 0
        
        # Apply sunday deduction rules based on adjusted absent days
        if eligible_sundays > 0 and adjusted_absent >= 3:
            if adjusted_absent >= 10:
                eligible_sundays = 0
            elif adjusted_absent >= 6:
                eligible_sundays = max(0, eligible_sundays - 2)
            else:
                eligible_sundays = max(0, eligible_sundays - 1)
        print(adjusted_present)
        print(eligible_sundays)
        print(per_day_salary)
        # Calculate gross salary using adjusted present days and eligible sundays
        gross_salary = round((adjusted_present + eligible_sundays) * per_day_salary, 2)
        print(gross_salary)
        
        # Calculate salary components
        basic_salary = round(gross_salary / 2, 2)
        
        # PF calculation (12% of basic, max 15000)
        pf_base = min(basic_salary, 15000)
        pf = round(pf_base * 0.12, 2)
        
        # ESIC calculation (0.75% of gross if salary <= 22500)
        esic = 0
        if employee.salary <= 21100:
            esic = round(gross_salary * 0.0075, 2)
        
        # HRA (50% of basic)
        hra = round(basic_salary * 0.5, 2)
        
        # Medical allowance (50% of HRA)
        medical_allowance = round(hra * 0.5, 2)
        
        # Conveyance allowance (50% of HRA)
        conveyance_allowance = round(hra * 0.5, 2)
        
        # Calculate overtime payment if eligible
        overtime_payment = 0
        if employee.is_getting_ot:
            overtime_hours = attendance_data.get('total_overtime_hours', 0)
            overtime_hours = float(overtime_hours)  # or int(), if appropriate
            if overtime_hours > 0:
                per_hour_rate = float(employee.salary) / (total_days * float(working_hours))

                overtime_payment = round(overtime_hours * per_hour_rate, 2)
        
        # Calculate OD payment
        od_payment = 0
        od_days = int(float(attendance_data.get('extra_days', {}).get('od_days', 0)))
        od_hours = float(attendance_data.get('extra_days', {}).get('od_hours', 0))

        if od_days > 0 or od_hours > 0:
            per_day_rate = float(employee.salary) / total_days
            per_hour_rate = float(per_day_rate) / float(working_hours)

            
            od_payment = round((od_days * per_day_rate) + (od_hours * per_hour_rate), 2)
        
        # Calculate incentive (overtime + OD)
        incentive = round(overtime_payment + od_payment, 2)
        
        # Calculate total salary
        total_salary = round(gross_salary + incentive - pf - esic, 2)
        
        return {
            "gross_salary": gross_salary,
            "basic_salary": basic_salary,
            "hra": hra,
            "medical_allowance": medical_allowance,
            "conveyance_allowance": conveyance_allowance,
            "pf": pf,
            "esic": esic,
            "incentive": incentive,
            "overtime_payment": overtime_payment,
            "od_payment": od_payment,
            "total_salary": total_salary,
            "cl_used": cl_used,  # Add CL used to the response
            "cl_remaining": available_cl - cl_used  # Add remaining CL to the response
        }