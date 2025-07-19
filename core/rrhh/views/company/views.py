import json

from django.http import HttpResponse
from django.views.generic import UpdateView

from config import settings
from core.rrhh.forms import CompanyForm, Company
from core.security.mixins import GroupPermissionMixin


class CompanyUpdateView(GroupPermissionMixin, UpdateView):
    model = Company
    template_name = 'company/create.html'
    form_class = CompanyForm
    permission_required = 'change_company'
    success_url = settings.LOGIN_REDIRECT_URL

    def get_object(self, queryset=None):
        return Company.objects.first() or Company()

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST['action']
        try:
            if action == 'create_or_edit':
                instance = self.get_object()
                if instance.pk:
                    form = CompanyForm(request.POST, request.FILES, instance=instance)
                else:
                    form = CompanyForm(request.POST, request.FILES)
                data = form.save()
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['title'] = f'Configuración de la {self.model._meta.verbose_name}'
        context['list_url'] = self.success_url
        context['action'] = 'create_or_edit'
        return context
