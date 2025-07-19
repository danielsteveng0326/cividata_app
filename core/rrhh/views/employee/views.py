import json
from io import BytesIO

import pandas as pd
import xlsxwriter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, View

from config import settings
from core.rrhh.forms import EmployeeForm, User, Employee, EmployeeUserForm
from core.rrhh.models import Position, Area
from core.security.mixins import GroupModuleMixin, GroupPermissionMixin


class EmployeeListView(GroupPermissionMixin, ListView):
    model = Employee
    template_name = 'employee/list.html'
    permission_required = 'view_employee'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'search':
                data = []
                for i in self.model.objects.filter():
                    data.append(i.as_dict())
            elif action == 'upload_excel':
                with transaction.atomic():
                    archive = request.FILES['archive']
                    df = pd.read_excel(archive, engine='openpyxl', dtype={'Código': str, 'Fecha de ingreso': str, 'Número de documento': str})
                    for record in json.loads(df.to_json(orient='records')):
                        user, created = User.objects.update_or_create(username=record['Número de documento'], defaults={
                            'names': record['Nombres'],
                            'is_active': record['Estado']
                        })
                        if created:
                            group = Group.objects.get(pk=settings.GROUPS['employee'])
                            if not user.groups.filter(id=group.id).exists():
                                user.groups.add(group)
                        employee, created = self.model.objects.update_or_create(
                            code=str(record['Código']),
                            user_id=user.id,
                            dni=record['Número de documento'],
                            defaults={
                                'hiring_date': record['Fecha de ingreso'],
                                'position': Position.objects.get_or_create(name=record['Cargo'])[0],
                                'area': Area.objects.get_or_create(name=record['Área'])[0],
                                'remuneration': float(record['Remuneración']),
                            }
                        )
                        print(f'{employee.id} => {created}')
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Listado de {self.model._meta.verbose_name_plural}'
        context['create_url'] = reverse_lazy('employee_create')
        return context


class EmployeeCreateView(GroupPermissionMixin, CreateView):
    model = Employee
    template_name = 'employee/create.html'
    form_class = EmployeeForm
    success_url = reverse_lazy('employee_list')
    permission_required = 'add_employee'

    def get_form_user(self):
        form = EmployeeUserForm()
        if self.request.POST or self.request.FILES:
            form = EmployeeUserForm(self.request.POST, self.request.FILES)
        return form

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'add':
                with transaction.atomic():
                    form1 = self.get_form_user()
                    form2 = self.get_form()
                    if form1.is_valid() and form2.is_valid():
                        user = form1.save(commit=False)
                        user.username = form2.cleaned_data['dni']
                        user.set_password(user.username)
                        user.save()
                        user.groups.add(Group.objects.get(pk=settings.GROUPS['employee']))
                        form_employee = form2.save(commit=False)
                        form_employee.user = user
                        form_employee.save()
                    else:
                        if not form1.is_valid():
                            data['error'] = form1.errors
                        elif not form2.is_valid():
                            data['error'] = form2.errors
            elif action == 'validate_data':
                field = request.POST['field']
                filters = Q()
                if field == 'dni':
                    filters &= Q(dni__iexact=request.POST['dni'])
                elif field == 'code':
                    filters &= Q(code__iexact=request.POST['code'])
                data['valid'] = not self.model.objects.filter(filters).exists() if filters.children else True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['title'] = f'Creación de un {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['frmUser'] = self.get_form_user()
        return context


class EmployeeUpdateView(GroupPermissionMixin, UpdateView):
    model = Employee
    template_name = 'employee/create.html'
    form_class = EmployeeForm
    success_url = reverse_lazy('employee_list')
    permission_required = 'change_employee'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_user(self):
        form = EmployeeUserForm(instance=self.request.user)
        if self.request.POST or self.request.FILES:
            form = EmployeeUserForm(self.request.POST, self.request.FILES, instance=self.object.user)
        return form

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'edit':
                with transaction.atomic():
                    form1 = self.get_form_user()
                    form2 = self.get_form()
                    if form1.is_valid() and form2.is_valid():
                        user = form1.save(commit=False)
                        user.save()
                        form_employee = form2.save(commit=False)
                        form_employee.user = user
                        form_employee.save()
                    else:
                        if not form1.is_valid():
                            data['error'] = form1.errors
                        elif not form2.is_valid():
                            data['error'] = form2.errors
            elif action == 'validate_data':
                field = request.POST['field']
                filters = Q()
                if field == 'dni':
                    filters &= Q(dni__iexact=request.POST['dni'])
                elif field == 'code':
                    filters &= Q(code__iexact=request.POST['code'])
                data['valid'] = not self.model.objects.filter(filters).exclude(id=self.object.id).exists() if filters.children else True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['title'] = f'Edición de un {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['frmUser'] = EmployeeUserForm(instance=self.object.user)
        return context


class EmployeeDeleteView(GroupPermissionMixin, DeleteView):
    model = Employee
    template_name = 'delete.html'
    success_url = reverse_lazy('employee_list')
    permission_required = 'delete_employee'

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
        return context


class EmployeeUpdateProfileView(GroupModuleMixin, UpdateView):
    model = Employee
    template_name = 'employee/profile.html'
    form_class = EmployeeForm
    success_url = settings.LOGIN_REDIRECT_URL

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.employee

    def get_form(self, form_class=None):
        form = super(EmployeeUpdateProfileView, self).get_form(form_class)
        for name in ['dni', 'code', 'position', 'area', 'hiring_date', 'remuneration']:
            form.fields[name].widget.attrs['readonly'] = True
        return form

    def get_form_user(self):
        form = EmployeeUserForm(instance=self.request.user)
        if self.request.POST or self.request.FILES:
            form = EmployeeUserForm(self.request.POST, self.request.FILES, instance=self.request.user)
        for name in ['names']:
            form.fields[name].widget.attrs['readonly'] = True
            form.fields[name].required = False
        return form

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'edit':
                with transaction.atomic():
                    form1 = self.get_form_user()
                    form2 = self.get_form()
                    if form1.is_valid() and form2.is_valid():
                        user = form1.save(commit=False)
                        user.save()
                        form_employee = form2.save(commit=False)
                        form_employee.user = user
                        form_employee.save()
                    else:
                        if not form1.is_valid():
                            data['error'] = form1.errors
                        elif not form2.is_valid():
                            data['error'] = form2.errors
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['title'] = f'Edición de un perfil de {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['frmUser'] = self.get_form_user()
        return context


class EmployeeExportExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            columns_info = [
                ('Código', 20, lambda c: c.code),
                ('Nombres', 50, lambda c: c.user.names),
                ('Número de documento', 35, lambda c: c.dni),
                ('Cargo', 35, lambda c: c.position.name),
                ('Fecha de ingreso', 35, lambda c: c.formatted_hiring_date()),
                ('Área', 35, lambda c: c.area.name),
                ('Remuneración', 30, lambda c: f'{c.remuneration:.2f}'),
                ('Estado', 30, lambda c: c.user.is_active)
            ]
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Empleados')
            cell_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
            row_format = workbook.add_format({'align': 'center', 'border': 1})
            for index, (name, width, _) in enumerate(columns_info):
                worksheet.set_column(index, index, width)
                worksheet.write(0, index, name, cell_format)
            for row, employee in enumerate(Employee.objects.filter(), start=1):
                for col, (_, _, value_func) in enumerate(columns_info):
                    worksheet.write(row, col, value_func(employee), row_format)
            workbook.close()
            output.seek(0)
            filename = 'EMPLEADOS.xlsx'
            response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        except:
            pass
        return HttpResponseRedirect(reverse_lazy('employee_list'))
