import json
from datetime import datetime
from io import BytesIO

import pandas as pd
import xlsxwriter
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum, Q, FloatField
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView

from core.rrhh import printer
from core.rrhh.forms import SalaryForm, Salary, SalaryDetail, SalaryHeading, Employee, Heading, Company, MONTHS, ITEM_TYPE
from core.security.mixins import GroupPermissionMixin


class SalaryListView(GroupPermissionMixin, CreateView):
    model = Salary
    template_name = 'salary/list_admin.html'
    form_class = SalaryForm
    permission_required = 'view_salary_admin'

    def get_form(self, form_class=None):
        form = SalaryForm()
        form.fields['year'].initial = datetime.now().date().year
        return form

    def write_salary_details_to_worksheet(self, worksheet, salary_detail, heading, row_format, row, index):
        if salary_detail:
            salary_heading = salary_detail.salaryheading_set.filter(heading_id=heading.id).first()
            if heading.has_quantity:
                worksheet.write(row, index + 1, salary_heading.get_quantity(), row_format)
                worksheet.write(row, index + 2, salary_heading.formatted_amount(), row_format)
                index += 2
            else:
                worksheet.write(row, index + 1, salary_heading.formatted_amount(), row_format)
                index += 1
        else:
            if heading.has_quantity:
                worksheet.write(row, index + 1, 0, row_format)
                worksheet.write(row, index + 2, 0.00, row_format)
                index += 2
            else:
                worksheet.write(row, index + 1, 0.00, row_format)
                index += 1
        return index

    def post(self, request, *args, **kwargs):
        action = request.POST['action']
        data = {}
        try:
            if action == 'search':
                data = []
                year = request.POST['year']
                month = request.POST['month']
                employee_id = json.loads(request.POST['employee_id'])
                filters = Q()
                if len(year):
                    filters &= Q(salary__year=year)
                if len(month):
                    filters &= Q(salary__month=month)
                if len(employee_id):
                    filters &= Q(employee_id__in=employee_id)
                for i in SalaryDetail.objects.filter(filters):
                    item = i.as_dict()
                    item['selected'] = 0
                    data.append(item)
            elif action == 'send_salary_email':
                not_sent = []
                salaries = SalaryDetail.objects.filter(id__in=json.loads(request.POST['salaries']))
                for salary_detail in salaries:
                    if not salary_detail.send_salary_email():
                        not_sent.append(salary_detail.__str__())
                if len(not_sent):
                    text = f','.join(not_sent)
                    data['error'] = f'No se han enviado los roles de pago de los empleados: {text}'
            elif action == 'search_detail_heading':
                data = []
                detail = SalaryDetail.objects.get(pk=request.POST['id'])
                for i in detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[0][0], amount__gt=0).order_by('heading__order'):
                    data.append([i.heading.name, i.get_quantity(), i.formatted_amount(), '---'])
                for i in detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[1][0], amount__gt=0).order_by('heading__order'):
                    data.append([i.heading.name, i.get_quantity(), '---', i.formatted_amount()])
                data.append(['Subtotal de Ingresos', '---', '---', detail.formatted_income()])
                data.append(['Subtotal de Descuentos', '---', '---', detail.formatted_expenses()])
                data.append(['Total a recibir', '---', '---', detail.formatted_total_amount()])
            elif action == 'upload_template_excel':
                with transaction.atomic():
                    year = int(request.POST['year'])
                    month = int(request.POST['month'])
                    archive = request.FILES['archive']
                    df = pd.read_excel(archive, engine='openpyxl', dtype=str)
                    df.columns = [col.strip() for col in df.columns]
                    for index, row in df.iterrows():
                        employee_code = row['Código']
                        employee = Employee.objects.get(code=employee_code)
                        salary_detail, created = SalaryDetail.objects.get_or_create(
                            employee=employee,
                            salary__year=year,
                            salary__month=month,
                            defaults={'salary': Salary.objects.get_or_create(year=year, month=month, company=Company.objects.first())[0]}
                        )
                        salary_detail.salaryheading_set.all().delete()
                        columns = [column for column in df.columns[6:-2]]
                        index = 0
                        while index < len(columns):
                            column = columns[index]
                            if 'Subtotal' in column:
                                index += 1
                                continue

                            amount = row[column]
                            detail = SalaryHeading()
                            detail.salary_detail = salary_detail

                            if 'Cantidad' in column:
                                detail.heading = Heading.objects.get(name=column.split('.')[-1])
                                detail.quantity = amount
                                detail.amount = str(row[df.columns[df.columns.get_loc(column) + 1]])
                                index += 1
                            else:
                                detail.heading = Heading.objects.get(name=column)
                                detail.amount = str(amount)

                            detail.amount = detail.amount.replace('.', '')
                            detail.save()
                            index += 1

                        salary_detail.income = salary_detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[0][0]).aggregate(result=Coalesce(Sum('amount'), 0.00, output_field=FloatField()))['result']
                        salary_detail.expenses = salary_detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[1][0]).aggregate(result=Coalesce(Sum('amount'), 0.00, output_field=FloatField()))['result']
                        salary_detail.total_amount = float(salary_detail.income) - float(salary_detail.expenses)
                        salary_detail.save()
            elif action == 'search_employee':
                data = []
                term = request.POST['term']
                for i in Employee.objects.filter(Q(user__names__icontains=term) | Q(dni__icontains=term) | Q(code__icontains=term)).order_by('user__names')[0:10]:
                    data.append(i.as_dict())
            elif action == 'remove_salaries':
                request.session['salaries'] = dict()
                employee_id = json.loads(request.POST['employee_id'])
                request.session['salaries']['year'] = int(request.POST['year'])
                month = request.POST['month']
                request.session['salaries']['month'] = dict()
                if len(month):
                    request.session['salaries']['month']['id'] = int(month)
                    request.session['salaries']['month']['name'] = MONTHS[int(month)][1]
                request.session['salaries']['employees'] = dict()
                if len(employee_id):
                    request.session['salaries']['employees'] = Employee.objects.filter(id__in=employee_id)
                data['url'] = str(reverse_lazy('salary_delete'))
            elif action == 'export_salaries_pdf':
                year = request.POST['year']
                month = request.POST['month']
                employee_id = json.loads(request.POST['employee_id'])
                filters = Q(salary__year=year)
                if len(month):
                    filters &= Q(salary__month=month)
                if len(employee_id):
                    filters &= Q(employee_id__in=employee_id)
                context = {
                    'salaries': SalaryDetail.objects.filter(filters),
                    'prints': [1, 2],
                    'date_joined': datetime.now().date()
                }
                filename = 'SALARIOS.pdf'
                pdf_file = printer.create_pdf(context=context, template_name='salary/payroll_receipt2.html')
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={filename}'
                response['X-Filename'] = filename
                return response
            elif action == 'export_salaries_excel':
                year = request.POST['year']
                month = request.POST['month']
                employee_id = json.loads(request.POST['employee_id'])
                filters = Q(salary__year=year)
                if len(month):
                    filters &= Q(salary__month=month)
                if len(employee_id):
                    filters &= Q(employee_id__in=employee_id)

                columns_info = [
                    ('Código', 15),
                    ('Empleado', 35),
                    ('Sección', 35),
                    ('Cargo', 35),
                    ('Número de documento', 35),
                    ('Fecha de ingreso', 35)
                ]

                headings = Heading.objects.filter()
                for heading in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('order'):
                    if heading.has_quantity:
                        columns_info.append((f'Cantidad.{heading.name}', 35))
                    columns_info.append((heading.name, 55))
                columns_info.append(('Subtotal', 55))
                for heading in headings.filter(item_type=ITEM_TYPE[1][0]).order_by('order'):
                    if heading.has_quantity:
                        columns_info.append((f'Cantidad.{heading.name}', 35))
                    columns_info.append((heading.name, 55))
                columns_info.extend([
                    ('Total Descuento', 55),
                    ('Total a Cobrar', 55),
                ])

                output = BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet('planilla')
                cell_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
                row_format = workbook.add_format({'align': 'center', 'border': 1})
                for index, (name, width) in enumerate(columns_info):
                    worksheet.set_column(index, index, width)
                    worksheet.write(0, index, name, cell_format)

                salaries = SalaryDetail.objects.filter(filters).select_related('employee', 'employee__area', 'employee__position').prefetch_related('salaryheading_set').order_by('employee')

                for row, salary_detail in enumerate(salaries, start=1):
                    worksheet.write(row, 0, salary_detail.employee.code, row_format)
                    worksheet.write(row, 1, salary_detail.employee.user.names, row_format)
                    worksheet.write(row, 2, salary_detail.employee.area.name, row_format)
                    worksheet.write(row, 3, salary_detail.employee.position.name, row_format)
                    worksheet.write(row, 4, salary_detail.employee.dni, row_format)
                    worksheet.write(row, 5, salary_detail.employee.formatted_hiring_date(), row_format)
                    index = 5
                    for heading in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('order'):
                        index = self.write_salary_details_to_worksheet(worksheet, salary_detail, heading, row_format, row, index)
                    index += 1
                    worksheet.write(row, index, salary_detail.formatted_income() if salary_detail else 0.00, row_format)
                    for heading in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('order'):
                        index = self.write_salary_details_to_worksheet(worksheet, salary_detail, heading, row_format, row, index)
                    worksheet.write(row, index + 1, salary_detail.formatted_expenses() if salary_detail else 0.00, row_format)
                    worksheet.write(row, index + 2, salary_detail.formatted_total_amount() if salary_detail else 0.00, row_format)

                workbook.close()
                output.seek(0)
                filename = f"PLANILLA_{datetime.now().date().strftime('%d_%m_%Y')}.xlsx"
                response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename={filename}'
                response['X-Filename'] = filename
                return response
            elif action == 'export_template_excel':
                year = request.POST['year']
                month = request.POST['month']

                columns_info = [
                    ('Código', 15),
                    ('Empleado', 35),
                    ('Sección', 35),
                    ('Cargo', 35),
                    ('Número de documento', 35),
                    ('Fecha de ingreso', 35)
                ]
                headings = Heading.objects.filter()
                for heading in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('order'):
                    if heading.has_quantity:
                        columns_info.append((f'Cantidad.{heading.name}', 35))
                    columns_info.append((heading.name, 55))
                columns_info.append(('Subtotal', 55))
                for heading in headings.filter(item_type=ITEM_TYPE[1][0]).order_by('order'):
                    if heading.has_quantity:
                        columns_info.append((f'Cantidad.{heading.name}', 35))
                    columns_info.append((heading.name, 55))
                columns_info.extend([
                    ('Total Descuento', 55),
                    ('Total a Cobrar', 55),
                ])

                output = BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet('planilla')
                cell_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
                row_format = workbook.add_format({'align': 'center', 'border': 1})
                for index, (name, width) in enumerate(columns_info):
                    worksheet.set_column(index, index, width)
                    worksheet.write(0, index, name, cell_format)

                for row, employee in enumerate(Employee.objects.filter(user__is_active=True), start=1):
                    worksheet.write(row, 0, employee.code, row_format)
                    worksheet.write(row, 1, employee.user.names, row_format)
                    worksheet.write(row, 2, employee.area.name, row_format)
                    worksheet.write(row, 3, employee.position.name, row_format)
                    worksheet.write(row, 4, employee.dni, row_format)
                    worksheet.write(row, 5, employee.formatted_hiring_date(), row_format)
                    index = 5
                    salary_detail = SalaryDetail.objects.filter(employee=employee, salary__year=year, salary__month=month).first()
                    for heading in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('order'):
                        index = self.write_salary_details_to_worksheet(worksheet, salary_detail, heading, row_format, row, index)
                    index += 1
                    worksheet.write(row, index, salary_detail.formatted_income() if salary_detail else 0.00, row_format)
                    for heading in headings.filter(item_type=ITEM_TYPE[1][0]).order_by('order'):
                        index = self.write_salary_details_to_worksheet(worksheet, salary_detail, heading, row_format, row, index)
                    worksheet.write(row, index + 1, salary_detail.formatted_expenses() if salary_detail else 0.00, row_format)
                    worksheet.write(row, index + 2, salary_detail.formatted_total_amount() if salary_detail else 0.00, row_format)
                workbook.close()
                output.seek(0)
                filename = f"PLANILLA_{datetime.now().date().strftime('%d_%m_%Y')}.xlsx"
                response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f"attachment; filename='{filename}'"
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
        context['create_url'] = reverse_lazy('salary_create')
        return context


class SalaryCreateView(GroupPermissionMixin, CreateView):
    model = Salary
    template_name = 'salary/create_admin.html'
    form_class = SalaryForm
    success_url = reverse_lazy('salary_list')
    permission_required = 'add_salary_admin'

    def post(self, request, *args, **kwargs):
        action = request.POST['action']
        data = {}
        try:
            if action == 'add':
                with transaction.atomic():
                    salary = Salary.objects.get_or_create(year=int(request.POST['year']), month=int(request.POST['month']), company=Company.objects.first())[0]
                    for i in json.loads(request.POST['headings']):
                        heading = i
                        employee = Employee.objects.get(pk=int(heading['employee']['id']))
                        salary_detail = salary.salarydetail_set.filter(employee=employee).first()
                        if salary_detail:
                            salary_detail.salaryheading_set.all().delete()
                        else:
                            salary_detail = SalaryDetail()
                            salary_detail.salary_id = salary.id
                            salary_detail.employee_id = employee.id
                            salary_detail.save()
                        for key in ['employee', 'total_discounts', 'total_charge', 'total_assets']:
                            del heading[key]
                        for key, value in heading.items():
                            SalaryHeading.objects.create(
                                salary_detail_id=salary_detail.id,
                                heading_id=int(value['id']),
                                quantity=int(value['quantity']),
                                amount=float(value['amount'])
                            )
                        salary_detail.income = salary_detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[0][0]).aggregate(result=Coalesce(Sum('amount'), 0.00, output_field=FloatField()))['result']
                        salary_detail.expenses = salary_detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[1][0]).aggregate(result=Coalesce(Sum('amount'), 0.00, output_field=FloatField()))['result']
                        salary_detail.total_amount = float(salary_detail.income) - float(salary_detail.expenses)
                        salary_detail.save()
            elif action == 'search_employee':
                data = []
                term = request.POST['term']
                for i in Employee.objects.filter(Q(user__names__icontains=term) | Q(dni__icontains=term) | Q(code__icontains=term)).order_by('user__names')[0:10]:
                    data.append(i.as_dict())
            elif action == 'search_employees':
                detail = []
                year = int(request.POST['year'])
                month = int(request.POST['month'])
                employee_id = json.loads(request.POST['employee_id'])
                filters = Q(user__is_active=True)
                if len(employee_id):
                    filters &= Q(id__in=employee_id)
                employees = Employee.objects.filter(filters)
                columns = [{'data': 'employee.user.names'}]
                headings = Heading.objects.filter(active=True)
                for i in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('item_type', 'order', 'has_quantity'):
                    if i.has_quantity:
                        columns.append({'data': f'{i.code}.quantity'})
                    columns.append({'data': i.code})
                columns.append({'data': 'total_assets'})
                for i in headings.filter(item_type=ITEM_TYPE[1][0]).order_by('item_type', 'order'):
                    if i.has_quantity:
                        columns.append({'data': f'{i.code}.quantity'})
                    columns.append({'data': i.code})
                columns.append({'data': 'total_discounts'})
                columns.append({'data': 'total_charge'})
                for employee in employees:
                    heading = {}
                    for d in headings.filter(item_type=ITEM_TYPE[0][0]).order_by('order'):
                        item = d.as_dict()
                        item['quantity'] = 0
                        item['amount'] = 0.00
                        if d.code == 'salario':
                            item['amount'] = float(employee.remuneration)
                            item['quantity'] = employee.get_amount_of_assists(year, month)
                        queryset = d.get_amount_detail_salary(employee=employee.id, year=year, month=month)
                        if queryset:
                            item['amount'] = float(queryset.amount)
                            item['quantity'] = queryset.quantity
                        heading[d.code] = item
                    for d in headings.filter(item_type=ITEM_TYPE[1][0]).order_by('order'):
                        item = d.as_dict()
                        item['quantity'] = 0
                        item['amount'] = 0.00
                        queryset = d.get_amount_detail_salary(employee=employee.id, year=year, month=month)
                        if queryset:
                            item['amount'] = float(queryset.amount)
                            item['quantity'] = queryset.quantity
                        heading[d.code] = item
                    salary_detail = SalaryDetail.objects.filter(employee_id=employee.id, salary__year=year, salary__month=month).first()
                    if salary_detail:
                        heading['total_assets'] = {'code': 'total_assets', 'amount': float(salary_detail.income)}
                        heading['total_discounts'] = {'code': 'total_discounts', 'amount': float(salary_detail.expenses)}
                        heading['total_charge'] = {'code': 'total_charge', 'amount': float(salary_detail.total_amount)}
                    else:
                        heading['total_assets'] = {'code': 'total_assets', 'amount': 0.00}
                        heading['total_discounts'] = {'code': 'total_discounts', 'amount': 0.00}
                        heading['total_charge'] = {'code': 'total_charge', 'amount': float(employee.remuneration)}
                    heading['employee'] = employee.as_dict()
                    detail.append(heading)
                data = {'detail': detail, 'columns': columns}
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
        context['assets'] = Heading.objects.filter(active=True, item_type=ITEM_TYPE[0][0]).order_by('id')
        context['discounts'] = Heading.objects.filter(active=True, item_type=ITEM_TYPE[1][0]).order_by('id')
        return context


class SalaryDeleteView(GroupPermissionMixin, ListView):
    model = Salary
    template_name = 'salary/delete_admin.html'
    success_url = reverse_lazy('salary_list')
    permission_required = 'delete_salary_admin'

    def get(self, request, *args, **kwargs):
        if self.get_object():
            return super(SalaryDeleteView, self).get(request, *args, **kwargs)
        messages.error(request, 'No se encontraron salarios para el año y mes especificados')
        return HttpResponseRedirect(self.success_url)

    def get_object(self):
        try:
            month = self.request.session['salaries']['month']
            employees = self.request.session['salaries']['employees']
            filters = Q(salary__year=self.request.session['salaries']['year'])
            if len(month):
                filters &= Q(salary__month=month['id'])
            if len(employees):
                filters &= Q(employee_id__in=employees)
            return SalaryDetail.objects.filter(filters)
        except:
            pass
        return None

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.get_object().delete()
            if 'salaries' in request.session:
                del request.session['salaries']
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminación de un {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        return context


class SalaryPrintView(LoginRequiredMixin, TemplateView):
    template_name = 'salary/payroll_receipt1.html'
    success_url = reverse_lazy('salary_list')
    permission_required = 'print_salary'

    def get_success_url(self):
        if self.request.user.is_employee:
            return reverse_lazy('salary_employee_list')
        return self.success_url

    def get(self, request, *args, **kwargs):
        try:
            context = {
                'salary_detail': SalaryDetail.objects.get(pk=self.kwargs['pk']),
                'prints': [1, 2],
                'date_joined': datetime.now().date()
            }
            pdf_file = printer.create_pdf(context=context, template_name=self.template_name)
            return HttpResponse(pdf_file, content_type='application/pdf')
        except Exception as e:
            messages.error(request, str(e))
        return HttpResponseRedirect(self.get_success_url())


class SalaryEmployeeListView(GroupPermissionMixin, ListView):
    model = Salary
    template_name = 'salary/list_employee.html'
    permission_required = 'view_salary_employee'

    def post(self, request, *args, **kwargs):
        action = request.POST['action']
        data = {}
        try:
            if action == 'search':
                data = []
                year = request.POST['year']
                month = request.POST['month']
                filters = Q(employee=request.user.employee)
                if len(year):
                    filters &= Q(salary__year=year)
                if len(month):
                    filters &= Q(salary__month=month)
                for i in SalaryDetail.objects.filter(filters):
                    data.append(i.as_dict())
            elif action == 'search_detail_heading':
                data = []
                salary_detail = SalaryDetail.objects.get(pk=request.POST['id'])
                for i in salary_detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[0][0], amount__gt=0).order_by('heading__order'):
                    data.append([i.heading.name, i.get_quantity(), i.formatted_amount(), '---'])
                for i in salary_detail.salaryheading_set.filter(heading__item_type=ITEM_TYPE[1][0], amount__gt=0).order_by('heading__order'):
                    data.append([i.heading.name, i.get_quantity(), '---', i.formatted_amount()])
                data.append(['Subtotal de Ingresos', '---', '---', salary_detail.formatted_income()])
                data.append(['Subtotal de Descuentos', '---', '---', salary_detail.formatted_expenses()])
                data.append(['Total a recibir', '---', '---', salary_detail.formatted_total_amount()])
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Listado de {self.model._meta.verbose_name_plural}'
        context['form'] = SalaryForm()
        return context
