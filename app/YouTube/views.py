from .clients import *
from .views_general import *
from .views_update import *
from .views_payment_history import *
from .views_add import *
from .views_asset_categorize import *
from .views_dashboard import *
from .views_payment_export import *
from .export_all import *
from .custom_leeway import *
from .custom_ene import *
from .custom_kdigital import *
from .custom_onlyone import *

@login_required
def test_client(request):
  kor = Client.objects.filter(office='KR')
  for k_client in kor:
    k_channels = Channel.objects.filter(client=k_client)
    for k_channel in k_channels:
      ag_name = (k_client.client_name + ' - ' + k_channel.channel_name)
      Asset.objects.filter(asset_channel_id=k_channel.channel_id).update(asset_group_id=AssetGroup.objects.get(group_name=ag_name).id, office='KR')
  return redirect('home')


@login_required
def client_info(request, client_id):
  a = Client.objects.get(id=client_id)
  managers = a.manager.all()
  asset_groups = a.assetgroup_set.all()
  channels = a.channel_set.all()
  context = {
    'client': a,
    'managers': managers,
    'asset_groups': asset_groups,
    'channels': channels
  }
  return render(request, "client_info.html", context)


@login_required
def asset_groups(request):
  asset_group = AssetGroup.objects.all()
  # paginator = Paginator(asset_group, 25)
  # page = request.GET.get('page')
  # asset_groups = paginator.get_page(page)
  context = {"asset_groups": asset_group}
  return render(request, "asset/asset_groups.html", context)


@login_required
def ag_asset_list(request, asset_group_id):
  asset = Asset.objects.filter(asset_group=asset_group_id)
  asset_group = AssetGroup.objects.get(id=asset_group_id)
  paginator = Paginator(asset, 25)
  page = request.GET.get('page')
  assets = paginator.get_page(page)
  context = {"assets": assets, 'asset_group_id': asset_group_id, "asset_group": asset_group}
  return render(request, "asset/asset_list.html", context)


@login_required
@csrf_exempt
def office_asset(request, office):
  search = 1
  if request.method == "GET":
    if office == 'UD':
      office = None
    asset = Asset.objects.filter(Q(office=office) & Q(asset_group_id=None) & Q(asset_type__in=["Sound Recording", "Art Track"]))
  if request.method == "POST":
    search = request.POST['search']
    if office == 'UD':
      asset = Asset.objects.filter(
        Q(office=None) & Q(asset_id__contains=search) | Q(asset_title__contains=search) | Q(asset_labels__contains=search) | Q(
          asset_type__contains=search) | Q(artist__contains=search))
    else:
      asset = Asset.objects.filter(Q(office=office) & Q(asset_id__contains=search))
  paginator = Paginator(asset, 25)
  page = request.GET.get('page')
  assets = paginator.get_page(page)
  context = {"assets": assets, "search": search}
  return render(request, "asset/asset_list.html", context)
