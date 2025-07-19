import calendar
import json
import locale
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, FloatField
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.views.generic import TemplateView

from core.rrhh.models import Area, SalaryHeading, Employee, SalaryDetail, Position, Heading
from core.security.models import Dashboard


class DashboardView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        dashboard = Dashboard.objects.first()
        if dashboard and dashboard.layout == 1:
            return 'vtc_dashboard_employee.html' if self.request.user.is_employee else 'vtc_dashboard_admin.html'
        return 'hzt_dashboard.html'

    def get(self, request, *args, **kwargs):
        request.user.set_group_session()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'get_monthly_salary_by_area':
                data = []
                year = datetime.now().year
                month = datetime.now().month
                for i in Area.objects.filter():
                    amount = SalaryHeading.objects.filter(salary_detail__salary__year=year, salary_detail__salary__month=month, salary_detail__employee__area_id=i.id).aggregate(result=Coalesce(Sum('amount'), 0.00, output_field=FloatField()))['result']
                    if amount:
                        data.append([i.name, float(amount)])
            elif action == 'get_yearly_total_salary':
                data = []
                year = datetime.now().year
                for month in range(1, 13):
                    result = SalaryDetail.objects.filter(salary__month=month, salary__year=year).aggregate(result=Coalesce(Sum('total_amount'), 0.00, output_field=FloatField()))['result']
                    data.append(float(result))
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Panel de administración'
        if not self.request.user.is_employee:
            context['employees'] = Employee.objects.all().count()
            context['areas'] = Area.objects.all().count()
            context['heading'] = Heading.objects.all().count()
            context['positions'] = Position.objects.all().count()
            context['salaries'] = SalaryDetail.objects.filter().order_by('-id')[0:10]
            context['year'] = datetime.now().year
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            context['month'] = calendar.month_name[datetime.now().month]
        return context
