import gspread
import pandas as pd
import pygsheets
from django.db import connections
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


def payment_export(request, client_id, year_month):
  scope = ['https://spreadsheets.google.com/feeds',
           'https://www.googleapis.com/auth/drive']
  credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
  gc = gspread.authorize(credentials)

  client = Client.objects.get(id=client_id)
  asset_groups = AssetGroup.objects.filter(client=client)
  assets = Asset.objects.filter(asset_group__in=asset_groups)
  ch_groups = asset_groups.filter(asset_type='ch')
  at_groups = asset_groups.filter(asset_type='at')
  sr_groups = asset_groups.filter(asset_type='sr')

  mc_revenues = []
  ch_revenues = {}
  at_revenues = {}
  sr_revenues = {}

  # Channel Assets to List
  if len(ch_groups) > 0:
    for ag in ch_groups:
      ch_revenues[ag.group_name] = []
      rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
      mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
      if len(rev) > 0:
        rev_by_id = rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          r['asset_title'] = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['partner_revenue'] = r.pop('total')
          ch_revenues[ag.group_name].append(r)
      if len(mc_rev) > 0:
        rev_by_id = mc_rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          r['asset_title'] = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['partner_revenue'] = r.pop('total')
          mc_revenues.append(r)

  # Art Track Assets to List
  if len(at_groups) > 0:
    for ag in at_groups:
      at_revenues[ag.group_name] = []
      rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
      if len(rev) > 0:
        rev_by_id = rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          r['asset_title'] = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['partner_revenue'] = r.pop('total')
          at_revenues[ag.group_name].append(r)

  # Sound Recording Assets to List
  if len(sr_groups) > 0:
    for ag in sr_groups:
      sr_revenues[ag.group_name] = []
      rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
      mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
      if len(rev) > 0:
        rev_by_id = rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          r['asset_title'] = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['partner_revenue'] = r.pop('total')
          sr_revenues[ag.group_name].append(r)

      with connections['default'].cursor() as cursor:
        cursor.execute(f"""
          select ic.asset_id as asset_id, asset_Title, sum(split_revenue) * 0.4 / {float(client.sr_split)} as partner_revenue
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
          group by ic.asset_id, asset_title
          order by partner_revenue desc;
        """)
        for promo_rev in cursor.fetchall():
          tmp = {'asset_id': promo_rev[0], 'asset_title': promo_rev[1], 'partner_revenue': promo_rev[2]}
          sr_revenues[ag.group_name].append(tmp)

      sr_revenues[ag.group_name] = pd.DataFrame(sr_revenues[ag.group_name]).groupby(['asset_id', 'asset_title']).sum().reset_index().sort_values(by='partner_revenue', ascending=False).to_dict(
        'records')
      if len(mc_rev) > 0:
        rev_by_id = mc_rev.values('asset_id').annotate(total=Sum('partner_revenue')).order_by('-total')
        for r in rev_by_id:
          r['asset_title'] = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['partner_revenue'] = r.pop('total')
          mc_revenues.append(r)

  # Create Spread Sheet
  pyg = pygsheets.authorize(service_account_file='service_account.json')
  sample_report_id = '1xGQJEigfpbWgksvvrRTs9cxXTr0CX_H5VR0vY2ZcSIY'
  folder_id = '1OcDHBR_QrSrv8gr7pLFnKOVgPsCnZviZ'
  new_ss = pyg.drive.copy_file(file_id=sample_report_id, title=f'{year_month.split("-")[0]}년 {int(year_month.split("-")[1])}월 수익 정산서 [{client}]', folder=folder_id)
  sh = gc.open_by_key(new_ss['id'])

  # Batch Update List
  update_request = {}
  batch_update_request = {}
  batch_update_request['requests'] = []

  # Add Channel Assets
  if len(ch_revenues) > 0:
    for i, ag in enumerate(ch_revenues):
      update_request[ag] = []
      update_request[ag].append({
        'range': 'A1:B1',
        'values': [[ag.split(' - ')[-1] + ' 채널', '']]
      })
      update_request[ag].append({
        'range': f'A3:C{2 + len(ch_revenues[ag])}',
        'values': [[rev['asset_id'], f'{rev["asset_title"]}', float(rev["partner_revenue"])] for rev in ch_revenues[ag]]
      })
      update_request[ag].append({
        'range': f'A{3 + len(ch_revenues[ag])}:C{4 + len(ch_revenues[ag])}',
        'values': [['', '수익 분배 전 금액', f'=SUM(C3:C{2 + len(ch_revenues[ag])})'], ['', '수익 분배 후 금액', f'=SUM(C3:C{2 + len(ch_revenues[ag])})*{float(client.channel_split)}']],
      })
      template = sh.worksheet(sh.worksheets()[1].title)
      ws = template.duplicate(new_sheet_name=ag.split(' - ')[-1], insert_sheet_index=len(sh.worksheets()))
      ws.batch_update(update_request[ag], value_input_option='USER_ENTERED')
      batch_update_request = asset_title_left(ch_revenues, batch_update_request, ws, ag)
      batch_update_request = bottom_color(ch_revenues, batch_update_request, ws, ag)
      batch_update_request = add_border(ch_revenues, batch_update_request, ws, ag)
      batch_update_request = format_currency(ch_revenues, batch_update_request, ws, ag)

  # Add Sound Recording Assets
  if len(sr_revenues) > 0:
    for i, ag in enumerate(sr_revenues):
      update_request[ag] = []
      update_request[ag].append({
        'range': 'A1:B1',
        'values': [['음원', '']]
      })
      update_request[ag].append({
        'range': f'A3:C{2 + len(sr_revenues[ag])}',
        'values': [[rev['asset_id'], f'{rev["asset_title"]}', float(rev["partner_revenue"])] for rev in sr_revenues[ag]]
      })
      update_request[ag].append({
        'range': f'A{3 + len(sr_revenues[ag])}:C{4 + len(sr_revenues[ag])}',
        'values': [['', '수익 분배 전 금액', f'=SUM(C3:C{2 + len(sr_revenues[ag])})'], ['', '수익 분배 후 금액', f'=SUM(C3:C{2 + len(sr_revenues[ag])})*{float(client.sr_split)}']],
      })
      template = sh.worksheet(sh.worksheets()[1].title)
      ws = template.duplicate(new_sheet_name=ag, insert_sheet_index=len(sh.worksheets()))
      ws.batch_update(update_request[ag], value_input_option='USER_ENTERED')
      batch_update_request = asset_title_left(sr_revenues, batch_update_request, ws, ag)
      batch_update_request = bottom_color(sr_revenues, batch_update_request, ws, ag)
      batch_update_request = add_border(sr_revenues, batch_update_request, ws, ag)
      batch_update_request = format_currency(sr_revenues, batch_update_request, ws, ag)

  # Add Art Track Assets
  if len(at_revenues) > 0:
    for i, ag in enumerate(at_revenues):
      update_request[ag] = []
      update_request[ag].append({
        'range': 'A1:B1',
        'values': [['아트트랙', '']]
      })
      update_request[ag].append({
        'range': f'A3:C{2 + len(at_revenues[ag])}',
        'values': [[rev['asset_id'], f'{rev["asset_title"]}', float(rev["partner_revenue"])] for rev in at_revenues[ag]]
      })
      update_request[ag].append({
        'range': f'A{3 + len(at_revenues[ag])}:C{4 + len(at_revenues[ag])}',
        'values': [['', '수익 분배 전 금액', f'=SUM(C3:C{2 + len(at_revenues[ag])})'], ['', '수익 분배 후 금액', f'=SUM(C3:C{2 + len(at_revenues[ag])})*{float(client.at_split)}']],
      })
      template = sh.worksheet(sh.worksheets()[1].title)
      ws = template.duplicate(new_sheet_name=ag, insert_sheet_index=len(sh.worksheets()))
      ws.batch_update(update_request[ag], value_input_option='USER_ENTERED')
      batch_update_request = asset_title_left(at_revenues, batch_update_request, ws, ag)
      batch_update_request = bottom_color(at_revenues, batch_update_request, ws, ag)
      batch_update_request = add_border(at_revenues, batch_update_request, ws, ag)
      batch_update_request = format_currency(at_revenues, batch_update_request, ws, ag)

  if len(mc_revenues) > 0:
    mc_revenues = pd.DataFrame(mc_revenues).groupby(['asset_id', 'asset_title']).sum().reset_index().sort_values(by='partner_revenue', ascending=False).to_dict('records')
    # Add Manual Claimed Assets
    update_request['mc'] = []
    update_request['mc'].append({
      'range': 'A1:B1',
      'values': [['직접소유권주장', '']]
    })
    update_request['mc'].append({
      'range': f'A3:C{2 + len(mc_revenues)}',
      'values': [[rev['asset_id'], f'{rev["asset_title"]}', float(rev["partner_revenue"])] for rev in mc_revenues]
    })
    update_request["mc"].append({
      'range': f'A{3 + len(mc_revenues)}:C{4 + len(mc_revenues)}',
      'values': [['', '수익 분배 전 금액', f'=SUM(C3:C{2 + len(mc_revenues)})'], ['', '수익 분배 후 금액', f'=SUM(C3:C{2 + len(mc_revenues)})*{float(client.mc_split)}']],
    })
    template = sh.worksheet(sh.worksheets()[1].title)
    ws = template.duplicate(new_sheet_name="직접소유권주장", insert_sheet_index=len(sh.worksheets()))
    ws.batch_update(update_request["mc"], value_input_option='USER_ENTERED')
    batch_update_request = asset_title_left(mc_revenues, batch_update_request, ws, "mc")
    batch_update_request = bottom_color(mc_revenues, batch_update_request, ws, "mc")
    batch_update_request = add_border(mc_revenues, batch_update_request, ws, "mc")
    batch_update_request = format_currency(mc_revenues, batch_update_request, ws, "mc")

  # Summary
  sh.del_worksheet(sh.worksheet(sh.worksheets()[1].title))
  total_sheet = len(sh.worksheets())
  ws = sh.worksheet(sh.worksheets()[0].title)

  batch_update_request['requests'].append({
    "insertDimension": {
      "range": {
        "sheetId": ws.id,
        "dimension": "ROWS",
        "startIndex": 22,
        "endIndex": 22 + total_sheet - 3
      },
      "inheritFromBefore": True
    }
  })
  batch_update_request['requests'].append({
    "mergeCells": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 22,
        "endRowIndex": 22 + total_sheet,
        "startColumnIndex": 3,
        "endColumnIndex": 5
      },
      "mergeType": "MERGE_ROWS"
    }
  })
  batch_update_request['requests'].append({
    "updateBorders": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 22,
        "endRowIndex": 20 + total_sheet,
        "startColumnIndex": 1,
        "endColumnIndex": 6
      },
      "top": {"style": "SOLID", "width": 2},
      "bottom": {"style": "SOLID", "width": 2},
      "innerHorizontal": {"style": "SOLID", "width": 2},
      "innerVertical": {"style": "SOLID", "width": 2},
      "left": {"style": "SOLID", "width": 2},
      "right": {"style": "SOLID", "width": 2}
    }
  })

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

  # item_list = []
  # for i, ws in enumerate(sh.worksheets()):
  #   title = ws.title.replace("'", "''")
  #   item_list.append([i, ws.title, f"='{title}'!C{length[i] + 4}"])
  # item_list = item_list[1:]
  # print(item_list)
  item_list = [[i, ws.title, f"""='{ws.title.replace("'", "''")}'!C{length[i] + 4}"""] for i, ws in enumerate(sh.worksheets())][1:]
  sh.batch_update(batch_update_request)
  summary_update = []
  summary_update.append({'range': f'B22:D{22 + total_sheet}', 'values': item_list})
  summary_update.append({'range': f'E{23 + total_sheet}', 'values': [[f'=SUM(D22:E{22 + total_sheet - 2})']]})
  summary_update.append({'range': f'D17', 'values': [[f'{year_month.split("-")[0]}년 {year_month.split("-")[1]}월 수익 내역']]})
  summary_update.append({'range': f'B13', 'values': [[client.payment_method]]})
  summary_update.append({'range': f'B8', 'values': [[client.client_name]]})
  summary_update.append({'range': f'B9', 'values': [['n/a']]})
  summary_update.append({'range': f'B10', 'values': [[client.email]]})
  ws.batch_update(summary_update, value_input_option='USER_ENTERED')

  return redirect('payment_history', client_id=client_id, year_month=year_month)
