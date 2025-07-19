from django.urls import path
from core.rrhh.views.company.views import *
from core.rrhh.views.area.views import *
from core.rrhh.views.position.views import *
from core.rrhh.views.heading.views import *
from core.rrhh.views.employee.views import *
from core.rrhh.views.salary.views import *
from core.rrhh.views.assistance.views import *

urlpatterns = [
    # company
    path('company/update/', CompanyUpdateView.as_view(), name='company_update'),
    # area
    path('area/', AreaListView.as_view(), name='area_list'),
    path('area/add/', AreaCreateView.as_view(), name='area_create'),
    path('area/update/<int:pk>/', AreaUpdateView.as_view(), name='area_update'),
    path('area/delete/<int:pk>/', AreaDeleteView.as_view(), name='area_delete'),
    # position
    path('position/', PositionListView.as_view(), name='position_list'),
    path('position/add/', PositionCreateView.as_view(), name='position_create'),
    path('position/update/<int:pk>/', PositionUpdateView.as_view(), name='position_update'),
    path('position/delete/<int:pk>/', PositionDeleteView.as_view(), name='position_delete'),
    # heading
    path('heading/', HeadingListView.as_view(), name='heading_list'),
    path('heading/add/', HeadingCreateView.as_view(), name='heading_create'),
    path('heading/update/<int:pk>/', HeadingUpdateView.as_view(), name='heading_update'),
    path('heading/delete/<int:pk>/', HeadingDeleteView.as_view(), name='heading_delete'),
    # employee
    path('employee/', EmployeeListView.as_view(), name='employee_list'),
    path('employee/add/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employee/update/<int:pk>/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employee/update/profile/', EmployeeUpdateProfileView.as_view(), name='employee_update_profile'),
    path('employee/delete/<int:pk>/', EmployeeDeleteView.as_view(), name='employee_delete'),
    path('employee/export/excel/', EmployeeExportExcelView.as_view(), name='employee_export_excel'),
    # assistance
    path('assistance/', AssistanceListView.as_view(), name='assistance_list'),
    path('assistance/add/', AssistanceCreateView.as_view(), name='assistance_create'),
    path('assistance/delete/<str:start_date>/<str:end_date>/', AssistanceDeleteView.as_view(), name='assistance_delete'),
    path('assistance/update/<str:date_joined>/', AssistanceUpdateView.as_view(), name='assistance_update'),
    path('assistance/employee/', AssistanceEmployeeListView.as_view(), name='assistance_employee_list'),
    # salary
    path('salary/', SalaryListView.as_view(), name='salary_list'),
    path('salary/add/', SalaryCreateView.as_view(), name='salary_create'),
    path('salary/delete/', SalaryDeleteView.as_view(), name='salary_delete'),
    path('salary/print/<int:pk>/', SalaryPrintView.as_view(), name='salary_print_receipt'),
    path('salary/employee/', SalaryEmployeeListView.as_view(), name='salary_employee_list'),
    path('salary/employee/print/<int:pk>/', SalaryPrintView.as_view(), name='salary_employee_print_receipt'),
]
