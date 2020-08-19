from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import AssetForm, Asset, PromotionUpdateForm
from .models import PromotionVideo


@login_required
def update_asset(request, asset_id):
  asset = Asset.objects.get(asset_id=asset_id)
  form = AssetForm(instance=asset)
  if request.method == 'POST':
    form = AssetForm(request.POST, instance=asset)
    if form.is_valid():
      form.save()
      return redirect('asset', mode='office', asset_group_id='all')
  context = {'form': form, 'asset': asset, 'asset_id': asset_id}
  return render(request, 'form/update_asset.html', context)


@login_required
def update_promovid(request, asset_id):
  promo_vid = PromotionVideo.objects.get(asset_id=asset_id)
  form = PromotionUpdateForm(instance=promo_vid)
  if request.method == 'POST':
    form = PromotionUpdateForm(request.POST, instance=promo_vid)
    if form.is_valid():
      form.save()
      return redirect('promotion')
  context = {'form': form}
  return render(request, 'form/update_asset.html', context)
