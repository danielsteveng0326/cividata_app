import base64
import os
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.db import models
from django.forms import model_to_dict

from config import settings
from core.rrhh.choices import *
from core.rrhh.printer import create_pdf
from core.user.models import User


class Company(models.Model):
    name = models.CharField(max_length=50, help_text='Ingrese un nombre', verbose_name='Nombre')
    ruc = models.CharField(max_length=13, help_text='Ingrese un RUC', verbose_name='Ruc')
    address = models.CharField(max_length=200, help_text='Ingrese una dirección', verbose_name='Dirección')
    mobile = models.CharField(max_length=10, help_text='Ingrese un número de teléfono celular', verbose_name='Teléfono celular')
    phone = models.CharField(max_length=9, help_text='Ingrese un número de teléfono convencional', verbose_name='Teléfono convencional')
    email = models.CharField(max_length=50, help_text='Ingrese un correo electrónico', verbose_name='Email')
    website = models.CharField(max_length=250, help_text='Ingrese una página web', verbose_name='Página web')
    description = models.CharField(max_length=500, help_text='Ingrese una descripción', null=True, blank=True, verbose_name='Descripción')
    image = models.ImageField(null=True, blank=True, upload_to='company/%Y/%m/%d', verbose_name='Logo')
    signature = models.ImageField(null=True, blank=True, upload_to='company/%Y/%m/%d', verbose_name='Firma')

    def __str__(self):
        return self.name

    @property
    def base64_image(self):
        try:
            if self.image:
                with open(self.image.path, 'rb') as image_file:
                    base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                    extension = os.path.splitext(self.image.name)[1]
                    content_type = f'image/{extension.lstrip(".")}'
                    return f"data:{content_type};base64,{base64_data}"
        except:
            pass
        return None

    @property
    def base64_signature(self):
        try:
            if self.signature:
                with open(self.signature.path, 'rb') as image_file:
                    base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                    extension = os.path.splitext(self.signature.name)[1]
                    content_type = f'image/{extension.lstrip(".")}'
                    return f"data:{content_type};base64,{base64_data}"
        except:
            pass
        return None

    def get_image(self):
        if self.image:
            return f'{settings.MEDIA_URL}{self.image}'
        return f'{settings.STATIC_URL}img/default/logo.png'

    def get_signature(self):
        if self.signature:
            return f'{settings.MEDIA_URL}{self.signature}'
        return f'{settings.STATIC_URL}img/default/firma.png'

    def as_dict(self):
        item = model_to_dict(self)
        return item

    class Meta:
        verbose_name = 'Compañia'
        verbose_name_plural = 'Compañias'
        default_permissions = ()
        permissions = (
            ('change_company', 'Can change Compañia'),
        )


class Area(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text='Ingrese un nombre', verbose_name='Nombre')

    def __str__(self):
        return self.name

    def as_dict(self):
        item = model_to_dict(self)
        return item

    class Meta:
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'


class Position(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text='Ingrese un nombre', verbose_name='Nombre')

    def __str__(self):
        return self.name

    def as_dict(self):
        item = model_to_dict(self)
        return item

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'


class Employee(models.Model):
    code = models.CharField(max_length=5, unique=True, help_text='Ingrese un código', verbose_name='Código')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=13, unique=True, help_text='Ingrese un número de documento', verbose_name='Número de documento')
    hiring_date = models.DateField(default=datetime.now, verbose_name='Fecha de antiguedad')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, verbose_name='Cargo')
    area = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name='Area')
    remuneration = models.FloatField(default=0.00, verbose_name='Remuneración')

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f'{self.user.names} / {self.dni}'

    def get_amount_of_assists(self, year, month):
        return self.assistancedetail_set.filter(assistance__date_joined__year=year, assistance__date_joined__month=month, active=True).count()

    def formatted_hiring_date(self):
        return self.hiring_date.strftime('%Y-%m-%d')

    def as_dict(self):
        item = model_to_dict(self)
        item['text'] = self.get_full_name()
        item['user'] = self.user.as_dict()
        item['hiring_date'] = self.hiring_date.strftime('%Y-%m-%d')
        item['position'] = self.position.as_dict()
        item['area'] = self.area.as_dict()
        item['remuneration'] = float(self.remuneration)
        return item

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'


class Heading(models.Model):
    name = models.CharField(max_length=200, help_text='Ingrese un nombre', verbose_name='Nombre')
    code = models.CharField(max_length=30, unique=True, help_text='Ingrese una referencia', verbose_name='Referencia')
    item_type = models.CharField(max_length=15, choices=ITEM_TYPE, default='haberes', verbose_name='Tipo')
    active = models.BooleanField(default=True, verbose_name='Estado')
    order = models.IntegerField(default=0, verbose_name='Posición')
    has_quantity = models.BooleanField(default=False, verbose_name='¿Posee cantidad?')

    def __str__(self):
        return self.name

    @property
    def number(self):
        return f'{self.id:04d}'

    def as_dict(self):
        item = model_to_dict(self)
        item['item_type'] = {'id': self.item_type, 'name': self.get_item_type_display()}
        return item

    def get_amount_detail_salary(self, employee, year, month):
        return self.salaryheading_set.filter(salary_detail__employee_id=employee, salary_detail__salary__year=year, salary_detail__salary__month=month).first()

    def convert_name_to_code(self):
        excludes = [' ', '.', '%']
        code = self.name.lower()
        for i in excludes:
            code = code.replace(i, '_')
        if code[-1] == '_':
            code = code[0:-1]
        return code

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.code = self.convert_name_to_code()
        super(Heading, self).save()

    class Meta:
        verbose_name = 'Rubro'
        verbose_name_plural = 'Rubros'


class Salary(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Compañia')
    payment_date = models.DateField(default=datetime.now, verbose_name='Fecha de pago')
    year = models.IntegerField(verbose_name='Año')
    month = models.IntegerField(choices=MONTHS, default=0, verbose_name='Mes')

    def __str__(self):
        return self.payment_date.strftime('%Y-%m-%d')

    def as_dict(self):
        item = model_to_dict(self, exclude=['compa'])
        item['payment_date'] = self.payment_date.strftime('%Y-%m-%d')
        item['month'] = {'id': self.month, 'name': self.get_month_display()}
        return item

    class Meta:
        verbose_name = 'Salario'
        verbose_name_plural = 'Salarios'
        default_permissions = ()
        permissions = (
            ('view_salary_admin', 'Can view Salario'),
            ('add_salary_admin', 'Can add Salario'),
            ('change_salary_admin', 'Can change Salario'),
            ('delete_salary_admin', 'Can delete Salario'),
            ('print_salary', 'Can print Salario'),
            ('view_salary_employee', 'Can view Salario | Employee'),
        )


class SalaryDetail(models.Model):
    salary = models.ForeignKey(Salary, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name='Empleado')
    income = models.FloatField(default=0.00)
    expenses = models.FloatField(default=0.00)
    total_amount = models.FloatField(default=0.00)

    def __str__(self):
        return self.employee.user.names

    def send_salary_email(self):
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = f'Rol de pago del mes de {self.salary.get_month_display()} del año {self.salary.year}'
            message['From'] = settings.EMAIL_HOST
            message['To'] = self.employee.user.email
            content = f'Estimado(a)\n\n{self.employee.user.names.upper()}\n\n'
            content += f'Se le ha enviado el rol de pago correspondiente al mes de {self.salary.get_month_display()} del año {self.salary.year}.\n\n'
            part = MIMEText(content)
            message.attach(part)
            context = {
                'salary_detail': self,
                'prints': [1, 2],
                'date_joined': datetime.now().date()
            }
            pdf_file = create_pdf(context=context, template_name='salary/payroll_receipt1.html')
            part = MIMEApplication(pdf_file, _subtype='pdf')
            part.add_header('Content-Disposition', 'attachment', filename=f'{self.employee.user.names.upper().replace(" ", "_")}_{self.salary.month}_{self.salary.year}.pdf')
            message.attach(part)
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(settings.EMAIL_HOST_USER, message['To'], message.as_string())
            server.quit()
            return True
        except:
            pass
        return False

    def get_income(self):
        return self.salaryheading_set.filter(heading__item_type='haberes', amount__gt=0).order_by('heading__order')

    def get_expenses(self):
        return self.salaryheading_set.filter(heading__item_type='descuentos', amount__gt=0).order_by('heading__order')

    def formatted_income(self):
        return float(self.income)

    def formatted_expenses(self):
        return float(self.expenses)

    def formatted_total_amount(self):
        return float(self.total_amount)

    def as_dict(self):
        item = model_to_dict(self)
        item['salary'] = self.salary.as_dict()
        item['employee'] = self.employee.as_dict()
        item['income'] = self.formatted_income()
        item['expenses'] = self.formatted_expenses()
        item['total_amount'] = self.formatted_total_amount()
        return item

    class Meta:
        verbose_name = 'Salario Detalle'
        verbose_name_plural = 'Salario Detalles'
        default_permissions = ()


class SalaryHeading(models.Model):
    salary_detail = models.ForeignKey(SalaryDetail, on_delete=models.CASCADE)
    heading = models.ForeignKey(Heading, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0)
    amount = models.FloatField(default=0.00)

    def __str__(self):
        return self.salary_detail.employee.user.names

    def get_quantity(self):
        if self.heading.has_quantity:
            return self.quantity
        return '0'

    def formatted_amount(self):
        return float(self.amount)

    def as_dict(self):
        item = model_to_dict(self, exclude=['salary'])
        item['amount'] = float(self.amount)
        return item

    class Meta:
        verbose_name = 'Detalle de Salario'
        verbose_name_plural = 'Detalle de Salarios'
        default_permissions = ()


class Assistance(models.Model):
    date_joined = models.DateField(default=datetime.now, verbose_name='Fecha de asistencia')
    year = models.IntegerField()
    month = models.IntegerField(choices=MONTHS, default=0)
    day = models.IntegerField()

    def __str__(self):
        return self.get_month_display()

    def formatted_date_joined(self):
        return self.date_joined.strftime('%Y-%m-%d')

    def as_dict(self):
        item = model_to_dict(self, exclude=['history'])
        item['date_joined'] = self.formatted_date_joined()
        item['month'] = {'id': self.month, 'name': self.get_month_display()}
        return item

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        default_permissions = ()
        permissions = (
            ('view_assistance_admin', 'Can view Asistencia'),
            ('add_assistance_admin', 'Can add Asistencia'),
            ('change_assistance_admin', 'Can change Asistencia'),
            ('delete_assistance_admin', 'Can delete Asistencia'),
            ('view_assistance_employee', 'Can view Asistencia | Empleado'),
        )


class AssistanceDetail(models.Model):
    assistance = models.ForeignKey(Assistance, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Empleado')
    description = models.CharField(max_length=500, null=True, blank=True, help_text='Ingrese una descripción', verbose_name='Descripción')
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.employee.get_full_name()

    def as_dict(self):
        item = model_to_dict(self)
        item['assistance'] = self.assistance.as_dict()
        item['employee'] = self.employee.as_dict()
        return item

    class Meta:
        verbose_name = 'Detalle de Asistencia'
        verbose_name_plural = 'Detalles de Asistencias'
        default_permissions = ()
