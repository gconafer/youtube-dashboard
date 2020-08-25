import gspread
import pandas as pd
import pygsheets
from django.db import connections
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import redirect
from oauth2client.service_account import ServiceAccountCredentials

from .models import Client, Asset, AssetGroup, AssetRevenueView


def asset_title_left(revenues, batch_update_request, ws, ag):
  if ag != "mc":
    revenue_list = revenues[ag]
  else:
    revenue_list = revenues
  batch_update_request['requests'].append({
    "repeatCell": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2,
        "endRowIndex": 4 + len(revenue_list),
        "startColumnIndex": 1,
        "endColumnIndex": 2
      },
      "cell": {
        "userEnteredFormat": {
          "numberFormat": {"type": "TEXT"},
          "horizontalAlignment": "LEFT",
        }
      },
      "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
    }
  })
  return batch_update_request


def bottom_merge(revenues, batch_update_request, ws, ag):
  if ag != "mc":
    revenue_list = revenues[ag]
  else:
    revenue_list = revenues
  batch_update_request['requests'].append({
    "mergeCells": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2 + len(revenue_list),
        "endRowIndex": 4 + len(revenue_list),
        "startColumnIndex": 1,
        "endColumnIndex": 2
      },
      "mergeType": "MERGE_ROWS"
    }
  })
  return batch_update_request


def bottom_color(revenues, batch_update_request, ws, ag):
  if ag != "mc":
    revenue_list = revenues[ag]
  else:
    revenue_list = revenues
  batch_update_request['requests'].append({
    "repeatCell": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2 + len(revenue_list),
        "endRowIndex": 3 + len(revenue_list),
        "startColumnIndex": 0,
        "endColumnIndex": 3
      },
      "cell": {
        "userEnteredFormat": {
          # Grey
          "backgroundColor": {"red": 0.8509804, "green": 0.8509804, "blue": 0.8509804},
          "horizontalAlignment": "CENTER",
          "textFormat": {"bold": True}
        }
      },
      "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }
  })
  batch_update_request['requests'].append({
    "repeatCell": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 3 + len(revenue_list),
        "endRowIndex": 4 + len(revenue_list),
        "startColumnIndex": 0,
        "endColumnIndex": 3
      },
      "cell": {
        "userEnteredFormat": {
          # Sky Blue
          "backgroundColor": {"red": 0.8117647, "green": 0.8862745, "blue": 0.9529412},
          "horizontalAlignment": "CENTER",
          "textFormat": {"bold": True}
        }
      },
      "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }
  })
  return batch_update_request


def add_border(revenues, batch_update_request, ws, ag):
  if ag != "mc":
    revenue_list = revenues[ag]
  else:
    revenue_list = revenues
  batch_update_request['requests'].append({
    "updateBorders": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 0,
        "endRowIndex": 4 + len(revenue_list),
        "startColumnIndex": 0,
        "endColumnIndex": 3
      },
      "top": {"style": "SOLID", },
      "bottom": {"style": "SOLID", },
      "innerHorizontal": {"style": "SOLID", },
      "innerVertical": {"style": "SOLID"},
      "left": {"style": "SOLID"},
      "right": {"style": "SOLID"}
    }
  })
  return batch_update_request


def format_currency(revenues, batch_update_request, ws, ag):
  if ag != "mc":
    revenue_list = revenues[ag]
  else:
    revenue_list = revenues
  batch_update_request['requests'].append({
    "repeatCell": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2,
        "endRowIndex": 4 + len(revenue_list),
        "startColumnIndex": 2,
        "endColumnIndex": 3
      },
      "cell": {
        "userEnteredFormat": {
          "numberFormat": {"type": "CURRENCY"},
          "horizontalAlignment": "RIGHT",
        }
      },
      "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
    }
  })
  return batch_update_request


def export_ene(request, year_month, client_id):
  scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
  credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
  gc = gspread.authorize(credentials)

  client = Client.objects.get(id=client_id)
  asset_groups = AssetGroup.objects.filter(client=client)
  # ch_groups = asset_groups.filter(asset_type='ch')
  at_groups = asset_groups.filter(asset_type='at')
  sr_groups = asset_groups.filter(asset_type='sr')

  mc_revenues = []
  # ch_revenues = {}
  at_revenues = {}
  sr_revenues = {}

  # Art Track Assets to List
  if len(at_groups) > 0:
    for ag in at_groups:
      rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
      if len(rev) > 0:
        at_revenues[ag.group_name] = []
        rev_by_id = rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          asset_info = Asset.objects.get(asset_id=r['asset_id'])
          title = asset_info.asset_title if asset_info.asset_title else ''
          isrc = asset_info.isrc if asset_info.isrc else ''
          artist = asset_info.artist if asset_info.artist else ''
          label = asset_info.label if asset_info.label else ''
          if asset_info.upc:
            album_code = asset_info.upc
          else:
            if asset_info.grid:
              album_code = asset_info.grid
            else:
              album_code = ''
          if len(Asset.objects.filter(Q(upc=album_code) & Q(album__isnull=False))) > 0:
            album_info = Asset.objects.filter(Q(upc=album_code) & Q(album__isnull=False)).first()
            album = album_info.album
          else:
            if len(Asset.objects.filter(Q(grid=album_code) & Q(album__isnull=False))) > 0:
              album_info = Asset.objects.filter(Q(grid=album_code) & Q(album__isnull=False)).first()
              album = album_info.album
            else:
              album = ''
          r['isrc'] = '\'' + isrc
          r['artist'] = '\'' + artist
          r['album'] = '\'' + album
          r['label'] = '\'' + label
          r['asset_title'] = '\'' + title
          r['album_code'] = '\'' + album_code
          r['partner_revenue'] = r.pop('total')
          at_revenues[ag.group_name].append(r)

  # Sound Recording Assets to List
  if len(sr_groups) > 0:
    for ag in sr_groups:
      rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
      mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
      if len(rev) > 0:
        sr_revenues[ag.group_name] = []
        rev_by_id = rev.values('asset_id', 'revenue_type').annotate(total=Sum('partner_revenue')).order_by('-total')
        print(rev_by_id)
        return ''
        for r in rev_by_id:
          asset_info = Asset.objects.get(asset_id=r['asset_id'])
          title = asset_info.asset_title if asset_info.asset_title else ''
          isrc = asset_info.isrc if asset_info.isrc else ''
          artist = asset_info.artist if asset_info.artist else ''
          album = asset_info.album if asset_info.album else ''
          label = asset_info.label if asset_info.label else ''
          if asset_info.upc:
            album_code = asset_info.upc
          else:
            if asset_info.grid:
              album_code = asset_info.grid
            else:
              album_code = ''
          r['isrc'] = '\'' + isrc
          r['artist'] = '\'' + artist
          r['album'] = '\'' + album
          r['label'] = '\'' + label
          r['asset_title'] = '\'' + title
          r['album_code'] = '\'' + album_code
          r['partner_revenue'] = r.pop('total')
          sr_revenues[ag.group_name].append(r)

      with connections['default'].cursor() as cursor:
        cursor.execute(f"""
          select ic.asset_id as asset_id, isrc, artist, upc, grid, album, label, asset_title, sum(split_revenue) * 0.4 / {client.sr_split} as partner_revenue
          from "YouTube_promotionvideo" as pmv
                   join (select *
                         from "YouTube_promotionvideo_included_asset" ic
                         where ic.asset_id in (select asset_id from "YouTube_asset" where asset_group_id = {ag.id})) as ic
                        on pmv.video_id = ic.promotionvideo_id
                   join (
              select asset_id, sum / count as split_revenue
              from (
                       select asset_id, count
                       from "YouTube_promotionvideo" as pm
                                join (select promotionvideo_id, count(asset_id) as count
                                      from "YouTube_promotionvideo_included_asset"
                                      group by promotionvideo_id) as ic on pm.video_id = ic.promotionvideo_id) a
                       join (select asset_id, sum(partner_revenue)
                             from "YouTube_assetrevenueview"
                             where promotion = True
                               and year_month = '{year_month}'
                             group by asset_id) b using (asset_id)) c
                        on pmv.asset_id = c.asset_id
                   join "YouTube_asset" YTa on ic.asset_id = YTa.asset_id
          group by ic.asset_id, isrc, artist, upc, grid, album, label, asset_title
          order by partner_revenue desc;
        """)
        for promo_rev in cursor.fetchall():
          title = promo_rev[7] if title else ''
          if promo_rev[2]:
            album_code = promo_rev[2]
          else:
            if promo_rev[3]:
              album_code = promo_rev[3]
            else:
              album_code = ''
          tmp = {
            'asset_id': promo_rev[0],
            'isrc': promo_rev[1],
            'artist': promo_rev[2],
            'album_code': album_code,
            'album': promo_rev[5],
            'label': promo_rev[6],
            'asset_title': title, 'partner_revenue': promo_rev[8]}
          sr_revenues[ag.group_name].append(tmp)

        if len(sr_revenues) > 0:
          sr_revenues[ag.group_name] = pd.DataFrame(sr_revenues[ag.group_name]).groupby(['asset_id', 'isrc', 'artist', 'album_code', 'album', 'asset_title']).sum().reset_index().sort_values(
            by='partner_revenue', ascending=False).to_dict('records')
      if len(mc_rev) > 0:
        rev_by_id = mc_rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          asset_info = Asset.objects.get(asset_id=r['asset_id'])
          title = asset_info.asset_title if asset_info.asset_title else ''
          isrc = asset_info.isrc if asset_info.isrc else ''
          artist = asset_info.artist if asset_info.artist else ''
          album = asset_info.album if asset_info.album else ''
          label = asset_info.label if asset_info.label else ''
          if asset_info.upc:
            album_code = asset_info.upc
          else:
            if asset_info.grid:
              album_code = asset_info.grid
            else:
              album_code = ''
          r['isrc'] = '\'' + isrc
          r['artist'] = '\'' + artist
          r['album'] = '\'' + album
          r['label'] = '\'' + label
          r['asset_title'] = '\'' + title
          r['album_code'] = '\'' + album_code
          r['partner_revenue'] = r.pop('total')
          mc_revenues.append(r)
  # return ''
  # Create Spread Sheet
  pyg = pygsheets.authorize(service_account_file='service_account.json')
  sample_report_id = '16yCzOTvtc-wnbLWxhDIX7gQH6gNivn1rdbLfVMojdhU'
  folder_id = '17AdfygJ9dFcOmfib4DB9ffspW2fPbqaP'

  new_ss = pyg.drive.copy_file(file_id=sample_report_id, title=f'{year_month.split("-")[0]}년 {int(year_month.split("-")[1])}월 수익 정산서 [{client}]', folder=folder_id)
  sh = gc.open_by_key(new_ss['id'])

  # Batch Update List
  update_request = {}
  batch_update_request = {}
  batch_update_request['requests'] = []

  # Add Sound Recording Assets
  if len(sr_revenues) > 0:
    for i, ag in enumerate(sr_revenues):
      leng = len(sr_revenues[ag])
      if leng > 0:
        update_request[ag] = []
        update_request[ag].append(
          {
            'range': f'A3:G{2 + leng}',
            'values': [[
              rev['asset_id'],
              rev['isrc'],
              rev['artist'],
              rev['album_code'],
              rev['album'],
              f'{rev["asset_title"]}',
              float(rev["partner_revenue"])
            ] for rev in sr_revenues[ag]]
          }
        )
        update_request[ag].append({
          'range': f'A{3 + leng}:B{4 + leng}',
          'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
        })
        update_request[ag].append({
          'range': f'G{3 + leng}:G{4 + leng}',
          'values': [[f'=SUM(G3:G{2 + leng})'], [f'=SUM(G3:G{2 + leng})*{float(client.sr_split)}']],
        })

        ws = sh.worksheets()[2]
        insert_row_request = {'requests': [{
          "insertDimension": {
            "range": {
              "sheetId": ws.id,
              "dimension": "ROWS",
              "startIndex": 22,
              "endIndex": 22 + leng
            },
            "inheritFromBefore": True
          }
        }]}
        sh.batch_update(insert_row_request)
        ws.batch_update(update_request[ag], value_input_option='USER_ENTERED')
        batch_update_request = asset_title_left(sr_revenues, batch_update_request, ws, ag)
        batch_update_request = bottom_color(sr_revenues, batch_update_request, ws, ag)
        batch_update_request = add_border(sr_revenues, batch_update_request, ws, ag)
        batch_update_request = format_currency(sr_revenues, batch_update_request, ws, ag)

  # Add Art Track Assets
  if len(at_revenues) > 0:
    for i, ag in enumerate(at_revenues):
      if len(at_revenues[ag]) > 0:
        update_request[ag] = []
        update_request[ag].append(
          {
            'range': f'A3:G{2 + len(at_revenues[ag])}',
            'values': [[
              rev['asset_id'],
              rev['isrc'],
              rev['artist'],
              rev['album_code'],
              rev['album'],
              f'{rev["asset_title"]}',
              float(rev["partner_revenue"])
            ] for rev in at_revenues[ag]]
          }
        )
        update_request[ag].append({
          'range': f'A{3 + len(at_revenues[ag])}:B{4 + len(at_revenues[ag])}',
          'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
        })
        update_request[ag].append({
          'range': f'G{3 + len(at_revenues[ag])}:G{4 + len(at_revenues[ag])}',
          'values': [[f'=SUM(G3:G{2 + len(at_revenues[ag])})'], [f'=SUM(G3:G{2 + len(at_revenues[ag])})*{float(client.at_split)}']],
        })

        ws = sh.worksheet(sh.worksheets()[3].title)
        insert_row_request = {'requests': [{
          "insertDimension": {
            "range": {
              "sheetId": ws.id,
              "dimension": "ROWS",
              "startIndex": 22,
              "endIndex": 22 + len(at_revenues[ag])
            },
            "inheritFromBefore": True
          }
        }]}
        sh.batch_update(insert_row_request)
        ws.batch_update(update_request[ag], value_input_option='USER_ENTERED')
        batch_update_request = asset_title_left(at_revenues, batch_update_request, ws, ag)
        batch_update_request = bottom_color(at_revenues, batch_update_request, ws, ag)
        batch_update_request = add_border(at_revenues, batch_update_request, ws, ag)
        batch_update_request = format_currency(at_revenues, batch_update_request, ws, ag)

  if len(mc_revenues) > 0:
    print(mc_revenues)
    # mc_revenues = pd.DataFrame(mc_revenues).groupby(['asset_id', 'asset_title']).sum().reset_index().sort_values(by='partner_revenue', ascending=False).to_dict('records')
    # Add Manual Claimed Assets
    update_request['mc'] = []
    update_request['mc'].append(
      {
        'range': f'A3:G{2 + len(mc_revenues)}',
        'values': [[
          rev['asset_id'],
          rev['isrc'],
          rev['artist'],
          rev['album_code'],
          rev['album'],
          f'{rev["asset_title"]}',
          float(rev["partner_revenue"])
        ] for rev in mc_revenues]
      }
    )
    update_request["mc"].append({
      'range': f'A{3 + len(mc_revenues)}:B{4 + len(mc_revenues)}',
      'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
    })
    update_request["mc"].append({
      'range': f'G{3 + len(mc_revenues)}:G{4 + len(mc_revenues)}',
      'values': [[f'=SUM(G3:G{2 + len(mc_revenues)})'], [f'=SUM(G3:G{2 + len(mc_revenues)})*{float(client.mc_split)}']],
    })
    ws = sh.worksheet(sh.worksheets()[4].title)
    ws.batch_update(update_request["mc"], value_input_option='USER_ENTERED')
    batch_update_request = asset_title_left(mc_revenues, batch_update_request, ws, "mc")
    batch_update_request = bottom_color(mc_revenues, batch_update_request, ws, "mc")
    batch_update_request = add_border(mc_revenues, batch_update_request, ws, "mc")
    batch_update_request = format_currency(mc_revenues, batch_update_request, ws, "mc")

  # Summary
  total_sheet = len(sh.worksheets())
  ws = sh.worksheet(sh.worksheets()[0].title)

  length = [0]
  for ag in ch_revenues:
    if len(ch_revenues[ag]) > 0:
      length.append(len(ch_revenues[ag]))
  for ag in sr_revenues:
    if len(sr_revenues[ag]) > 0:
      length.append(len(sr_revenues[ag]))
  for ag in at_revenues:
    if len(at_revenues[ag]) > 0:
      length.append(len(at_revenues[ag]))
  if len(mc_revenues) > 0:
    length.append(len(mc_revenues))

  item_list = [
    [f"='LEEWay Music & Media'!C{length[1] + 4}"],
    [f"='음원'!G{length[2] + 4}"],
    [f"='아트트랙'!G{length[3] + 4}"],
    [f"='직접소유권주장'!G{length[4] + 4}"],
  ]
  # sh.batch_update(batch_update_request)
  summary_update = []
  summary_update.append({'range': f'D22:D27', 'values': item_list})
  summary_update.append({'range': f'D17', 'values': [[f'{year_month.split("-")[0]}년 {year_month.split("-")[1]}월 수익 내역']]})
  summary_update.append({'range': f'B13', 'values': [[client.payment_method]]})
  summary_update.append({'range': f'B8', 'values': [[client.client_name]]})
  summary_update.append({'range': f'B9', 'values': [['']]})
  summary_update.append({'range': f'B10', 'values': [[client.email]]})
  ws.batch_update(summary_update, value_input_option='USER_ENTERED')
  import time
  time.sleep(25)

  return redirect('home')
