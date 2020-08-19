from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import ClientAddForm, ChannelAddForm, AssetGroupAddForm, ManagerSignUpForm, PromotionAddForm, AddAssetForm
from .models import Client, Asset, AssetGroup


@staff_member_required
@login_required
def client_add_form(request):
  form = ClientAddForm()
  if request.method == 'POST':
    form = ClientAddForm(request.POST)
    if form.is_valid():
      new_client = form.save()
      return redirect('client_info', new_client.pk)
  context = {'form': form}
  return render(request, 'form/add_account.html', context)


@login_required
def add_channel(request, client_id):
  form = ChannelAddForm(initial={'client': client_id})
  client = Client.objects.get(id=client_id)
  if request.method == 'POST':
    form = ChannelAddForm(request.POST)
    if form.is_valid():
      form.save()
      channel_ag = AssetGroup()
      channel_ag.client = Client.objects.get(id=client_id)
      channel_ag.asset_type = 'ch'
      channel_ag.group_name = form.cleaned_data['client'].client_name + ' - ' + form.cleaned_data['channel_name']
      channel_ag.save()
      Asset.objects.filter(asset_channel_id=form.cleaned_data['channel_id']).update(asset_group_id=channel_ag.id, office=client.office)
      return redirect('client_info', client_id)
  context = {'form': form, 'client': client, 'client_id': client_id}
  return render(request, 'form/add_form.html', context)


@login_required
def add_asset_group(request, client_id):
  client = Client.objects.get(id=client_id)
  form = AssetGroupAddForm(initial={'client': client_id, 'group_name': client.client_name + ' - '})
  if request.method == 'POST':
    form = AssetGroupAddForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('client_info', client_id)
  context = {'form': form, 'client': client, 'client_id': client_id}
  return render(request, 'form/add_form.html', context)


@staff_member_required
@login_required
def add_manager(request):
  form = ManagerSignUpForm()
  if request.method == 'POST':
    form = ManagerSignUpForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('manager')
  context = {'form': form}
  return render(request, 'form/add_account.html', context)


@login_required
def add_promotion_video(request):
  form = PromotionAddForm()
  if request.method == 'POST':
    form = PromotionAddForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('add_promotion')
  context = {'form': form}
  return render(request, 'form/add_promotion.html', context)


@login_required
def add_asset(request):
  form = AddAssetForm()
  if request.method == 'POST':
    form = AddAssetForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('asset')
  context = {'form': form}
  return render(request, 'form/add_asset.html', context)
