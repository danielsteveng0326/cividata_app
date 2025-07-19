import json
import os
import random
import string
from datetime import date
from os.path import basename

import django
from django.core.files import File
from django.core.management import BaseCommand

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import Group
from core.rrhh.models import *


class Command(BaseCommand):
    help = 'It allows me to insert test data into the software'

    def load_json_from_file(self, file):
        with open(f'{settings.BASE_DIR}/deploy/json/{file}', encoding='utf-8', mode='r') as wr:
            return json.loads(wr.read())

    def handle(self, *args, **options):
        company = Company.objects.create(
            name='TechNova Corp.',
            ruc='0934567891002',
            address='Av. Central, Edificio Innovate, Piso 3',
            mobile='0987654321',
            phone='3045678',
            email='contact@technova.com',
            website='https://technova.io',
            description='TechNova se dedica a brindar soluciones tecnológicas innovadoras para empresas, enfocándose en optimizar procesos y mejorar la eficiencia operativa mediante software de última generación'
        )
        image_path = f'{settings.BASE_DIR}{settings.STATIC_URL}img/default/logo.png'
        company.image.save(basename(image_path), content=File(open(image_path, 'rb')), save=False)
        signature_path = f'{settings.BASE_DIR}{settings.STATIC_URL}img/default/firma.jpeg'
        company.signature.save(basename(signature_path), content=File(open(signature_path, 'rb')), save=False)
        company.save()

        for area_json in self.load_json_from_file(file='area.json'):
            Area.objects.create(**area_json)

        for position_json in self.load_json_from_file(file='position.json'):
            Position.objects.create(**position_json)

        numbers = list(string.digits)
        area_id = list(Area.objects.values_list('id', flat=True))
        position_id = list(Position.objects.values_list('id', flat=True))

        for item in self.load_json_from_file(file='employee.json')[0:20]:
            dni = ''.join(random.choices(numbers, k=10))
            user = User.objects.create(username=dni, email=item['email'], names=f"{item['first']} {item['last']}")
            user.set_password(dni)
            user.save()
            user.groups.add(Group.objects.get(pk=settings.GROUPS['employee']))
            employee = Employee.objects.create(
                user=user,
                dni=dni,
                code=''.join(random.choices(numbers, k=5)),
                hiring_date=date(random.randint(1969, 2006), random.randint(1, 12), random.randint(1, 28)),
                position_id=random.choice(position_id),
                area_id=random.choice(area_id),
                remuneration=random.randint(450, 1200)
            )
            print(f'record inserted employee {employee.id}')

        for heading_json in self.load_json_from_file(file='heading.json'):
            Heading.objects.create(**heading_json)

        current_date = datetime.now().date()
        number_list = [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1]

        for day in range(1, 30):
            date_joined = datetime(current_date.year, current_date.month, day)
            assistance = Assistance.objects.create(year=current_date.year, month=current_date.month, day=day, date_joined=date_joined)
            active_employees = Employee.objects.filter(user__is_active=True)
            AssistanceDetail.objects.bulk_create([
                AssistanceDetail(assistance=assistance, employee=employee, active=random.choice(number_list), description='' if random.choice(number_list) else 'No asistió al trabajo')
                for employee in active_employees
            ])
