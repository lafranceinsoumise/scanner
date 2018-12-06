"""fi_scanner_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from registrations import viewsets
from .metrics import get_metrics
from registrations.views import CodeView


router = routers.DefaultRouter()
router.register(r"registrations", viewsets.RegistrationViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("code/<code>/", csrf_exempt(CodeView.as_view()), name="view_code"),
    path("metrics/", get_metrics),
    path("api/", include(router.urls)),
]
