from .views import ProcessAttendanceAPI
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet, GatePassViewSet, ShiftAssignmentViewSet,
    ODSlipViewSet, SundayReplacementViewSet, HolidayViewSet,
    ManualPunchViewSet,EmployeeViewSet1,EmployeeViewSet2,ProcessedAttendanceAPIView,MissedPunchReportAPI,SalaryCalculationAPI
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'employees1', EmployeeViewSet1, basename='employee1')
router.register(r'employees2', EmployeeViewSet2, basename='employee2')
router.register(r'gatepasses', GatePassViewSet, basename='gatepass')
router.register(r'shiftassignments', ShiftAssignmentViewSet, basename='shiftassignment')
router.register(r'odslips', ODSlipViewSet, basename='odslip')
router.register(r'sundayreplacements', SundayReplacementViewSet, basename='sundayreplacement')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'manualpunches', ManualPunchViewSet, basename='manualpunch')



urlpatterns = [
    # Your other URLs here...
    # URL for ProcessAttendanceAPI
    path('api/attendance/process/', ProcessAttendanceAPI.as_view(), name='process-attendance'),
    path('', include(router.urls)),
    path('save/attendancesave/', ProcessedAttendanceAPIView.as_view(), name='processed-attendance'),
    path('misspunch/', MissedPunchReportAPI.as_view(), name='MissedPunch-ReportAPI'),
    path('salary-calculation/', SalaryCalculationAPI.as_view(), name='salary-calculation'),
]
