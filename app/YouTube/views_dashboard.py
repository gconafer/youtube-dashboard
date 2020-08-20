from time import time

import plotly.graph_objects as go
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.cache import cache
from django.db.models import Sum, F, Q
from django.shortcuts import render

from .models import AssetRevenueView, Client, AssetGroup, Asset, Manager


@login_required
@user_passes_test(lambda u: u.is_superuser)
def dashboard(request, ym):
  # Month Revenue
  starttime = time()
  year_month = AssetRevenueView.objects.order_by().values('year_month').distinct().values_list('year_month', flat=True)
  year_month = list(year_month)

  ch_asset = Asset.objects.filter(asset_type__in=['Web', 'Music Video', 'Movie', 'Television Episode'])
  sr_asset = Asset.objects.filter(asset_type='Sound Recording')
  at_asset = Asset.objects.filter(asset_type='Art Track')

  ch_revenue = list(AssetRevenueView.objects.filter(asset__in=ch_asset, manual_claimed=False, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  sr_revenue = list(AssetRevenueView.objects.filter(asset__in=sr_asset, manual_claimed=False, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  at_revenue = list(AssetRevenueView.objects.filter(asset__in=at_asset, manual_claimed=False, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  mc_revenue = list(AssetRevenueView.objects.filter(manual_claimed=True, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  pm_revenue = list(AssetRevenueView.objects.filter(manual_claimed=False, promotion=True).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))

  print(time() - starttime)

  fig = go.Figure(data=[
    go.Bar(name='Channel', x=year_month, y=ch_revenue),
    go.Bar(name='Sound Recording', x=year_month, y=sr_revenue),
    go.Bar(name='Art Track', x=year_month, y=at_revenue),
    go.Bar(name='Manual Claiming', x=year_month, y=mc_revenue),
    go.Bar(name='Promotion', x=year_month, y=pm_revenue),
  ])
  fig.update_layout(barmode='stack')
  monthly_json = fig.to_json()

  # Client Revenue
  rev = AssetRevenueView.objects.filter(year_month=ym).values('asset__asset_group__client__client_name').annotate(
    partner_revenue=Sum('partner_revenue'), client=F('asset__asset_group__client__client_name'))
  labels = [r['asset__asset_group__client__client_name'] for r in rev]
  values = [r['partner_revenue'] for r in rev]

  fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label',
                               insidetextorientation='radial', textposition='inside')])
  revenue_json = fig.to_json()

  print(time() - starttime)

  # Client Profit
  profit_labels = cache.get(f'{ym}_profit_labels')
  profit_values = cache.get(f'{ym}_profit_values')
  if profit_labels == None or profit_values == None:
    clients = Client.objects.filter(~Q(client_name='프로모션채널'))
    profit = {}
    for client in clients:
      profit[client.client_name] = 0
      for ag in AssetGroup.objects.filter(client=client):
        if ag.asset_type == "sr":
          split = client.sr_split
        elif ag.asset_type == "ch":
          split = client.channel_split
        elif ag.asset_type == "at":
          split = client.at_split
        revs = AssetRevenueView.objects.filter(asset__asset_id__in=Asset.objects.filter(asset_group=ag), manual_claimed=False, promotion=False, year_month=ym)
        if len(revs) > 0:
          profit[client.client_name] += (1 - float(split)) * revs.aggregate(Sum('partner_revenue'))['partner_revenue__sum']
      mc_revs = AssetRevenueView.objects.filter(asset__asset_id__in=Asset.objects.filter(asset_group__in=AssetGroup.objects.filter(client=client)), manual_claimed=True, promotion=False, year_month=ym)
      if len(mc_revs) > 0:
        profit[client.client_name] += mc_revs.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(1 - client.mc_split)
      promo_revs = AssetRevenueView.objects.filter(asset__asset_id__in=Asset.objects.filter(asset_group__in=AssetGroup.objects.filter(client=client)), manual_claimed=False, promotion=True,
                                                   year_month=ym)
      if len(promo_revs) > 0:
        profit[client.client_name] += promo_revs.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * 0.6
    labels = list(profit.keys())
    values = list(profit.values())
    profit_values = values
    cache.set(f'{ym}_profit_labels', labels)
    cache.set(f'{ym}_profit_values', values)
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label',
                                 insidetextorientation='radial', textposition='inside')])
  else:
    fig = go.Figure(data=[go.Pie(labels=profit_labels, values=profit_values, textinfo='percent+label',
                                 insidetextorientation='radial', textposition='inside')])
  profit_json = fig.to_json()
  print(time() - starttime)

  # Revenue by Office
  rev = AssetRevenueView.objects.filter(year_month=ym).values('asset__office').annotate(
    partner_revenue=Sum('partner_revenue'), client=F('asset__office'))
  labels = [r['asset__office'] for r in rev]
  values = [r['partner_revenue'] for r in rev]

  fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='label+percent',
                               insidetextorientation='radial', textposition='inside')])
  by_office = fig.to_json()
  print(time() - starttime)

  music_month_reveue = AssetRevenueView.objects.filter(year_month=ym, cms='Music').aggregate(Sum('partner_revenue'))['partner_revenue__sum']
  non_music_month_reveue = AssetRevenueView.objects.filter(Q(year_month=ym) and ~Q(cms='Music')).aggregate(Sum('partner_revenue'))['partner_revenue__sum']

  context = {
    'client_revenue': revenue_json,
    'client_profit': profit_json,
    'by_office': by_office,
    'monthly': monthly_json,
    'ym': ym,
    'month_profit': sum(profit_values),
    'music_month_reveue': music_month_reveue,
    'non_music_month_reveue': non_music_month_reveue,
    'dashboard_type': 'admin'
  }
  return render(request, "dashboard.html", context)


@staff_member_required
@login_required
def country_dashboard(request, ym):
  country = Manager.objects.get(user_id=request.user.id).office
  # Month Revenue
  starttime = time()
  year_month = AssetRevenueView.objects.order_by().values('year_month').distinct().values_list('year_month', flat=True)
  year_month = list(year_month)

  country_asset = Asset.objects.filter(office=country)

  ch_asset = country_asset.filter(asset_type__in=['Web', 'Music Video', 'Movie', 'Television Episode'])
  sr_asset = country_asset.filter(asset_type='Sound Recording')
  at_asset = country_asset.filter(asset_type='Art Track')

  ch_revenue = list(AssetRevenueView.objects.filter(asset__in=ch_asset, manual_claimed=False, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  sr_revenue = list(AssetRevenueView.objects.filter(asset__in=sr_asset, manual_claimed=False, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  at_revenue = list(AssetRevenueView.objects.filter(asset__in=at_asset, manual_claimed=False, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  mc_revenue = list(AssetRevenueView.objects.filter(manual_claimed=True, promotion=False).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))
  pm_revenue = list(AssetRevenueView.objects.filter(manual_claimed=False, promotion=True).values('year_month').annotate(
    partner_revenue=Sum('partner_revenue')).values_list('partner_revenue', flat=True))

  print(time() - starttime)

  fig = go.Figure(data=[
    go.Bar(name='Channel', x=year_month, y=ch_revenue),
    go.Bar(name='Sound Recording', x=year_month, y=sr_revenue),
    go.Bar(name='Art Track', x=year_month, y=at_revenue),
    go.Bar(name='Manual Claiming', x=year_month, y=mc_revenue),
    go.Bar(name='Promotion', x=year_month, y=pm_revenue),
  ])
  fig.update_layout(barmode='stack')
  monthly_json = fig.to_json()

  # Client Revenue
  country_revenue = AssetRevenueView.objects.filter(asset_id__in=country_asset)
  rev = country_revenue.filter(year_month=ym).values('asset__asset_group__client__client_name').annotate(
    partner_revenue=Sum('partner_revenue'), client=F('asset__asset_group__client__client_name'))
  labels = [r['asset__asset_group__client__client_name'] for r in rev]
  values = [r['partner_revenue'] for r in rev]

  fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label',
                               insidetextorientation='radial', textposition='inside')])
  revenue_json = fig.to_json()

  print(time() - starttime)

  # Client Profit
  profit_labels = cache.get(f'{country}_{ym}_profit_labels')
  profit_values = cache.get(f'{country}_{ym}_profit_values')
  country_client = Client.objects.filter(office=country)
  if profit_labels == None or profit_values == None:
    clients = country_client.filter(~Q(client_name='프로모션채널'))
    profit = {}
    for client in clients:
      profit[client.client_name] = 0
      for ag in AssetGroup.objects.filter(client=client):
        if ag.asset_type == "sr":
          split = client.sr_split
        elif ag.asset_type == "ch":
          split = client.channel_split
        elif ag.asset_type == "at":
          split = client.at_split
        revs = country_revenue.filter(asset__asset_id__in=Asset.objects.filter(asset_group=ag), manual_claimed=False, promotion=False, year_month=ym)
        if len(revs) > 0:
          profit[client.client_name] += (1 - float(split)) * revs.aggregate(Sum('partner_revenue'))['partner_revenue__sum']
      mc_revs = country_revenue.filter(asset__asset_id__in=Asset.objects.filter(asset_group__in=AssetGroup.objects.filter(client=client)), manual_claimed=True, promotion=False, year_month=ym)
      if len(mc_revs) > 0:
        profit[client.client_name] += mc_revs.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(1 - client.mc_split)
      promo_revs = country_revenue.filter(asset__asset_id__in=Asset.objects.filter(asset_group__in=AssetGroup.objects.filter(client=client)), manual_claimed=False, promotion=True,
                                                   year_month=ym)
      if len(promo_revs) > 0:
        profit[client.client_name] += promo_revs.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * 0.6
    labels = list(profit.keys())
    values = list(profit.values())
    profit_values = values
    cache.set(f'{country}_{ym}_profit_labels', labels)
    cache.set(f'{country}_{ym}_profit_values', values)
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label',
                                 insidetextorientation='radial', textposition='inside')])
  else:
    fig = go.Figure(data=[go.Pie(labels=profit_labels, values=profit_values, textinfo='percent+label',
                                 insidetextorientation='radial', textposition='inside')])
  profit_json = fig.to_json()
  print(time() - starttime)

  # Revenue by Office
  rev = AssetRevenueView.objects.filter(year_month=ym).values('asset__office').annotate(
    partner_revenue=Sum('partner_revenue'), client=F('asset__office'))
  labels = [r['asset__office'] for r in rev]
  values = [r['partner_revenue'] for r in rev]

  fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='label+percent',
                               insidetextorientation='radial', textposition='inside')])
  by_office = fig.to_json()
  print(time() - starttime)

  music_month_reveue = country_revenue.filter(year_month=ym, cms='Music').aggregate(Sum('partner_revenue'))['partner_revenue__sum']
  non_music_month_reveue = country_revenue.filter(Q(year_month=ym) and ~Q(cms='Music')).aggregate(Sum('partner_revenue'))['partner_revenue__sum']

  context = {
    'client_revenue': revenue_json,
    'client_profit': profit_json,
    'by_office': by_office,
    'monthly': monthly_json,
    'ym': ym,
    'month_profit': sum(profit_values),
    'music_month_reveue': music_month_reveue,
    'non_music_month_reveue': non_music_month_reveue,
    'dashboard_type': 'staff'
  }
  return render(request, "dashboard.html", context)
