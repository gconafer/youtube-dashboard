from django.shortcuts import redirect
import pygsheets
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Client, Manager, Asset, AssetGroup, Channel


def replace(num):
  if num == 0:
    return 1.0
  else:
    return float(num.replace('%', '')) / 100


@login_required
def insert_client(request):
  gc = pygsheets.authorize(service_account_file='service_account.json')
  label_info = gc.open_by_key('1nPpgrHqsO0H_GMNrVhiCrRHiua6gZyZhkBs6RRW4j18')
  client_info = label_info[3].get_all_records()
  channel_info = label_info[0].get_all_records()

  for client in client_info:
    new_client = Client()
    new_client.client_name = client['Name']
    new_client.email = client['Email']
    new_client.payment_method = client['Payment Method']
    new_client.channel_split = replace(client['Channel %'])
    new_client.sr_split = replace(client['SR %'])
    new_client.at_split = replace(client['AT %'])
    new_client.mc_split = replace(client['MC %'])
    new_client.office = 'KR'
    new_client.save()
    new_client.manager.add(Manager.objects.get(user_id=2))

  for client in channel_info:
    if client['channel_id'] != 'n/a':
      this_client = Client.objects.get(client_name=client['client'])
      # Add New Channel
      new_channel = Channel()
      new_channel.channel_name = client['channel_name']
      new_channel.channel_id = client['channel_id']
      new_channel.client = this_client
      new_channel.save()

      # Add New Asset Group
      new_asset_group = AssetGroup()
      new_asset_group.group_name = this_client.client_name + ' - ' + client['channel_name']
      new_asset_group.asset_type = 'ch'
      new_asset_group.client = this_client
      new_asset_group.save()

      # Add Asset to Asset Group
      assets = Asset.objects.filter(asset_channel_id=client['channel_id'])
      assets.update(office='KR', asset_group_id=new_asset_group.id)

  return redirect('home')


@login_required
def channel_id_country(request):
  gc = pygsheets.authorize(service_account_file='service_account.json')
  label_info = gc.open_by_key('1nPpgrHqsO0H_GMNrVhiCrRHiua6gZyZhkBs6RRW4j18')
  channel_country = label_info[7].get_all_records()
  for ch in channel_country:
    assets = Asset.objects.filter(asset_channel_id=ch['channel_id'])
    assets.update(office=ch['office'])
  return redirect('home')
