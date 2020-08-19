from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Asset
from .models import AssetGroup


@login_required
@csrf_exempt
def categorize(request, mode, asset_group_id):
  if request.method == "POST":
    thing = request.POST.getlist('asset_id')
    for asset_id in thing:
      asset = Asset.objects.get(asset_id=asset_id)
      if 'office' in request.POST.keys():
        asset.office = request.POST['office']
      if 'asset_group' in request.POST.keys():
        asset.asset_group_id = request.POST['asset_group']
        asset.office = AssetGroup.objects.get(id=asset_group_id).client.office
      asset.save()

  assets = Asset.objects.all()
  asset_id_query = request.GET.get('asset_id')
  asset_title_query = request.GET.get('asset_title')
  asset_channel_id_query = request.GET.get('asset_channel_id')
  asset_labels_query = request.GET.get('asset_labels')
  artist_query = request.GET.get('artist')
  album_query = request.GET.get('album')
  label_query = request.GET.get('label')
  office_query = request.GET.get('office')
  asset_group_assigned_query = request.GET.get('asset_group_assigned')
  inactive_asset_query = request.GET.get('inactive')
  custom_id_query = request.GET.get('custom_id')
  isrc_query = request.GET.get('isrc')
  upc_query = request.GET.get('upc')
  grid_query = request.GET.get('grid')
  asset_type_query = request.GET.get('asset_type')
  lang_filter_query = request.GET.get('lang')

  if asset_group_id != 'all':
    ags = AssetGroup.objects.get(id=asset_group_id)
  else:
    ags = None

  if asset_id_query != '' and asset_id_query is not None:
    assets = assets.filter(asset_id__contains=asset_id_query)

  if asset_title_query != '' and asset_title_query is not None:
    assets = assets.filter(asset_title__contains=asset_title_query)

  if asset_channel_id_query != '' and asset_channel_id_query is not None:
    assets = assets.filter(asset_channel_id__contains=asset_channel_id_query)

  if asset_labels_query != '' and asset_labels_query is not None:
    assets = assets.filter(asset_labels__contains=asset_labels_query)

  if artist_query != '' and artist_query is not None:
    assets = assets.filter(artist__icontains=artist_query)

  if album_query != '' and album_query is not None:
    assets = assets.filter(album__icontains=album_query)

  if label_query != '' and label_query is not None:
    assets = assets.filter(label__icontains=label_query)

  if asset_group_assigned_query != '' and asset_group_assigned_query is not None:
    if asset_group_assigned_query == "Yes":
      assets = assets.filter(~Q(asset_group=None))
    if asset_group_assigned_query == "No":
      assets = assets.filter(Q(asset_group=None))

  if inactive_asset_query != '' and inactive_asset_query is not None:
    if inactive_asset_query == "Missing":
      assets = assets.filter(Q(asset_channel_id=None))
    if inactive_asset_query == "Not Missing":
      assets = assets.filter(~Q(asset_channel_id=None))

  kr_regex = '[가-힇]+'
  jp_regex = '[ぁ-んァ-ン]'

  if lang_filter_query != '' and lang_filter_query is not None:
    if lang_filter_query == "Korean":
      assets = assets.filter(Q(asset_title__regex=kr_regex) or Q(artist__regex=kr_regex) or Q(label__regex=kr_regex) or Q(album__regex=kr_regex))
    if lang_filter_query == "Japanese":
      assets = assets.filter(Q(asset_title__regex=jp_regex) or Q(artist__regex=jp_regex) or Q(label__regex=jp_regex) or Q(album__regex=jp_regex))

  if office_query != '' and office_query is not None:
    if office_query != 'All':
      if office_query != 'None':
        assets = assets.filter(office=office_query)
      else:
        assets = assets.filter(office=None)

  if custom_id_query != '' and custom_id_query is not None:
    assets = assets.filter(custom_id__icontains=custom_id_query)

  if isrc_query != '' and isrc_query is not None:
    assets = assets.filter(isrc__icontains=isrc_query)

  if upc_query != '' and upc_query is not None:
    assets = assets.filter(upc__icontains=upc_query)

  if grid_query != '' and grid_query is not None:
    assets = assets.filter(grid__icontains=grid_query)

  if asset_type_query != '' and asset_type_query is not None:
    if asset_type_query != "All":
      assets = assets.filter(asset_type__in=asset_type_query.split('/'))

  if not request.user.is_superuser:
    office = request.user.manager.office
    assets = assets.filter(Q(office=office) | Q(office__isnull=True) | Q(office='UN'))
  if request.GET.get('per_view'):
    paginator = Paginator(assets, request.GET.get('per_view'))
  else:
    paginator = Paginator(assets, 25)
  page = request.GET.get('page')
  p_assets = paginator.get_page(page)

  context = {
    'assets': p_assets,
    'asset_group': ags,
    'values': request.GET,
    'mode': mode
  }
  return render(request, "asset/asset_search.html", context=context)
