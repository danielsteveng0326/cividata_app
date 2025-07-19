import json
from datetime import datetime
from io import BytesIO

import xlsxwriter
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from core.rrhh.forms import AssistanceForm, Assistance, Employee, AssistanceDetail
from core.security.mixins import GroupPermissionMixin


class AssistanceListView(GroupPermissionMixin, ListView):
    model = Assistance
    template_name = 'assistance/list_admin.html'
    permission_required = 'view_assistance_admin'

    def post(self, request, *args, **kwargs):
        action = request.POST['action']
        data = {}
        try:
            if action == 'search':
                data = []
                start_date = request.POST['start_date']
                end_date = request.POST['end_date']
                filters = Q()
                if len(start_date) and len(end_date):
                    filters &= Q(assistance__date_joined__range=[start_date, end_date])
                for i in AssistanceDetail.objects.filter(filters).order_by('assistance__date_joined'):
                    data.append(i.as_dict())
            elif action == 'export_assistences_excel':
                start_date = request.POST['start_date']
                end_date = request.POST['end_date']
                filters = Q()
                if len(start_date) and len(end_date):
                    filters &= Q(assistance__date_joined__range=[start_date, end_date])
                columns_info = [
                    ('Fecha de asistencia', 35, lambda c: c.assistance.formatted_date_joined()),
                    ('Empleado', 50, lambda c: c.employee.user.names),
                    ('Número de documento', 50, lambda c: c.employee.dni),
                    ('Cargo', 50, lambda c: c.employee.position.name),
                    ('Area', 50, lambda c: c.employee.area.name),
                    ('Observación', 50, lambda c: c.description),
                    ('Asistencia', 50, lambda c: c.active),
                ]
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet('Asistencias')
                cell_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
                row_format = workbook.add_format({'align': 'center', 'border': 1})
                for index, (name, width, _) in enumerate(columns_info):
                    worksheet.set_column(index, index, width)
                    worksheet.write(0, index, name, cell_format)
                for row, assistance_detail in enumerate(AssistanceDetail.objects.filter(filters).order_by('assistance__date_joined'), start=1):
                    for col, (_, _, value_func) in enumerate(columns_info):
                        worksheet.write(row, col, value_func(assistance_detail), row_format)
                workbook.close()
                output.seek(0)
                filename = 'ASISTENCIAS.xlsx'
                response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename={filename}'
                response['X-Filename'] = filename
                return response
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Listado de {self.model._meta.verbose_name_plural}'
        context['create_url'] = reverse_lazy('assistance_create')
        context['form'] = AssistanceForm()
        return context


class AssistanceCreateView(GroupPermissionMixin, CreateView):
    model = Assistance
    template_name = 'assistance/create_admin.html'
    form_class = AssistanceForm
    success_url = reverse_lazy('assistance_list')
    permission_required = 'add_assistance_admin'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'add':
                with transaction.atomic():
                    date_joined = datetime.strptime(request.POST['date_joined'], '%Y-%m-%d')
                    assistance = self.model.objects.create(
                        date_joined=date_joined,
                        year=date_joined.year,
                        month=date_joined.month,
                        day=date_joined.day
                    )
                    for i in json.loads(request.POST['assistances']):
                        AssistanceDetail.objects.create(
                            assistance_id=assistance.id,
                            employee_id=int(i['id']),
                            description=i['description'],
                            active=i['active'],
                        )
            elif action == 'generate_assistance':
                data = []
                for i in Employee.objects.filter(user__is_active=True):
                    item = i.as_dict()
                    item['active'] = 0
                    item['description'] = ''
                    data.append(item)
            elif action == 'validate_data':
                data = {'valid': not self.model.objects.filter(date_joined=request.POST['date_joined'].strip()).exists()}
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['title'] = f'Creación de una {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context


class AssistanceUpdateView(GroupPermissionMixin, CreateView):
    model = Assistance
    template_name = 'assistance/create_admin.html'
    form_class = AssistanceForm
    success_url = reverse_lazy('assistance_list')
    permission_required = 'change_assistance_admin'

    def get_form(self, form_class=None):
        form = AssistanceForm(initial={'date_joined': self.kwargs['date_joined']})
        form.fields['date_joined'].widget.attrs.update({'disabled': True})
        return form

    def get_object(self, queryset=None):
        return Assistance.objects.filter(date_joined=self.kwargs['date_joined']).first()

    def get(self, request, *args, **kwargs):
        if self.get_object():
            return super(AssistanceUpdateView, self).get(request, *args, **kwargs)
        messages.error(request, f"No se puede editar la asistencia del día {self.kwargs['date_joined']} porque no existe")
        return HttpResponseRedirect(self.success_url)

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'edit':
                with transaction.atomic():
                    for i in json.loads(request.POST['assistances']):
                        if 'pk' in i:
                            detail = AssistanceDetail.objects.get(pk=i['pk'])
                        else:
                            date_joined = datetime.strptime(self.kwargs['date_joined'], '%Y-%m-%d')
                            assistance = self.model.objects.get_or_create(date_joined=date_joined, year=date_joined.year, month=date_joined.month, day=date_joined.day)[0]
                            detail = AssistanceDetail()
                            detail.assistance_id = assistance.id
                        detail.employee_id = i['id']
                        detail.description = i['description']
                        detail.active = i['active']
                        detail.save()
            elif action == 'generate_assistance':
                data = []
                date_joined = self.kwargs['date_joined']
                for i in Employee.objects.filter(user__is_active=True):
                    item = i.as_dict()
                    item['active'] = 0
                    item['description'] = ''
                    assistance_detail = AssistanceDetail.objects.filter(assistance__date_joined=date_joined, employee_id=i.id).first()
                    if assistance_detail:
                        item['pk'] = assistance_detail.id
                        item['active'] = 1 if assistance_detail.active else 0
                        item['description'] = assistance_detail.description
                    data.append(item)
            elif action == 'validate_data':
                data = {'valid': not self.model.objects.filter(date_joined=request.POST['date_joined']).exclude(date_joined=self.kwargs['date_joined']).exists()}
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['title'] = f'Edición de una {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class AssistanceDeleteView(GroupPermissionMixin, ListView):
    model = Assistance
    template_name = 'assistance/delete_admin.html'
    success_url = reverse_lazy('assistance_list')
    permission_required = 'delete_assistance_admin'

    def get(self, request, *args, **kwargs):
        if self.get_object():
            return super(AssistanceDeleteView, self).get(request, *args, **kwargs)
        messages.error(request, 'No se encontraron asistencias dentro del rango de fechas especificado')
        return HttpResponseRedirect(self.success_url)

    def get_object(self, queryset=None):
        return self.model.objects.filter(date_joined__range=[self.kwargs['start_date'], self.kwargs['end_date']]).first()

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.get_object().delete()
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminación de un {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['start_date'] = self.kwargs['start_date']
        context['end_date'] = self.kwargs['end_date']
        return context


class AssistanceEmployeeListView(GroupPermissionMixin, ListView):
    model = Assistance
    template_name = 'assistance/list_employee.html'
    permission_required = 'view_assistance_employee'

    def post(self, request, *args, **kwargs):
        action = request.POST['action']
        data = {}
        try:
            if action == 'search':
                data = []
                start_date = request.POST['start_date']
                end_date = request.POST['end_date']
                filters = Q(employee__user=request.user)
                if len(start_date) and len(end_date):
                    filters &= Q(assistance__date_joined__range=[start_date, end_date])
                for i in AssistanceDetail.objects.filter(filters).order_by('assistance__date_joined'):
                    data.append(i.as_dict())
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Listado de {self.model._meta.verbose_name_plural}'
        context['form'] = AssistanceForm()
        return context
