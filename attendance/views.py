import requests
# from datetime import datetime, timedelta, time
# from django.db.models import Q
from rest_framework.views import APIView
from datetime import date
# from rest_framework.response import Response
# from rest_framework import status
# from django.utils import timezone
# from dateutil import rrule
# from decimal import Decimal
from .models import Employee,Holiday,ShiftAssignment,SundayReplacement,GatePass,ODSlip,ManualPunch
# from django.db.models.functions import Cast
# from django.db.models import DateTimeField
# from django.db import models
# from .models import ProcessedAttendance
# from datetime import date
from django.core.serializers.json import DjangoJSONEncoder
import json
# from django.utils import timezone
# from datetime import timezone as datetime_timezone  # Python's built-in timezone
# from django.utils import timezone as django_timezone  # Django's timezone utilities
# import pytz  # Required for India timezone
# from django.utils.timezone import localtime
# ist = pytz.timezone('Asia/Kolkata')

# class ProcessAttendanceAPI(APIView):
#     def post(self, request):
#         # Step 1: Get input parameters
#         month = request.data.get('month')
#         year = request.data.get('year')
#         save_data = request.data.get('save', False)
        
#         if not month or not year:
#             return Response(
#                 {"error": "Month and year are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         try:
#             month = int(month)
#             year = int(year)
#             if month < 1 or month > 12:
#                 raise ValueError
#         except ValueError:
#             return Response(
#                 {"error": "Invalid month or year"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Step 2: Get all employees
#         employees = Employee.objects.all()
        
#         # Step 3: Get date range for processing
#         start_date = datetime(year, month, 1).date()
#         if month == 12:
#             end_date = datetime(year+1, 1, 1).date()
#         else:
#             end_date = datetime(year, month+1, 1).date()
        
#         # Step 4: Fetch all relevant data in bulk for performance
#         gate_passes = GatePass.objects.filter(
#             employee__in=employees,
#             date__gte=start_date,
#             date__lt=end_date
#         ).select_related('employee')
        
#         shift_assignments = ShiftAssignment.objects.filter(
#             employee__in=employees,
#             start_date__lte=end_date,
#             end_date__gte=start_date
#         ).select_related('employee')

        
        
#         od_slips = ODSlip.objects.filter(
#             employee__in=employees,
#             od_date__gte=start_date,
#             od_date__lt=end_date
#         ).select_related('employee')
        
#         sunday_replacements = SundayReplacement.objects.filter(
#             Q(department__isnull=True) | Q(department__in=[emp.employee_department for emp in employees]),
#             sunday_date__gte=start_date,
#             sunday_date__lt=end_date
#         )
        
#         holidays = Holiday.objects.filter(
#             Q(department__isnull=True) | Q(department__in=[emp.employee_department for emp in employees]),
#             holiday_date__gte=start_date,
#             holiday_date__lt=end_date
#         )
#         offset = timedelta(hours=5, minutes=30)

#         # Replace the manual punch filtering with this:
#         manual_punches = ManualPunch.objects.filter(
#             employee__in=employees
#         ).filter(
#             Q(punch_in_time__date__gte=start_date, punch_in_time__date__lt=end_date + timedelta(days=1)) |
#             Q(punch_out_time__date__gte=start_date, punch_out_time__date__lt=end_date + timedelta(days=1))
#         ).select_related('employee')

#         # Apply +5:30 manually
#         for punch in manual_punches:
#             punch.punch_in_time = punch.punch_in_time + offset if punch.punch_in_time else None
#             punch.punch_out_time = punch.punch_out_time + offset if punch.punch_out_time else None
        
#         # Step 5: Fetch punch logs from all machines
#         punch_logs = self.fetch_punch_logs(start_date, end_date)
        
#         # Step 6: Process attendance for each employee
#         results = []
#         for employee in employees:
#             employee_data = self.process_employee_attendance(
#                 employee,
#                 start_date,
#                 end_date,
#                 gate_passes,
#                 shift_assignments,
#                 od_slips,
#                 sunday_replacements,
#                 holidays,
#                 manual_punches,
#                 punch_logs
#             )
#             results.append(employee_data)
#         # NEW: Save the data if requested
#         if save_data:
#             self.save_processed_data(results, month, year)
        
#         return Response(results, status=status.HTTP_200_OK)
    
#     def save_processed_data(self, results, month, year):
#         saved_records = []
#         for employee_data in results:
#             try:
#                 employee = Employee.objects.get(employee_id=employee_data['employee_id'])
                
#                 # Create or update processed attendance record
#                 record, created = ProcessedAttendance.objects.update_or_create(
#                     employee=employee,
#                     month=month,
#                     year=year,
#                     defaults={
#                         'attendance_data': json.loads(json.dumps(employee_data, cls=DjangoJSONEncoder))
#                     }
#                 )
#                 saved_records.append(record.id)
#             except Employee.DoesNotExist:
#                 continue
#             except Exception as e:
#                 print(f"Error saving attendance for employee {employee_data['employee_id']}: {str(e)}")
#                 continue
        
#         return saved_records
    
#     def fetch_punch_logs(self, start_date, end_date):
#         # List of all biometric machines
#         machines = [
#             {'serial': 'CRJP232260279', 'username': 'Api', 'password': 'Api@123#$'},
#             {'serial': 'CRJP224060053', 'username': 'Api', 'password': 'Api@123#$'},
#             # Add other machines here
#         ]
        
#         all_logs = []
        
#         # Adjust date range to include next day for night shift employees
#         extended_end_date = end_date + timedelta(days=1)
        
#         for machine in machines:
#             try:
#                 # Prepare SOAP request
#                 url = "http://ampletrail.com/ssbforge/iclock/WebAPIService.asmx?op=GetTransactionsLog"
#                 headers = {
#                     'Content-Type': 'text/xml; charset=utf-8',
#                     'SOAPAction': 'http://tempuri.org/GetTransactionsLog',
#                     'API-Key': '11'
#                 }
                
#                 # Format dates for SOAP request
#                 from_datetime = start_date.strftime('%Y-%m-%dT%H:%M:%S')
#                 to_datetime = extended_end_date.strftime('%Y-%m-%dT%H:%M:%S')
                
#                 xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
# <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#   <soap:Body>
#     <GetTransactionsLog xmlns="http://tempuri.org/">
#       <FromDateTime>{from_datetime}</FromDateTime>
#       <ToDateTime>{to_datetime}</ToDateTime>
#       <SerialNumber>{machine['serial']}</SerialNumber>
#       <UserName>{machine['username']}</UserName>
#       <UserPassword>{machine['password']}</UserPassword>
#       <strDataList></strDataList>
#     </GetTransactionsLog>
#   </soap:Body>
# </soap:Envelope>"""
                
#                 # Make the request
#                 response = requests.post(url, headers=headers, data=xml_body)
#                 response.raise_for_status()
                
#                 # Parse the response (simplified - in real implementation use proper XML parsing)
#                 logs = self.parse_punch_logs_response(response.text)
#                 all_logs.extend(logs)
                
#             except Exception as e:
#                 # Log error but continue with other machines
#                 print(f"Error fetching logs from machine {machine['serial']}: {str(e)}")
#                 continue
        
#         # Sort all logs by datetime
#         all_logs.sort(key=lambda x: x['datetime'])
#         return all_logs
    
#     def parse_punch_logs_response(self, xml_response):
#         logs = []
#         india_timezone = pytz.timezone('Asia/Kolkata')  # Define India Standard Time
#         lines = xml_response.split('\n')
#         for line in lines:
#             if '\t' in line:
#                 parts = line.strip().split('\t')
#                 if len(parts) >= 2:
#                     try:
#                         emp_id = parts[0]
#                         datetime_str = parts[1]
#                         dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
#                         # Make the datetime timezone-aware using datetime.timezone.utc
#                         dt = django_timezone.make_aware(dt, timezone=india_timezone)
#                         logs.append({
#                             'employee_id': emp_id,
#                             'datetime': dt
#                         })
#                     except ValueError:
#                         continue
#         return logs
    
    
#     def process_employee_attendance(self, employee, start_date, end_date, gate_passes, 
#                                   shift_assignments, od_slips, sunday_replacements, 
#                                   holidays, manual_punches, punch_logs):
#         # Initialize result structure
#         result = {
#             'employee_id': employee.employee_id,
#             'employee_name': employee.employee_name,
#             'department': employee.employee_department,
#             'employee_type': employee.employee_type,
#             'shift_type': employee.shift_type,
#             'month': start_date.month,
#             'year': start_date.year,
#             'daily_attendance': [],
#             'total_days_in_month': 0,
#             'total_working_days': 0,
#             'total_present_days': 0,
#             'total_absent_days': 0,
#             'total_leave_days': 0,
#             'sundays_in_month': 0,  # Added this line for total Sundays in month
#             'gets_sundays_off': employee.is_getting_sunday,  # Added this line
#             'total_holiday_days': 0,
#             'extra_days': {  # New field for tracking OD and other special days
#                 'od_display': '',  # <-- changed to string
#                 'od_days': Decimal('0.0'),
#                 'od_hours': Decimal('0.0'),  # Added this line for total OD hours
#                 'gate_pass_deductions': Decimal('0.0'),
#                 'total': Decimal('0.0')
#             },
#             'total_working_hours': Decimal('0.0'),
#             'total_overtime_hours': Decimal('0.0'),
#             'od_slips': [] 
            
#         }

#         replaced_sundays = 0
#         regular_sundays = 0
#         replacement_holidays = 0

#         # Initialize counters
#         present_days = Decimal('0.0')
#         absent_days = Decimal('0.0')
#         half_days = Decimal('0.0')


#         def round_overtime(overtime_hours):
#             """
#             Round overtime according to:
#             - 0.0 if <= 15 minutes
#             - 0.5 if between 16-45 minutes
#             - 1.0 if >= 46 minutes
#             Cap at 4.0 hours
#             """
#             if overtime_hours <= 0:
#                 return Decimal('0.0')
            
#             total_minutes = overtime_hours * 60

#             if total_minutes <= 15:
#                 rounded = Decimal('0.0')
#             elif total_minutes <= 40:
#                 rounded = Decimal('0.5')
#             else:
#                 # Round up to the next full hour
#                 rounded = Decimal(str(math.ceil(total_minutes / 60)))

#             return min(rounded, Decimal('4.0'))
        
        

#         def adjust_manual_punch_time(punch_time, is_manual):
#             """Adjust manual punch time by subtracting 5:30 hours if it's a manual punch"""
#             if is_manual and punch_time:
#                 return punch_time - timedelta(hours=5, minutes=30)
#             return punch_time
                
#         # Get employee's punch logs
#         emp_logs = [log for log in punch_logs if log['employee_id'] == employee.employee_id]
#         # In your process_employee_attendance method, add debug logging:
#         # Get employee's manual punches
#         emp_manual_punches = [mp for mp in manual_punches if mp.employee_id == employee.id]
#         # First pass: Count special days before processing daily attendance
#         for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1)):
#             date = day.date()
            
#             # Check for Sunday replacements
#             if date.weekday() == 6:  # Sunday
#                 replacement = next((sr for sr in sunday_replacements 
#                                 if (sr.department is None or sr.department == employee.employee_department) 
#                                 and sr.sunday_date == date), None)
                
#                 if replacement:
#                     replaced_sundays += 1
#                     # Count the replacement date as a holiday
#                     replacement_holidays += 1
#                 elif employee.is_getting_sunday:
#                     regular_sundays += 1
        
#         # Process each day in the month
#         for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1)):
#             date = day.date()
            
#             # Initialize day record
#             day_record = {
#                 'date': date,
#                 'day_type': 'Working Day',
#                 'shift_type': employee.shift_type,
#                 'scheduled_in': employee.working_time_in,
#                 'scheduled_out': employee.working_time_out,
#                 'actual_in': None,
#                 'actual_out': None,
#                 'is_manual_in': False,
#                 'is_manual_out': False,
#                 'manual_reason': None,
#                 'status': 'Absent',
#                 'working_hours': Decimal('0.0'),
#                 'overtime_hours': Decimal('0.0'),
#                 'gate_pass': None,
#                 'is_holiday': False,
#                 'holiday_name': None,
#                 'is_sunday_replaced': False,
#                 'replacement_date': None,
#                 'is_od': False,
#                 'od_hours': Decimal('0.0'),
#                 'od_days': Decimal('0.0'),
#                 'remarks': '',
#                 'night_shift_valid': None,  # New field to track night shift validity
#                 'is_half_day': False,  # Add this new field
#                 'day_value': Decimal('0.0'),  # New field: 1.0, 0.5 or 0.0
#             }
            
#             # Check if this is a rotational shift and if there's an assignment
#             if employee.shift_type == 'ROT':
#                 assignment = next((sa for sa in shift_assignments 
#                                  if sa.employee_id == employee.id and 
#                                  sa.start_date <= date <= sa.end_date), None)
#                 if assignment:
#                     day_record['shift_type'] = assignment.shift_type
#                     day_record['scheduled_in'] = assignment.working_time_in
#                     day_record['scheduled_out'] = assignment.working_time_out
            
#             # Check if this is a holiday
#             dept_holidays = [h for h in holidays 
#                            if (h.department is None or h.department == employee.employee_department) 
#                            and h.holiday_date == date]
#             if dept_holidays:
#                 day_record['is_holiday'] = True
#                 day_record['holiday_name'] = dept_holidays[0].holiday_name
#                 day_record['day_type'] = 'Holiday'
#                 day_record['status'] = 'Holiday'
#                 result['total_holiday_days'] += 1
#                 result['daily_attendance'].append(day_record)
#                 continue
            
#             # Check if this is a Sunday
#             # In the process_employee_attendance method, replace the Sunday checking block with this:

#             # Check if this is a Sunday
#             if date.weekday() == 6:  # Sunday
#                 # Check for Sunday replacement first - this takes precedence
#                 replacement = next((sr for sr in sunday_replacements 
#                                 if (sr.department is None or sr.department == employee.employee_department) 
#                                 and sr.sunday_date == date), None)
                
#                 if replacement:
#                     day_record['is_sunday_replaced'] = True
#                     day_record['replacement_date'] = replacement.replacement_date
#                     day_record['day_type'] = 'Sunday Replacement'
#                     # For replaced Sundays, attendance is mandatory for all
#                     day_record['status'] = 'Working on Replacement Day'
#                 elif employee.is_getting_sunday:
#                     day_record['day_type'] = 'Sunday'
#                     # Check for OD slip first
#                     od_slip = next((od for od in od_slips 
#                                 if od.employee_id == employee.id and od.od_date == date), None)
#                     if od_slip:
#                         day_record['is_od'] = True
#                         day_record['od_hours'] = od_slip.extra_hours
#                         day_record['od_days'] = od_slip.extra_days
#                         day_record['status'] = 'On Duty (Sunday)'
#                         result['extra_days']['od_days'] += Decimal(str(od_slip.extra_days))
#                         result['extra_days']['od_hours'] += Decimal(str(od_slip.extra_hours))
                        
#                         # Build the od_display string
#                         od_display = []
#                         if od_slip.extra_days:
#                             od_display.append(f"{int(od_slip.extra_days)}d")
#                         if od_slip.extra_hours:
#                             od_display.append(f"{int(od_slip.extra_hours)}h")
#                         day_record['remarks'] = f"OD - {' '.join(od_display)}"
                        
#                         if od_display:
#                             if result['extra_days']['od_display']:
#                                 result['extra_days']['od_display'] += " + " + ' '.join(od_display)
#                             else:
#                                 result['extra_days']['od_display'] = ' '.join(od_display)
                        
#                         # Skip punch processing for Sundays with OD
#                         result['daily_attendance'].append(day_record)
#                         continue
#                     else:
#                         day_record['status'] = 'Sunday'
#                         result['daily_attendance'].append(day_record)
#                         continue
#                 else:
#                     day_record['day_type'] = 'Sunday'

#             # Then later in the code where you process punches, add this condition at the start:
#             if day_record['status'] == 'On Duty (Sunday)':
#                 # We already processed this day, just continue
#                 continue
                        
#             # Check for OD slip
#             od_slip = next((od for od in od_slips 
#                           if od.employee_id == employee.id and od.od_date == date), None)
#             if od_slip:
#                 day_record['is_od'] = True
#                 day_record['od_hours'] = od_slip.extra_hours
#                 day_record['od_days'] = od_slip.extra_days
#                 day_record['status'] = 'On Duty'
#                 result['extra_days']['od_days'] += Decimal(str(od_slip.extra_days))
#                 result['extra_days']['od_hours'] += Decimal(str(od_slip.extra_hours))  # Add OD hour
#                 result['od_slips'].append({
#                     'date': od_slip.od_date,
#                     'hours': od_slip.extra_hours,
#                     'days': od_slip.extra_days,
#                     'reason': od_slip.reason,
#                     'approved_by': od_slip.approved_by
#                 })

#                 # Build the od_display string
#                 od_display = []
#                 if od_slip.extra_days:
#                     od_display.append(f"{int(od_slip.extra_days)}d")
#                 if od_slip.extra_hours:
#                     od_display.append(f"{int(od_slip.extra_hours)}h")
#                 day_record['remarks'] = f"OD - {' '.join(od_display)}"
                
#                 if od_display:
#                     if result['extra_days']['od_display']:
#                         # Append to existing if already present
#                         result['extra_days']['od_display'] += " + " + ' '.join(od_display)
#                     else:
#                         result['extra_days']['od_display'] = ' '.join(od_display)

              
#                 total_od_days = int(result['extra_days']['od_days'])
#                 total_od_hours = int(result['extra_days']['od_hours'])
#                 # Convert hours and days to a combined string like "1d 5h"
#                 od_display = []
#                 if total_od_days > 0:
#                     od_display.append(f"{total_od_days}d")
#                 if total_od_hours > 0:
#                     od_display.append(f"{total_od_hours}h")
                
#                 result['extra_days']['od_display'] = ' '.join(od_display) if od_display else ''
                

            
#             # Check for gate pass
#             gate_pass = next((gp for gp in gate_passes 
#                     if gp.employee_id == employee.id and gp.date == date), None)
#             if gate_pass:
#                 day_record['gate_pass'] = {
#                     'date': gate_pass.date,
#                     'out_time': gate_pass.out_time,
#                     'approved_by': gate_pass.approved_by,
#                     'action_taken': gate_pass.action_taken,
#                     'reason': gate_pass.reason
#                 }
                
#                 if gate_pass.action_taken == 'FD':
#                     day_record['status'] = 'Present (Full Day Gate Pass)'
#                     result['total_present_days'] += Decimal('1.0')  # <-- Add this line
#                 elif gate_pass.action_taken == 'HD':
#                     day_record['status'] = 'Half Day (Gate Pass)'
#                     day_record['working_hours'] = employee.working_hours / 2
#                     day_record['day_value'] = Decimal('0.5')
#                     present_days -= Decimal('0.5')
#                     half_days += Decimal('0.5')
#                 elif gate_pass.action_taken == 'FD_CUT':
#                     day_record['status'] = 'Absent (Full Day Cut Gate Pass)'
#                     result['extra_days']['gate_pass_deductions'] += Decimal('1.0')
#                     day_record['remarks'] = f'Gate Pass - Full Day Cut (-1 day) - {gate_pass.reason}'
#                 elif gate_pass.action_taken == 'HD_CUT':
#                     day_record['status'] = 'Half Day (Gate Pass Cut)'
#                     result['extra_days']['gate_pass_deductions'] += Decimal('0.5')
#                     day_record['remarks'] = f'Gate Pass - Half Day Cut (-0.5 day) - {gate_pass.reason}'
#                     day_record['working_hours'] = employee.working_hours / 2
#                     # Change present days count to 0.5 for half day cuts
#                     result['total_present_days'] += Decimal('0.5')
            
#             # Get all punches for this day
#             day_start = django_timezone.make_aware(datetime.combine(date, time.min))
#             day_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time.min))
            
#             # For night shift, include next day's morning punches
#             if day_record['shift_type'] == 'NIGHT':
#                 day_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time(23, 59, 59)))
            
#             day_punches = []
#             for log in emp_logs:
#                 log_time = log['datetime']
#                 # Ensure both datetimes are timezone-aware for comparison
#                 if django_timezone.is_aware(day_start) and not django_timezone.is_aware(log_time):
#                     log_time = django_timezone.make_aware(log_time)
#                 elif not django_timezone.is_aware(day_start) and django_timezone.is_aware(log_time):
#                     day_start = django_timezone.make_aware(day_start)
#                     day_end = django_timezone.make_aware(day_end)
                
#                 if day_start <= log_time < day_end:
#                     day_punches.append(log)
            
#             # Add manual punches
#             manual_in = next((
#                 mp for mp in emp_manual_punches 
#                 if mp.punch_in_time and (
#                     (date == mp.punch_in_time.date()) or  # Normal case
#                     (
#                         day_record['shift_type'] == 'NIGHT' and (
#                             (mp.punch_in_time.date() == date and mp.punch_in_time.time() >= time(16, 0)) or  # Evening punch
#                             (mp.punch_in_time.date() == date + timedelta(days=1) and mp.punch_in_time.time() < time(12, 0))  # Morning punch
#                         )
#                     )
#                 )
#             ), None)


#             if manual_in:
#     # Ensure the manual punch time is timezone-aware
#                 punch_in_time = django_timezone.make_aware(manual_in.punch_in_time) if not django_timezone.is_aware(manual_in.punch_in_time) else manual_in.punch_in_time
#                 day_punches.append({
#                     'employee_id': employee.employee_id,
#                     'datetime': punch_in_time,
#                     'is_manual': True
#                 })
#                 day_record['is_manual_in'] = True
#                 day_record['manual_reason'] = manual_in.reason

            
#             manual_out = next((
#                 mp for mp in emp_manual_punches 
#                 if mp.punch_out_time and (
#                     (date == mp.punch_out_time.date()) or  # Normal case
#                     (
#                         day_record['shift_type'] == 'NIGHT' and (
#                             (mp.punch_out_time.date() == date and mp.punch_out_time.time() >= time(16, 0)) or  # Evening punch
#                             (mp.punch_out_time.date() == date + timedelta(days=1) and mp.punch_out_time.time() < time(12, 0))  # Morning punch
#                         )
#                     )
#                 )
#             ), None)


#             if manual_out:
#                 # Ensure the manual punch time is timezone-aware
#                 punch_out_time = django_timezone.make_aware(manual_out.punch_out_time) if not django_timezone.is_aware(manual_out.punch_out_time) else manual_out.punch_out_time
#                 day_punches.append({
#                     'employee_id': employee.employee_id,
#                     'datetime': punch_out_time,
#                     'is_manual': True
#                 })
#                 day_record['is_manual_out'] = True
#                 day_record['manual_reason'] = manual_out.reason
                        
#             # Sort punches by time
#             day_punches.sort(key=lambda x: x['datetime'])
            
#             # Process punches based on shift type
#             if day_record['shift_type'] in ['DAY', 'ROT']:
#                 # For day shift, first punch is IN, last is OUT
#                 if len(day_punches) >= 2:
#                     day_record['actual_in'] = day_punches[0]['datetime'].time()
#                     day_record['actual_out'] = day_punches[-1]['datetime'].time()
#                     day_record['status'] = 'Present'
                    
#                     # Calculate working hours
#                     in_dt = day_punches[0]['datetime']
#                     out_dt = day_punches[-1]['datetime']
#                     worked_hours = (out_dt - in_dt).total_seconds() / 3600
#                     day_record['working_hours'] = Decimal(str(round(worked_hours, 2)))

#                     # NEW: Check for early departure (before 4 PM for day shift)
#                     if out_dt.time() < time(16, 0) and not gate_pass:
#                         day_record['status'] = 'Half Day (Early Departure)'
#                         day_record['working_hours'] = Decimal(str(round(worked_hours/2, 2)))
#                         day_record['remarks'] = 'Left before 4 PM without gate pass'
#                         # Count as half day
#                         result['total_present_days'] += Decimal('0.5')
#                     else:
#                         result['total_present_days'] += Decimal('1.0')

                    
                    
#                     # Calculate overtime if eligible
#                     if employee.is_getting_ot and not day_record['is_od']:
#                         scheduled_out_dt = django_timezone.make_aware(datetime.combine(date, day_record['scheduled_out']))
#                         if out_dt.tzinfo is None:
#                             out_dt = timezone.make_aware(out_dt)  # Only make it aware if it is naive
#                         if day_record['is_manual_out']:
#                             out_dt = adjust_manual_punch_time(out_dt, True)
#                         if scheduled_out_dt.tzinfo is None:
#                             scheduled_out_dt = timezone.make_aware(scheduled_out_dt)  # Same for scheduled_out_dt
#                         if out_dt > scheduled_out_dt:
#                             overtime = (out_dt - scheduled_out_dt).total_seconds() / 3600
#                             rounded_overtime = round_overtime(overtime) - Decimal('0.5')
#                             if employee.employee_id == "SSB022":
#                                 print(
#                                     f"Date: {date} | "
#                                     f"Scheduled Out: {scheduled_out_dt.time()} | "
#                                     f"Actual Out: {out_dt.time()} | "
#                                     f"Raw OT Hours: {overtime:.2f} | "
#                                     f"Rounded OT Before Adjustment: {round_overtime(overtime):.2f} | "
#                                     f"Final OT: {rounded_overtime:.2f}"
#                                 )
#                             day_record['overtime_hours'] = rounded_overtime
#                             result['total_overtime_hours'] += rounded_overtime
                    
#                     # NEW: Handle single punch case
#                 elif len(day_punches) == 1 and not gate_pass:
#                     punch_time = day_punches[0]['datetime'].time()
#                     day_record['actual_in'] = punch_time
#                     day_record['status'] = 'Half Day (Single Punch)'
#                     day_record['remarks'] = 'Only one punch recorded without gate pass'
#                     # Count as half day
#                     result['total_present_days'] += Decimal('0.5')
#                     # Estimate working hours as half day
#                     day_record['working_hours'] = employee.working_hours / 2
            
#             elif day_record['shift_type'] == 'NIGHT':
#                 # For night shift, we need to look at punches from current evening to next morning
#                 night_start = django_timezone.make_aware(datetime.combine(date, time(16, 0)))  # 4 PM
#                 night_end = django_timezone.make_aware(datetime.combine(date + timedelta(days=1), time(12, 0))) 
                
#                 # Get all punches in this extended window
#                 night_punches = [log for log in emp_logs if night_start <= log['datetime'] < night_end]
#                 if manual_in:
#                     night_punches.append({
#                         'employee_id': employee.employee_id,
#                         'datetime': manual_in.punch_in_time,
#                         'is_manual': True
#                     })
#                 if manual_out:
#                     night_punches.append({
#                         'employee_id': employee.employee_id,
#                         'datetime': manual_out.punch_out_time,
#                         'is_manual': True
#                     })
                
#                 if len(night_punches) >= 2:
#                     # Sort by time
#                     night_punches.sort(key=lambda x: x['datetime'])
                    
#                     # First punch is IN, last is OUT
#                     in_punch = night_punches[0]['datetime']
#                     out_punch = night_punches[-1]['datetime']
                    
#                     # Calculate if this is a valid night shift
#                     is_valid_night_shift = (
#                         in_punch.time() >= time(16, 0) and  # 4 PM or later
#                         out_punch.time() <= time(12, 0) and  # Noon or earlier
#                         (out_punch - in_punch).total_seconds() >= 8 * 3600  # At least 8 hours
#                     )
                    
#                     day_record['night_shift_valid'] = is_valid_night_shift
                    
#                     if is_valid_night_shift:
#                         day_record['actual_in'] = in_punch.time()
#                         day_record['actual_out'] = out_punch.time()
#                         day_record['status'] = 'Present'
                        
#                         # Calculate working hours
#                         worked_hours = (out_punch - in_punch).total_seconds() / 3600
#                         day_record['working_hours'] = Decimal(str(round(worked_hours, 2)))

#                          # NEW: Check for early departure (before 4 AM for night shift)
#                         if out_punch.time() < time(4, 0) and not gate_pass:
#                             day_record['status'] = 'Half Day (Early Departure)'
#                             day_record['working_hours'] = Decimal(str(round(worked_hours/2, 2)))
#                             day_record['remarks'] = 'Left before 4 AM without gate pass'
#                             # Count as half day
#                             result['total_present_days'] += Decimal('0.5')
#                         else:
#                             result['total_present_days'] += Decimal('1.0')
                        
#                         # Calculate overtime if eligible
#                         if employee.is_getting_ot and not day_record['is_od']:
#                             scheduled_out_dt = django_timezone.make_aware(datetime.combine(
#                                 date + timedelta(days=1),
#                                 day_record['scheduled_out']
#                             ))
#                             out_punch = night_punches[-1]['datetime']
#                             if day_record['is_manual_out']:
#                                 out_punch = adjust_manual_punch_time(out_punch, True)
#                             # Ensure out_punch is timezone-aware
#                             if not django_timezone.is_aware(out_punch):
#                                 out_punch = django_timezone.make_aware(out_punch)
#                             if out_punch > scheduled_out_dt:
#                                 overtime = (out_punch - scheduled_out_dt).total_seconds() / 3600
#                                 rounded_overtime = round_overtime(overtime)
#                                 day_record['overtime_hours'] = rounded_overtime
#                                 result['total_overtime_hours'] += rounded_overtime
#                     else:
#                         day_record['remarks'] = 'Night shift validation failed - check timings'
#                 else:
#                     # NEW: Handle single punch case for night shift
#                     if len(night_punches) == 1 and not gate_pass:
#                         punch_time = night_punches[0]['datetime'].time()
#                         day_record['actual_in'] = punch_time
#                         day_record['status'] = 'Half Day (Single Punch)'
#                         day_record['remarks'] = 'Only one punch recorded without gate pass'
#                         # Count as half day
#                         result['total_present_days'] += Decimal('0.5')
#                         # Estimate working hours as half day
#                         day_record['working_hours'] = employee.working_hours / 2
#                     else:
#                         day_record['remarks'] = f'Insufficient punches found ({len(night_punches)}) for night shift'
            
#              # Determine day value based on status - MODIFIED SECTION
#             if day_record['status'] == 'Present':
#                 day_record['day_value'] = Decimal('1.0')
#                 present_days += Decimal('1.0')
#             elif day_record['status'].startswith('Half Day'):
#                 day_record['day_value'] = Decimal('0.5')
#                 present_days += Decimal('0.5')
#                 half_days += Decimal('0.5')
#             elif day_record['status'] == 'Absent':
#                 day_record['day_value'] = Decimal('0.0')
#                 absent_days += Decimal('1.0')
#             elif day_record['status'] == 'Holiday':
#                 day_record['day_value'] = Decimal('0.0')
#             elif day_record['status'] == 'Sunday' and employee.is_getting_sunday:
#                 day_record['day_value'] = Decimal('0.0')


#             # ... (rest of day processing)

#             result['daily_attendance'].append(day_record)

#         # Calculate total working days - MODIFIED CALCULATION
#         total_days_in_month = (end_date - start_date).days
#         regular_sundays = sum(
#             1 for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1))
#             if day.date().weekday() == 6 and  # Sunday
#             not any(sr for sr in sunday_replacements 
#                 if (sr.department is None or sr.department == employee.employee_department) 
#                 and sr.sunday_date == day.date())
#         )
#          # Count half days as 0.5 in working days
#         half_day_count = sum(1 for day in result['daily_attendance'] if day.get('is_half_day', False))

#         result['total_days_in_month'] = (
#            total_days_in_month
#         )
#          # Calculate total extra days at the end
#         result['extra_days']['total'] = (
#             result['extra_days']['od_days'] -
#             result['extra_days']['gate_pass_deductions']
#         )
#         sundays_in_month = sum(
#             1 for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1))
#             if day.date().weekday() == 6  # Sunday
#         )
#         result['sundays_in_month'] = sundays_in_month
       

        
#         # Calculate total working days (excluding holidays, Sundays unless replaced)
#         result['total_working_days'] = (
#             total_days_in_month - 
#             regular_sundays - 
#             result['total_holiday_days'] +
#             replaced_sundays
#         )
#         result['total_present_days'] = present_days
#         result['total_absent_days'] = absent_days+half_days
#         result['total_half_days'] = half_days  # New field for tracking
        
        
#         return result
    

import pytz
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.utils import timezone as django_timezone
from dateutil import rrule

class ProcessAttendanceAPI(APIView):
    # Define timezone constants
    IST = pytz.timezone('Asia/Kolkata')
    UTC = pytz.UTC
    
    def post(self, request):
        # Step 1: Validate input parameters
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
        
        # Step 2: Get date range for processing
        start_date, end_date = self.get_date_range(year, month)
        
        # Step 3: Fetch all relevant data in bulk for performance
        employees = Employee.objects.all()
        data = self.fetch_attendance_data(employees, start_date, end_date)
        
        # Step 4: Process attendance for each employee
        results = []
        for employee in employees:
            employee_data = self.process_employee_attendance(
                employee,
                start_date,
                end_date,
                **data
            )
            results.append(employee_data)
        
        # Step 5: Save data if requested
        if save_data:
            self.save_processed_data(results, month, year)
        
        return Response(results, status=status.HTTP_200_OK)
    
    def get_date_range(self, year, month):
        """Get start and end dates for the given month/year"""
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year+1, 1, 1).date()
        else:
            end_date = datetime(year, month+1, 1).date()
        return start_date, end_date
    
    def fetch_attendance_data(self, employees, start_date, end_date):
        """Fetch all required data in bulk for performance"""
        # Convert dates to timezone-aware datetimes for queries
        tz_start = django_timezone.make_aware(datetime.combine(start_date, time.min))
        tz_end = django_timezone.make_aware(datetime.combine(end_date, time.min))
        
        departments = [emp.employee_department for emp in employees]
        employee_ids = [emp.id for emp in employees]
        
        return {
            'gate_passes': GatePass.objects.filter(
                employee_id__in=employee_ids,
                date__gte=start_date,
                date__lt=end_date
            ).select_related('employee'),
            
            'shift_assignments': ShiftAssignment.objects.filter(
                employee_id__in=employee_ids,
                start_date__lte=end_date,
                end_date__gte=start_date
            ).select_related('employee'),
            
            'od_slips': ODSlip.objects.filter(
                employee_id__in=employee_ids,
                od_date__gte=start_date,
                od_date__lt=end_date
            ).select_related('employee'),
            
            'sunday_replacements': SundayReplacement.objects.filter(
                Q(department__isnull=True) | Q(department__in=departments),
                sunday_date__gte=start_date,
                sunday_date__lt=end_date
            ),
            
            'holidays': Holiday.objects.filter(
                Q(department__isnull=True) | Q(department__in=departments),
                holiday_date__gte=start_date,
                holiday_date__lt=end_date
            ),
            
            'manual_punches': ManualPunch.objects.filter(
                employee_id__in=employee_ids
            ).filter(
                Q(punch_in_time__gte=tz_start, punch_in_time__lt=tz_end) |
                Q(punch_out_time__gte=tz_start, punch_out_time__lt=tz_end)
            ).select_related('employee'),
            
            'punch_logs': self.fetch_punch_logs(start_date, end_date)
        }
    
    def fetch_punch_logs(self, start_date, end_date):
        """Fetch punch logs from all biometric machines with proper timezone handling"""
        machines = [
            {'serial': 'CRJP232260279', 'username': 'Api', 'password': 'Api@123#$'},
            {'serial': 'CRJP224060053', 'username': 'Api', 'password': 'Api@123#$'},
        ]
        
        all_logs = []
        extended_end_date = end_date + timedelta(days=1)
        
        for machine in machines:
            try:
                url = "http://ampletrail.com/ssbforge/iclock/WebAPIService.asmx?op=GetTransactionsLog"
                headers = {
                    'Content-Type': 'text/xml; charset=utf-8',
                    'SOAPAction': 'http://tempuri.org/GetTransactionsLog',
                    'API-Key': '11'
                }
                
                xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetTransactionsLog xmlns="http://tempuri.org/">
      <FromDateTime>{start_date.strftime('%Y-%m-%dT%H:%M:%S')}</FromDateTime>
      <ToDateTime>{extended_end_date.strftime('%Y-%m-%dT%H:%M:%S')}</ToDateTime>
      <SerialNumber>{machine['serial']}</SerialNumber>
      <UserName>{machine['username']}</UserName>
      <UserPassword>{machine['password']}</UserPassword>
      <strDataList></strDataList>
    </GetTransactionsLog>
  </soap:Body>
</soap:Envelope>"""
                
                response = requests.post(url, headers=headers, data=xml_body)
                response.raise_for_status()
                logs = self.parse_punch_logs_response(response.text)
                all_logs.extend(logs)
                
            except Exception as e:
                print(f"Error fetching logs from machine {machine['serial']}: {str(e)}")
                continue
        
        all_logs.sort(key=lambda x: x['datetime'])
        return all_logs
    
    def parse_punch_logs_response(self, xml_response):
        """Parse punch logs response with proper timezone handling"""
        logs = []
        lines = xml_response.split('\n')
        
        for line in lines:
            if '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        emp_id = parts[0]
                        datetime_str = parts[1]
                        
                        # Parse naive datetime and make it timezone-aware (IST)
                        naive_dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                        aware_dt = self.IST.localize(naive_dt)
                        
                        # Convert to UTC for consistent storage
                        utc_dt = aware_dt.astimezone(self.UTC)
                        
                        logs.append({
                            'employee_id': emp_id,
                            'datetime': utc_dt,
                            'original_time': aware_dt  # Keep original IST time for display
                        })
                    except ValueError:
                        continue
        return logs
    
    def process_employee_attendance(self, employee, start_date, end_date, 
                                  gate_passes, shift_assignments, od_slips, 
                                  sunday_replacements, holidays, manual_punches, punch_logs):
        """Process attendance for a single employee with proper timezone handling"""
        # Initialize result structure
        result = self.initialize_attendance_result(employee, start_date)
        
        # Filter employee-specific data
        emp_gate_passes = [gp for gp in gate_passes if gp.employee_id == employee.id]
        emp_od_slips = [od for od in od_slips if od.employee_id == employee.id]
        emp_manual_punches = [mp for mp in manual_punches if mp.employee_id == employee.id]
        emp_punch_logs = [log for log in punch_logs if log['employee_id'] == employee.employee_id]
        
        # Process each day in the month
        for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1)):
            date = day.date()
            day_record = self.initialize_day_record(employee, date)
            
            # Apply shift assignments if rotational
            self.apply_shift_assignments(day_record, employee, date, shift_assignments)
            
            # Check for holidays and Sundays
            if self.process_special_days(day_record, result, employee, date, 
                                        holidays, sunday_replacements, emp_od_slips):
                result['daily_attendance'].append(day_record)
                continue
            
            # Process OD slips
            self.process_od_slips(day_record, result, date, emp_od_slips)
            
            # Process gate passes
            self.process_gate_passes(day_record, result, date, emp_gate_passes, employee)
            
            # Process punches
            self.process_punches(day_record, result, employee, date, 
                               emp_punch_logs, emp_manual_punches)
            
            result['daily_attendance'].append(day_record)
        
        # Calculate summary statistics
        self.calculate_summary_statistics(result, start_date, end_date, 
                                        sunday_replacements, employee)
        
        return result
    
    def initialize_attendance_result(self, employee, start_date):
        """Initialize the result structure for an employee"""
        return {
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
            'total_present_days': Decimal('0.0'),
            'total_absent_days': Decimal('0.0'),
            'total_leave_days': 0,
            'sundays_in_month': 0,
            'gets_sundays_off': employee.is_getting_sunday,
            'total_holiday_days': 0,
            'extra_days': {
                'od_display': '',
                'od_days': Decimal('0.0'),
                'od_hours': Decimal('0.0'),
                'gate_pass_deductions': Decimal('0.0'),
                'total': Decimal('0.0')
            },
            'total_working_hours': Decimal('0.0'),
            'total_overtime_hours': Decimal('0.0'),
            'od_slips': [],
            'total_half_days': Decimal('0.0')
        }
    
    def initialize_day_record(self, employee, date):
        """Initialize a day record structure"""
        return {
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
            'night_shift_valid': None,
            'is_half_day': False,
            'day_value': Decimal('0.0'),
        }
    
    def apply_shift_assignments(self, day_record, employee, date, shift_assignments):
        """Apply shift assignments if employee is on rotational shift"""
        if employee.shift_type == 'ROT':
            assignment = next((sa for sa in shift_assignments 
                            if sa.employee_id == employee.id and 
                            sa.start_date <= date <= sa.end_date), None)
            if assignment:
                # if employee.employee_id == 'SSB015':
                #     print(f"[DEBUG] Shift assignment found for {employee.employee_id} on {date}:")
                #     print(f"[DEBUG] Overriding {employee.working_time_in}->{employee.working_time_out}")
                #     print(f"[DEBUG] With {assignment.working_time_in}->{assignment.working_time_out}")
                day_record['shift_type'] = assignment.shift_type
                day_record['scheduled_in'] = assignment.working_time_in
                day_record['scheduled_out'] = assignment.working_time_out
        else:
            # For non-rotational shifts, use employee defaults
            day_record['scheduled_in'] = employee.working_time_in
            day_record['scheduled_out'] = employee.working_time_out
            # if employee.employee_id == 'SSB015':
            #     print(f"[DEBUG] Using employee defaults for {employee.employee_id} on {date}:")
            #     print(f"[DEBUG] Scheduled times: {employee.working_time_in}->{employee.working_time_out}")
        
    def process_special_days(self, day_record, result, employee, date, 
                           holidays, sunday_replacements, emp_od_slips):
        """Process holidays and Sundays, returns True if day is special"""
        # Check for holidays
        dept_holidays = [h for h in holidays 
                        if (h.department is None or h.department == employee.employee_department) 
                        and h.holiday_date == date]
        if dept_holidays:
            day_record.update({
                'is_holiday': True,
                'holiday_name': dept_holidays[0].holiday_name,
                'day_type': 'Holiday',
                'status': 'Holiday'
            })
            result['total_holiday_days'] += 1
            return True
        
        # Check for Sundays
        if date.weekday() == 6:  # Sunday
            replacement = next((sr for sr in sunday_replacements 
                             if (sr.department is None or sr.department == employee.employee_department) 
                             and sr.sunday_date == date), None)
            
            if replacement:
                day_record.update({
                    'is_sunday_replaced': True,
                    'replacement_date': replacement.replacement_date,
                    'day_type': 'Sunday Replacement',
                    'status': 'Working on Replacement Day'
                })
            elif employee.is_getting_sunday:
                od_slip = next((od for od in emp_od_slips if od.od_date == date), None)
                if od_slip:
                    self.process_od_slip(day_record, result, od_slip, 'On Duty (Sunday)')
                else:
                    day_record.update({
                        'day_type': 'Sunday',
                        'status': 'Sunday'
                    })
                return True
            else:
                day_record['day_type'] = 'Working Day'
        
        return False
    
    def process_od_slips(self, day_record, result, date, emp_od_slips):
        """Process OD slips for the day"""
        od_slip = next((od for od in emp_od_slips if od.od_date == date), None)
        if od_slip:
            self.process_od_slip(day_record, result, od_slip, 'On Duty')
    
    def process_od_slip(self, day_record, result, od_slip, status_prefix):
        """Process a single OD slip"""
        day_record.update({
            'is_od': True,
            'od_hours': od_slip.extra_hours,
            'od_days': od_slip.extra_days,
            'status': status_prefix,
            'remarks': f"OD - {self.format_od_display(od_slip)}"
        })
        
        result['extra_days']['od_days'] += Decimal(str(od_slip.extra_days))
        result['extra_days']['od_hours'] += Decimal(str(od_slip.extra_hours))
        
        # Update the od_display in result
        od_display = []
        if od_slip.extra_days:
            od_display.append(f"{int(od_slip.extra_days)}d")
        if od_slip.extra_hours:
            od_display.append(f"{int(od_slip.extra_hours)}h")
        
        if od_display:
            if result['extra_days']['od_display']:
                result['extra_days']['od_display'] += " + " + ' '.join(od_display)
            else:
                result['extra_days']['od_display'] = ' '.join(od_display)
        
        result['od_slips'].append({
            'date': od_slip.od_date,
            'hours': od_slip.extra_hours,
            'days': od_slip.extra_days,
            'reason': od_slip.reason,
            'approved_by': od_slip.approved_by
        })
    
    def format_od_display(self, od_slip):
        """Format OD display string"""
        parts = []
        if od_slip.extra_days:
            parts.append(f"{int(od_slip.extra_days)}d")
        if od_slip.extra_hours:
            parts.append(f"{int(od_slip.extra_hours)}h")
        return ' '.join(parts) if parts else ''
    
    def process_gate_passes(self, day_record, result, date, emp_gate_passes, employee):
        """Process gate passes for the day"""
        gate_pass = next((gp for gp in emp_gate_passes if gp.date == date), None)
        if gate_pass:
            day_record['gate_pass'] = {
                'date': gate_pass.date,
                'out_time': gate_pass.out_time,
                'approved_by': gate_pass.approved_by,
                'action_taken': gate_pass.action_taken,
                'reason': gate_pass.reason
            }
            
            if gate_pass.action_taken == 'FD':
                day_record.update({
                    'status': 'Present (Full Day Gate Pass)',
                    'day_value': Decimal('1.0'),
                    'working_hours': employee.working_hours
                })
                
            elif gate_pass.action_taken == 'HD':
                day_record.update({
                    'status': 'Half Day (Gate Pass)',
                    'working_hours': employee.working_hours / 2,
                    'day_value': Decimal('0.5'),
                    'is_half_day': True
                })
                result['total_present_days'] -= Decimal('0.5')
                result['total_absent_days'] += Decimal('0.5')
                result['total_half_days'] += Decimal('0.5')
                
            elif gate_pass.action_taken == 'FD_CUT':
                day_record.update({
                    'status': 'Absent (Full Day Cut Gate Pass)',
                    'day_value': Decimal('0.0'),
                    'remarks': f'Gate Pass - Full Day Cut (-1 day) - {gate_pass.reason}'
                })
                result['extra_days']['gate_pass_deductions'] += Decimal('1.0')
                result['total_absent_days'] += Decimal('1.0')
                result['total_present_days'] -= Decimal('1.0')
                
            elif gate_pass.action_taken == 'HD_CUT':
                day_record.update({
                    'status': 'Half Day (Gate Pass Cut)',
                    'working_hours': employee.working_hours / 2,
                    'day_value': Decimal('0.5'),
                    'remarks': f'Gate Pass - Half Day Cut (-0.5 day) - {gate_pass.reason}',
                    'is_half_day': True
                })
                result['extra_days']['gate_pass_deductions'] += Decimal('0.5')
                result['total_present_days'] += Decimal('0.5')
                result['total_absent_days'] += Decimal('0.5')
                result['total_half_days'] += Decimal('0.5')
    
    def process_punches(self, day_record, result, employee, date, 
                  emp_punch_logs, emp_manual_punches):
        """Process punches for the day with proper timezone handling"""
        # Get timezone-aware datetime range for the day
        day_start, day_end = self.get_day_range(date, day_record['shift_type'])
        
        # Get all punches for the day (including manual)
        day_punches = self.get_day_punches(
            date, day_record['shift_type'], 
            emp_punch_logs, emp_manual_punches
        )
        
        # Store punches information regardless of OD status
        if day_punches:
            in_punch = day_punches[0]['datetime'].astimezone(self.IST)
            day_record['actual_in'] = in_punch.time()
            day_record['is_manual_in'] = day_punches[0].get('is_manual', False)
            
            if len(day_punches) > 1:
                out_punch = day_punches[-1]['datetime'].astimezone(self.IST)
                day_record['actual_out'] = out_punch.time()
                day_record['is_manual_out'] = day_punches[-1].get('is_manual', False)
        
        # If it's an OD day, but both in and out punches are available, mark as Present
        if day_record['status'] in ['On Duty', 'On Duty (Sunday)']:
            if 'actual_in' in day_record and 'actual_out' in day_record:
                day_record['status'] = 'Present'
            else:
                return

        
        # Process based on shift type
        if day_record['shift_type'] in ['DAY', 'ROT']:
            self.process_day_shift(day_record, result, employee, date, day_punches)
        elif day_record['shift_type'] == 'NIGHT':
            self.process_night_shift(day_record, result, employee, date, day_punches)
        
        # Update day value based on status
        self.update_day_value(day_record, result)
    
    def get_day_range(self, date, shift_type):
        """Get timezone-aware datetime range for the day based on shift type"""
        day_start = self.IST.localize(datetime.combine(date, time.min))
        day_end = self.IST.localize(datetime.combine(date + timedelta(days=1), time.min))
        
        if shift_type == 'NIGHT':
            # For night shift, extend the range to include the next day's punches
            day_end = self.IST.localize(datetime.combine(date + timedelta(days=2), time.min))
        
        # Convert to UTC for consistent comparison
        return day_start.astimezone(self.UTC), day_end.astimezone(self.UTC)
    
    def get_day_punches(self, date, shift_type, emp_punch_logs, emp_manual_punches):
        """Get all punches for the day including manual punches"""
        if shift_type == 'NIGHT':
            # For night shift, look from 4PM current day to 10AM next day
            day_start = self.IST.localize(datetime.combine(date, time(16, 0)))
            day_end = self.IST.localize(datetime.combine(date + timedelta(days=1), time(10, 0)))
        else:
            # For day/rotational shifts, look at the calendar day
            day_start = self.IST.localize(datetime.combine(date, time.min))
            day_end = self.IST.localize(datetime.combine(date + timedelta(days=1), time.min))
        
        # Convert to UTC for comparison
        day_start = day_start.astimezone(self.UTC)
        day_end = day_end.astimezone(self.UTC)

        # Get biometric punches
        day_punches = [
            log for log in emp_punch_logs 
            if day_start <= log['datetime'] < day_end
        ]

        # Add both manual in and out punches if present
        for mp in emp_manual_punches:
            if mp.punch_in_time:
                punch_time_in = mp.punch_in_time.astimezone(self.UTC)
                if day_start <= punch_time_in < day_end:
                    day_punches.append({
                        'employee_id': mp.employee.employee_id,
                        'datetime': punch_time_in,
                        'is_manual': True,
                        'is_in_punch': True,
                        'reason': mp.reason
                    })

            if mp.punch_out_time:
                punch_time_out = mp.punch_out_time.astimezone(self.UTC)
                if day_start <= punch_time_out < day_end:
                    day_punches.append({
                        'employee_id': mp.employee.employee_id,
                        'datetime': punch_time_out,
                        'is_manual': True,
                        'is_in_punch': False,
                        'reason': mp.reason
                    })

        # Sort punches by time
        day_punches.sort(key=lambda x: x['datetime'])
        return day_punches

    
    def process_day_shift(self, day_record, result, employee, date, day_punches):

        is_sunday_without_off = (date.weekday() == 6 and not employee.is_getting_sunday)
        """Process day shift punches"""
        if len(day_punches) >= 2:
            in_punch = day_punches[0]['datetime'].astimezone(self.IST)
            out_punch = day_punches[-1]['datetime'].astimezone(self.IST)
            
            day_record.update({
                'actual_in': in_punch.time(),
                'actual_out': out_punch.time(),
                'status': 'Present',
                'is_manual_in': day_punches[0].get('is_manual', False),
                'is_manual_out': day_punches[-1].get('is_manual', False),
                'manual_reason': day_punches[0].get('reason') or day_punches[-1].get('reason')
            })
            
            # Calculate working hours
            worked_hours = (out_punch - in_punch).total_seconds() / 3600
            day_record['working_hours'] = Decimal(str(round(worked_hours, 2)))
            
            # Check for early departure
            if out_punch.time() < time(16, 0) and not day_record['gate_pass']:
                day_record.update({
                    'status': 'Half Day (Early Departure)',
                    'working_hours': Decimal(str(round(worked_hours/2, 2))),
                    'remarks': 'Left before 4 PM without gate pass',
                    'is_half_day': True
                })
                result['total_present_days'] += Decimal('0.5')
                result['total_half_days'] += Decimal('0.5')
            else:
                result['total_present_days'] += Decimal('1.0')
            
            # Calculate overtime if eligible
            if employee.is_getting_ot and not day_record['is_od']:
                scheduled_out = datetime.combine(date, day_record['scheduled_out'])
                scheduled_out_dt = self.IST.localize(scheduled_out).astimezone(self.UTC)
                
                if out_punch.astimezone(self.UTC) > scheduled_out_dt:
                    overtime = (out_punch.astimezone(self.UTC) - scheduled_out_dt).total_seconds() / 3600
                    rounded_overtime = self.round_overtime(overtime)
                    final_ot = max(Decimal('0.0'), rounded_overtime - Decimal('0.5'))
                    # Ensure overtime is not negative
                    day_record['overtime_hours'] = final_ot
                    result['total_overtime_hours'] += final_ot
                    # TARGET_EMPLOYEE_ID = 'SSB015'

                    # if employee.employee_id == TARGET_EMPLOYEE_ID:
                        

                    #     print(f"[DEBUG] EMP ID: {employee.employee_id} | DATE: {date}")
                    #     print(f"[DEBUG] In Time: {in_punch.time()} | Out Time: {out_punch.time()}")
                    #     print(f"[DEBUG] Scheduled Out: {day_record['scheduled_out']} | Actual Out: {out_punch.time()}")
                    #     print(f"[DEBUG] Raw OT: {(out_punch.astimezone(self.UTC) - scheduled_out_dt).total_seconds() / 3600:.2f}")
                    #     print(f"[DEBUG] Rounded OT: {rounded_overtime}")

                    

        
        elif len(day_punches) == 1 and not day_record['gate_pass']:
            punch_time = day_punches[0]['datetime'].astimezone(self.IST).time()
             # Special case: Sunday + single punch + doesn't get Sunday off
            if is_sunday_without_off:
                day_record.update({
                    'status': 'Absent',
                    'remarks': 'Single punch on Sunday (no Sunday off)',
                    'working_hours': Decimal('0.0'),
                    'day_value': Decimal('0.0')
                })
            else:
                day_record.update({
                    'actual_in': punch_time,
                    'status': 'Half Day (Single Punch)',
                    'remarks': 'Only one punch recorded without gate pass',
                    'working_hours': employee.working_hours / 2,
                    'is_half_day': True,
                    'is_manual_in': day_punches[0].get('is_manual', False),
                    'manual_reason': day_punches[0].get('reason')
                })
                result['total_present_days'] += Decimal('0.5')
                result['total_half_days'] += Decimal('0.5')
    
    def process_night_shift(self, day_record, result, employee, date, day_punches):
        """Process night shift punches with proper two-day span handling"""
        # For night shift, we need to look at punches from current day 4PM to next day 10AM
        current_day_start = self.IST.localize(datetime.combine(date, time(16, 0)))  # 4PM current day
        next_day_end = self.IST.localize(datetime.combine(date + timedelta(days=1), time(10, 0)))  # 10AM next day
        
        # Filter punches within the night shift window (4PM to 10AM next day)
        night_shift_punches = [
            punch for punch in day_punches
            if current_day_start <= punch['datetime'].astimezone(self.IST) <= next_day_end
        ]
        
        # Sort punches chronologically
        night_shift_punches.sort(key=lambda x: x['datetime'])
        
        # Need at least 2 punches (in and out) to consider present
        if len(night_shift_punches) >= 2:
            in_punch = night_shift_punches[0]['datetime'].astimezone(self.IST)
            out_punch = night_shift_punches[-1]['datetime'].astimezone(self.IST)
            
            # Validate night shift pattern:
            # 1. In punch should be after 4PM current day
            # 2. Out punch should be before 10AM next day
            # 3. Should have worked at least 6 hours
            is_valid = True
            remarks = []
            
            if in_punch.time() < time(16, 0):
                is_valid = False
                remarks.append("In punch before 4PM")
            
            if out_punch.time() > time(10, 0):
                is_valid = False
                remarks.append("Out punch after 10AM")
            
            duration_hours = (out_punch - in_punch).total_seconds() / 3600
            if duration_hours < 6:
                is_valid = False
                remarks.append(f"Duration less than 6 hours ({duration_hours:.1f}h)")
            
            day_record['night_shift_valid'] = is_valid
            
            if is_valid:
                day_record.update({
                    'actual_in': in_punch.time(),
                    'actual_out': out_punch.time(),
                    'status': 'Present',
                    'is_manual_in': night_shift_punches[0].get('is_manual', False),
                    'is_manual_out': night_shift_punches[-1].get('is_manual', False),
                    'manual_reason': night_shift_punches[0].get('reason') or night_shift_punches[-1].get('reason'),
                    'working_hours': Decimal(str(round(duration_hours, 2)))
                })
                
                # Check for full shift completion (8+ hours)
                if duration_hours >= 8 or day_record.get('gate_pass'):
                    result['total_present_days'] += Decimal('1.0')
                else:
                    day_record.update({
                        'status': 'Half Day (Short Duration)',
                        'is_half_day': True,
                        'remarks': 'Worked less than 8 hours without gate pass'
                    })
                    result['total_present_days'] += Decimal('0.5')
                    result['total_half_days'] += Decimal('0.5')
                
                # Calculate overtime if eligible
                if employee.is_getting_ot and not day_record['is_od']:
                    scheduled_out = datetime.combine(date + timedelta(days=1), time(4, 0))  # Assuming 6AM end time
                    scheduled_out_dt = self.IST.localize(scheduled_out).astimezone(self.UTC)
                    
                    if out_punch.astimezone(self.UTC) > scheduled_out_dt:
                        overtime = (out_punch.astimezone(self.UTC) - scheduled_out_dt).total_seconds() / 3600
                        rounded_overtime = self.round_overtime(overtime)
                        day_record['overtime_hours'] = rounded_overtime
                        result['total_overtime_hours'] += rounded_overtime
                        TARGET_EMPLOYEE_ID = 'SSB015'

                        if employee.employee_id == TARGET_EMPLOYEE_ID:
                        

                            print(f"[DEBUG] EMP ID: {employee.employee_id} | DATE: {date}")
                            print(f"[DEBUG] In Time: {in_punch.time()} | Out Time: {out_punch.time()}")
                            print(f"[DEBUG] Scheduled Out: {day_record['scheduled_out']} | Actual Out: {out_punch.time()}")
                            print(f"[DEBUG] Raw OT: {(out_punch.astimezone(self.UTC) - scheduled_out_dt).total_seconds() / 3600:.2f}")
                            print(f"[DEBUG] Rounded OT: {rounded_overtime}")
            else:
                day_record.update({
                    'status': 'Absent',
                    'remarks': 'Invalid night shift: ' + ', '.join(remarks)
                })
                result['total_absent_days'] += Decimal('1.0')
        
        elif len(night_shift_punches) == 1 and not day_record['gate_pass']:
            # Single punch case
            punch_time = night_shift_punches[0]['datetime'].astimezone(self.IST).time()
            day_record.update({
                'actual_in' if punch_time >= time(16, 0) else 'actual_out': punch_time,
                'status': 'Half Day (Single Punch)',
                'remarks': 'Only one punch recorded without gate pass',
                'working_hours': employee.working_hours / 2,
                'is_half_day': True,
                'is_manual_in': night_shift_punches[0].get('is_manual', False),
                'manual_reason': night_shift_punches[0].get('reason')
            })
            result['total_present_days'] += Decimal('0.5')
            result['total_half_days'] += Decimal('0.5')
        
        elif not day_record['gate_pass'] and day_record['status'] not in ['On Duty', 'On Duty (Sunday)']:
            day_record.update({
                'status': 'Absent',
                'remarks': 'No punches recorded for night shift'
            })
            result['total_absent_days'] += Decimal('1.0')
    
    def round_overtime(self, overtime_hours):
        """Round overtime according to company policy"""
        if overtime_hours <= 0:
            return Decimal('0.0')

        whole_hours = int(overtime_hours)  # e.g., 3
        remaining_minutes = (overtime_hours - whole_hours) * 60  # e.g., 0.34 * 60 = 20.4

        if remaining_minutes <= 15:
            extra = Decimal('0.0')
        elif remaining_minutes <= 40:
            extra = Decimal('0.5')
        else:
            extra = Decimal('1.0')

        total_rounded = Decimal(whole_hours) + extra
        return min(total_rounded, Decimal('4.0'))

    
    def update_day_value(self, day_record, result):
        """Update day value based on status"""
        # Skip if this is a gate pass day (already handled in process_gate_passes)
        if day_record.get('gate_pass'):
            return
            
        if day_record['status'] == 'Present':
            day_record['day_value'] = Decimal('1.0')
        elif day_record['status'].startswith('Half Day'):
            day_record['day_value'] = Decimal('0.5')
            result['total_absent_days'] += Decimal('0.5')
            result['total_half_days'] += Decimal('0.5')
        elif day_record['status'] == 'Absent':
            day_record['day_value'] = Decimal('0.0')
            result['total_absent_days'] += Decimal('1.0')
            # Don't increment absent days here - we'll calculate it later
    
    def calculate_summary_statistics(self, result, start_date, end_date, 
                               sunday_replacements, employee):
        """Calculate summary statistics for the month"""
        total_days_in_month = (end_date - start_date).days
        
        # Count Sundays
        sundays_in_month = sum(
            1 for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1))
            if day.date().weekday() == 6  # Sunday
        )
        
        # Count regular Sundays (not replaced)
        regular_sundays = sum(
            1 for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date-timedelta(days=1))
            if day.date().weekday() == 6 and  # Sunday
            not any(sr for sr in sunday_replacements 
                if (sr.department is None or sr.department == employee.employee_department) 
                and sr.sunday_date == day.date())
        )
        
        # Count replaced Sundays
        replaced_sundays = sum(
            1 for sr in sunday_replacements
            if (sr.department is None or sr.department == employee.employee_department) 
            and start_date <= sr.sunday_date < end_date
        )

        # For employees who don't get Sundays off, count all days as working days
        if not employee.is_getting_sunday:
            total_working_days = total_days_in_month - result['total_holiday_days']
        else:
            total_working_days = (
                total_days_in_month - 
                regular_sundays - 
                result['total_holiday_days'] +
                replaced_sundays
            )
        
        result.update({
            'total_days_in_month': total_days_in_month,
            'sundays_in_month': sundays_in_month,
            'total_working_days': total_working_days,
            'extra_days': {
                **result['extra_days'],
                'total': (
                    result['extra_days']['od_days'] -
                    result['extra_days']['gate_pass_deductions']
                )
            }
        })
        
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

    def convert_dates_to_strings(self, data):
        """Recursively convert date objects to ISO format strings"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self.convert_dates_to_strings(value)
                elif isinstance(value, date):
                    data[key] = value.isoformat()
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self.convert_dates_to_strings(item)
                elif isinstance(item, date):
                    data[i] = item.isoformat()
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
from .serializers import  EmployeeDocumentSerializer,EmployeeSerializeradvance
from rest_framework.decorators import action
from .models import  EmployeeDocument

class EmployeeViewSetadvance(viewsets.ReadOnlyModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializeradvance
    search_fields = ['employee_name', 'employee_id']
    ordering_fields = ['employee_name', 'id']
    ordering = ['employee_name']

# ViewSets for each model
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().prefetch_related('documents')
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ['employee_id', 'employee_name', 'father_name']
    ordering_fields = ['employee_id', 'employee_name', 'employee_department', 'joining_date']
    ordering = ['employee_id']

    def get_serializer_context(self):
        """Add request to serializer context for generating absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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

    @action(detail=True, methods=['get', 'post'])
    def documents(self, request, pk=None):
        """Endpoint for managing employee documents"""
        employee = self.get_object()
        
        if request.method == 'GET':
            documents = employee.documents.all()
            serializer = EmployeeDocumentSerializer(
                documents, 
                many=True, 
                context={'request': request}
            )
            return Response(serializer.data)
            
        elif request.method == 'POST':
            data = request.data.copy()
            data['employee'] = employee.id
            
            serializer = EmployeeDocumentSerializer(
                data=data, 
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            logger.error("Document upload validation error: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch', 'post'])
    def profile_picture(self, request, pk=None):
        """Endpoint for updating profile picture"""
        employee = self.get_object()
        
        if 'profile_picture' not in request.data:
            return Response(
                {'error': 'No profile picture provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(
            employee,
            data={'profile_picture': request.data['profile_picture']},
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def recent_joiners(self, request):
        """Custom endpoint for recently joined employees"""
        queryset = self.get_queryset().filter(
            joining_date__isnull=False
        ).order_by('-joining_date')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404


from django.shortcuts import get_object_or_404

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
    
    def get_queryset(self):
        employee_id = self.kwargs.get('employee_pk')
        return self.queryset.filter(employee_id=employee_id)
    
    def perform_create(self, serializer):
        employee_id = self.kwargs['employee_pk']
        employee = get_object_or_404(Employee, pk=employee_id)
        serializer.save(employee=employee)

    def create(self, request, *args, **kwargs):
        employee_id = self.kwargs['employee_pk']
        employee = get_object_or_404(Employee, pk=employee_id)
        
        # Add employee to serializer context
        serializer = self.get_serializer(data=request.data)
        serializer.context['employee'] = employee
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

from .serializers import EmployeeSerializerdocu, EmployeeDocumentSerializerdoc
from rest_framework import generics

class ActiveEmployeeListAPIView(generics.ListAPIView):
    """
    API endpoint to list all active employees (for dropdown selection)
    """
    queryset = Employee.objects.filter(is_active=True).order_by('employee_name')
    serializer_class = EmployeeSerializerdocu

class EmployeeDocumentListCreateAPIView(generics.ListCreateAPIView):
    queryset = EmployeeDocument.objects.all().order_by('-uploaded_at')
    serializer_class = EmployeeDocumentSerializerdoc

    def get_queryset(self):
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            return self.queryset.filter(employee__employee_id=employee_id)
        return self.queryset
    
class EmployeeDocumentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete an employee document
    """
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializerdoc
    lookup_field = 'id'

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
from .models import ProcessedAttendance, Employee,ProcessedSalary,SalaryAdvance
import math
from datetime import datetime
from django.db.models import Sum


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
            'is_getting_sunday', 'is_getting_ot', 'no_of_cl', 'employee_type','working_hours','is_getting_pf','is_monthly_salary','incentive'
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
                "Fix_Incentive": employee.incentive,
                "month": month,
                "year": year,
                "total_month_days": attendance_data.get('total_days_in_month', 30),
                "od_days": attendance_data.get('od_days', 0),
                "od_hours": attendance_data.get('od_hours', 0),
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
        
        return Response({
            "month": month,
            "year": year,
            "count": len(results),
            "processing_time_seconds": processing_time,
            "results": results
        })
    def get_salary_advance(self, employee, month, year):
        advances = SalaryAdvance.objects.filter(
            employee=employee,
            date_issued__year=year,
            date_issued__month=month
        ).aggregate(total_advance=Sum('amount'))

        return advances['total_advance'] or 0

    
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
            "total_salary": 0,
            "net_salary": 0
        }
        
        if not employee.salary or employee.salary <= 0:
            return salary_components
        
        total_days = int(attendance_data.get('total_days_in_month', 30))
        present_days = float(attendance_data.get('total_present_days', 0))
        absent_days = float(attendance_data.get('total_absent_days', 0))
        sundays = int(attendance_data.get('sundays_in_month', 0))
        leave_days = float(attendance_data.get('total_leave_days', 0))
        per_day_salary = float(employee.salary) / total_days
        fix_incentive = float(employee.incentive) if employee.incentive else 0
        per_day_fixincentive = fix_incentive / total_days if total_days else 0
        # Handle CL days - subtract from absent and add to present
        available_cl = employee.no_of_cl  # Total CL available to the employee
        working_hours = float(employee.working_hours)  # Total CL available to the employee
        cl_used = min(available_cl, absent_days)  # Can't use more CL than absent days
        
        # Adjust present and absent days based on CL usage 
        adjusted_present = present_days + cl_used
        adjusted_absent = absent_days - cl_used
        
        # Calculate eligible sundays based on adjusted absent days
        eligible_sundays = sundays if employee.is_getting_sunday else 0
        
        # Apply sunday deduction rules based on adjusted absent days
        if eligible_sundays > 0 and adjusted_absent >= 3:
            if adjusted_absent >= 9:
                eligible_sundays = 0
            elif adjusted_absent >= 7:
                eligible_sundays = max(0, eligible_sundays - 3)
            elif adjusted_absent >= 5:
                eligible_sundays = max(0, eligible_sundays - 2)
            else:
                eligible_sundays = max(0, eligible_sundays - 1)
        
        # Calculate gross salary based on monthly/daily salary type
        if employee.is_monthly_salary:
            # Monthly salary calculation (divide by total days * present days)
            per_day_salary = float(employee.salary) / total_days
            gross_salary = round((adjusted_present + eligible_sundays) * per_day_salary, 2)
        else:
            # Daily wage calculation (salary is already per day)
            gross_salary = round((adjusted_present + eligible_sundays) * float(employee.salary), 2)
        if employee.employee_id == 'SSB129':
            print(gross_salary)
            print(adjusted_present)
            print(eligible_sundays)
            print(per_day_salary)
        
        # Calculate salary components
        basic_salary = round(gross_salary / 2, 2)
        total_fix_incentive = round((adjusted_present + eligible_sundays) * per_day_fixincentive , 2)
        # PF calculation (12% of basic, max 15000)
        Process_total_present_dayes=adjusted_present + eligible_sundays
        pf = 0
        if employee.is_getting_pf:
            pf_base = min(basic_salary, 15000)
            pf = round(pf_base * 0.12, 2)
        
        attdence_bonous=0
        if employee.employee_department=='CNC' and Process_total_present_dayes==total_days:
            attdence_bonous=1000
        
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
            overtime_hours = float(attendance_data.get('total_overtime_hours', 0))
            if overtime_hours > 0:
                if employee.is_monthly_salary:
                    per_hour_rate = float(employee.salary) / (total_days * working_hours)
                else:
                    per_hour_rate = float(employee.salary) / working_hours
                overtime_payment = round(overtime_hours * per_hour_rate, 2)
        
        # Calculate OD payment
        od_payment = 0
        od_days = int(float(attendance_data.get('extra_days', {}).get('od_days', 0)))
        od_hours = float(attendance_data.get('extra_days', {}).get('od_hours', 0))

        if od_days > 0 or od_hours > 0:
            if employee.is_monthly_salary:
                per_day_rate = float(employee.salary) / total_days
                per_hour_rate = per_day_rate / float(working_hours)
            else:
                per_day_rate = float(employee.salary)
                per_hour_rate = per_day_rate /float(working_hours)
            
            od_payment = round((od_days * per_day_rate) + (od_hours * per_hour_rate), 2)
        
        # Calculate incentive (overtime + OD)
        incentive = round(overtime_payment + od_payment, 2)
        
        # Calculate total salary
        total_salary = round(gross_salary + incentive + total_fix_incentive + attdence_bonous - pf - esic, 2)

        salary_advance = self.get_salary_advance(employee, attendance_data.get('month'), attendance_data.get('year'))

        # Adjust final salary
        net_salary = round(Decimal(total_salary) - salary_advance, 2)

        return {
            "gross_salary": gross_salary,
            "basic_salary": basic_salary,
            "hra": hra,
            "medical_allowance": medical_allowance,
            "conveyance_allowance": conveyance_allowance,
            "pf": pf,
            "attdence_bonous":attdence_bonous,
            "esic": esic,
            "incentive": incentive,
            "total_fix_incentive": total_fix_incentive,
            "overtime_payment": overtime_payment,
            "od_payment": od_payment,
            "total_salary": total_salary,
            "salary_advance": salary_advance,
            "net_salary": net_salary,
            "cl_used": cl_used,  # Add CL used to the response
            "cl_remaining": available_cl - cl_used  # Add remaining CL to the response
        }
from .serializers import SalaryAdvanceSerializer, BulkSalaryAdvanceSerializer

class SalaryAdvanceViewSet(viewsets.ModelViewSet):
    queryset = SalaryAdvance.objects.select_related('employee').all()
    serializer_class = SalaryAdvanceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'employee__id': ['exact'],
        'amount': ['exact', 'gte', 'lte'],
        'date_issued': ['exact', 'gte', 'lte'],
    }
    search_fields = ['employee__employee_name', 'reason']
    ordering_fields = ['date_issued', 'amount', 'created_at']
    ordering = ['-date_issued']

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = BulkSalaryAdvanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        salary_advances = [SalaryAdvance(**item) for item in serializer.validated_data]
        SalaryAdvance.objects.bulk_create(salary_advances)

    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Convert to DataFrame for easy export
        df = pd.DataFrame(serializer.data)
        
        format = request.query_params.get('format', 'csv')
        
        if format == 'csv':
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            response = Response(output, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename=salary_advances_{datetime.now().date()}.csv'
        elif format == 'excel':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            response = Response(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename=salary_advances_{datetime.now().date()}.xlsx'
        else:
            return Response({"error": "Unsupported export format"}, status=400)
            
        return response