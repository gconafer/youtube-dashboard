"""djangosample URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
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
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from YouTube import views

urlpatterns = \
  [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', views.signin, name='login'),
    url(r'^logout/$', views.signout, name='logout'),
    path("select2/", include("django_select2.urls")),

    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('test', views.test_client),
    path('test_insert', views.insert_client),
    path('test_country', views.channel_id_country),
    path('export_all/<str:year_month>', views.all_payment_export),
    path('export_leeway/<str:year_month>/<str:client_id>', views.export_leeway, name='export_leeway'),
    path('export_ene/<str:year_month>/<str:client_id>', views.export_ene, name='export_ene'),
    path('export_kdigital/<str:year_month>/<str:client_id>', views.export_kdigital, name='export_kdigital'),

    path('dashboard/<str:ym>', views.dashboard, name='dashboard'),
    path('country-dashboard/<str:ym>', views.country_dashboard, name='country_dashboard'),

    path('promotion', views.promotions, name='promotion'),

    path('client', views.clients, name='client'),
    path('client/<int:client_id>', views.client_info, name='client_info'),

    # path('asset', views.categorize, name='asset'),
    path('asset/<str:mode>/<str:asset_group_id>', views.categorize, name='asset'),
    # path('asset/<str:mode>/<str:asset_group_id>', views.categorize, name='asset'),

    path('asset-update/<str:asset_id>', views.update_asset, name='asset_update'),
    path('promo-update/<str:asset_id>', views.update_promovid, name='promo_update'),

    path('asset-groups', views.asset_groups, name='asset_groups'),
    path('asset-groups/<int:asset_group_id>', views.ag_asset_list, name='asset_group_asset_list'),
    # path('asset-groups/<int:asset_group_id>/add', views.ag_asset_list, name='asset_group_asset_list'),

    path('payment-history/<int:client_id>/<str:year_month>', views.payment_history, name='payment_history'),
    path('payment-export/<int:client_id>/<str:year_month>', views.payment_export, name='payment_export'),

    path('assetupdate', views.success, name='asset_update'),
    path('success', views.success, name='success'),

    # path('asset_search', views.categorize),
    # path('asset/<str:office>', views.office_asset, name='office_asset'),
    path('manager', views.managers, name='manager'),

    path('add-manager', views.add_manager, name='add_manager'),
    path('add-asset-group/<int:client_id>', views.add_asset_group, name='add_asset_group'),
    path('add-channel/<int:client_id>', views.add_channel, name='add_channel'),
    path('add-client', views.client_add_form, name='add_client'),
    path('add-promotion', views.add_promotion_video, name='add_promotion'),
    path('add-asset', views.add_asset, name='add_asset'),

  ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
