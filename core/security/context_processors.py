from datetime import datetime

from core.rrhh.models import Company
from core.security.models import Dashboard


def site_settings(request):
    dashboard = Dashboard.objects.first()
    params = {
        'dashboard': dashboard,
        'date_joined': datetime.now(),
        'menu': dashboard.get_template_from_layout() if dashboard else 'hzt_body.html',
        'company': Company.objects.first(),
    }
    return params
