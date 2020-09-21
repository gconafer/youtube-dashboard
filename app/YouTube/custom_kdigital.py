import gspread
import pandas as pd
import pygsheets
from django.db import connections
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import redirect, render
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from django.shortcuts import resolve_url

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


def format_srat(batch_update_request, length, ws):
  batch_update_request['requests'].append({
    "mergeCells": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2 + length,
        "endRowIndex": 4 + length,
        "startColumnIndex": 1,
        "endColumnIndex": 7
      },
      "mergeType": "MERGE_ROWS"
    }
  })
  batch_update_request['requests'].append({
    "repeatCell": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2 + length,
        "endRowIndex": 3 + length,
        "startColumnIndex": 0,
        "endColumnIndex": 9
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
        "startRowIndex": 3 + length,
        "endRowIndex": 4 + length,
        "startColumnIndex": 0,
        "endColumnIndex": 9
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
  batch_update_request['requests'].append({
    "updateBorders": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 0,
        "endRowIndex": 4 + length,
        "startColumnIndex": 0,
        "endColumnIndex": 9
      },
      "top": {"style": "SOLID", },
      "bottom": {"style": "SOLID", },
      "innerHorizontal": {"style": "SOLID", },
      "innerVertical": {"style": "SOLID"},
      "left": {"style": "SOLID"},
      "right": {"style": "SOLID"}
    }
  })
  batch_update_request['requests'].append({
    "repeatCell": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2,
        "endRowIndex": 4 + length,
        "startColumnIndex": 8,
        "endColumnIndex": 9
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

def export_kdigital(request, year_month, client_id):
  scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
  credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
  gc = gspread.authorize(credentials)

  client = Client.objects.get(id=client_id)
  asset_groups = AssetGroup.objects.filter(client=client)
  ch_groups = asset_groups.filter(asset_type='ch')
  at_group = asset_groups.filter(asset_type='at').first()
  sr_group = asset_groups.filter(asset_type='sr').first()

  mc_revenues = []
  ch_revenues = {}
  at_revenues = {}
  sr_revenues = {}

  # Channel Assets to List
  if len(ch_groups) > 0:
    for ag in ch_groups:
      rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
      mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
      if len(rev) > 0:
        ch_revenues[ag.group_name] = []
        rev_by_id = rev.values('asset_id').annotate(total=Sum('partner_revenue'), owned_views=Sum('owned_views')).order_by('-total')
        for r in rev_by_id:
          title = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['asset_title'] = title if title else ''
          r['partner_revenue'] = r.pop('total')
          ch_revenues[ag.group_name].append(r)
      if len(mc_rev) > 0:
        rev_by_id = mc_rev.values('asset_id').annotate(total=Sum('partner_revenue'), owned_views=Sum('owned_views')).order_by('-total')
        for r in rev_by_id:
          title = Asset.objects.get(asset_id=r['asset_id']).asset_title
          r['asset_title'] = title if title else ''
          r['isrc'] = ''
          r['artist'] = ''
          r['album'] = ''
          r['label'] = ''
          r['album_code'] = ''
          r['partner_revenue'] = r.pop('total')
          mc_revenues.append(r)

  # Art Track Assets to List
  art_track = pd.read_sql_query(f"""
    select *
    from (select t.*
          from (select asset_id,
                       label,
                       artist,
                       isrc,
                       case when grid is null then upc else grid end               as album_code,
                       case when B.album is null then C.album else B.album end     as album,
                       asset_title,
                       row_number() over (partition by asset_id order by asset_id) as seqnum
                from "YouTube_asset" A
                         left join (select upc, album from "YouTube_asset" where album is not null) B using (upc)
                         left join (select grid, album from "YouTube_asset" where album is not null) C using (grid)
                where asset_group_id = {at_group.id}) t
          where seqnum = 1) X
             join (select asset_id, sum(owned_views) as owned_views, sum(partner_revenue) as partner_revenue
                   from "YouTube_assetrevenueview"
                   where asset_id in
                         (select asset_id
                          from "YouTube_asset"
                          where asset_group_id = {at_group.id})
                     and year_month = '{year_month}'
                   group by asset_id) Y using (asset_id)
    order by partner_revenue desc
    """, connections['default']).fillna('')
  for col in art_track.columns:
    if col not in ['owned_views', 'partner_revenue']:
      art_track[col] = art_track[col].map(lambda x: str(x), na_action='ignore')

  # Sound Recording Assets to List
  sound_recording = pd.read_sql_query(f"""
    select asset_id,
           isrc,
           artist,
           label,
           case when upc is null then grid else upc end as album_code,
           album,
           asset_title,
           owned_views,
           partner_revenue
    from (select asset_id, coalesce(owned_views, 0) + coalesce(promotion_owned_views, 0) as owned_views, coalesce(partner_revenue, 0) + coalesce(promotion_partner_revenue, 0) as partner_revenue
          from (select asset_id, sum(owned_views) as owned_views, sum(partner_revenue) as partner_revenue
                from "YouTube_assetrevenueview"
                where asset_id in (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})
                  and year_month = '{year_month}'
                  and manual_claimed = FALSE
                group by asset_id) O
                   full outer join (select asset_id, sum(split_owned_views) as promotion_owned_views, sum(split_partner_revenue) as promotion_partner_revenue
                                    from (
                                             select included_asset_id                 as asset_id,
                                                    split_owned_views,
                                                    split_partner_revenue * 0.4 / {float(client.sr_split)} as split_partner_revenue
                                             from (select YTp.asset_id     as promotion_asset_id,
                                                          include.asset_id as included_asset_id
                                                   from "YouTube_promotionvideo_included_asset" as include
                                                            join "YouTube_promotionvideo" YTp
                                                                 on "include".promotionvideo_id = YTp.video_id
                                                   where include.asset_id in
                                                         (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})) J
                                                      left join (select asset_id,
                                                                        cast(owned_views / total as int) as split_owned_views,
                                                                        partner_revenue / total          as split_partner_revenue
                                                                 from (select asset_id,
                                                                              sum(owned_views)     as owned_views,
                                                                              sum(partner_revenue) as partner_revenue
                                                                       from "YouTube_assetrevenueview"
                                                                       where asset_id in (
                                                                           select YTp.asset_id as asset_id
                                                                           from "YouTube_promotionvideo_included_asset" as include
                                                                                    join "YouTube_promotionvideo" YTp
                                                                                         on "include".promotionvideo_id = YTp.video_id
                                                                           where include.asset_id in
                                                                                 (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id}))
                                                                         and year_month = '{year_month}'
                                                                       group by asset_id) A
                                                                          left join (
                                                                     select Y.asset_id, count(X.asset_id) as total
                                                                     from "YouTube_promotionvideo_included_asset" X
                                                                              join "YouTube_promotionvideo" Y on X.promotionvideo_id = Y.video_id
                                                                     where promotionvideo_id in (
                                                                         select distinct video_id
                                                                         from "YouTube_promotionvideo_included_asset" as include
                                                                                  join "YouTube_promotionvideo" YTp
                                                                                       on "include".promotionvideo_id = YTp.video_id
                                                                         where include.asset_id in
                                                                               (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id}))
                                                                     group by Y.asset_id) B using (asset_id)) K
                                                                on J.promotion_asset_id = K.asset_id) M
                                    group by asset_id) P using (asset_id)) R
             join (select * from "YouTube_asset") S using (asset_id)
    order by partner_revenue desc;
    """, connections['default']).fillna('')

  mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=sr_group), year_month=year_month, manual_claimed=True, promotion=False)
  if len(mc_rev) > 0:
    rev_by_id = mc_rev.values('asset_id').annotate(total=Sum('partner_revenue'), owned_views=Sum('owned_views')).order_by('-total')
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

  # Create Spread Sheet
  pyg = pygsheets.authorize(service_account_file='service_account.json')
  folder_name = f'[Payment] {year_month}'
  search = pyg.drive.list(q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'",
                             spaces='drive', fields='nextPageToken, files(id, name)')
  if len(search) == 0:
      file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': ['1ySLfZsTXoG7XW8GIlIZE1iqDajtwv3jq']
      }
      kwargs = {}
      kwargs['supportsTeamDrives'] = True
      folder_id = pyg.drive.service.files().create(body=file_metadata, fields='id', **kwargs).execute()['id']
  else:
      folder_id = search[0]['id']

  sample_report_id = '1A_GFZ3mpXVsRtCnWDPBO46YakyHIvIiDsQ_altyTztU'

  new_ss = pyg.drive.copy_file(file_id=sample_report_id, title=f'{year_month.split("-")[0]}년 {int(year_month.split("-")[1])}월 수익 정산서 [{client}]', folder=folder_id)
  sh = gc.open_by_key(new_ss['id'])

  # Batch Update List
  update_request = {}
  batch_update_request = {}
  batch_update_request['requests'] = []

  # Insert Sound Recording
  ws = sh.worksheets()[3]
  update_request = []
  length = len(sound_recording)
  insert_row_request = {'requests': [{
    "insertDimension": {
      "range": {
        "sheetId": ws.id,
        "dimension": "ROWS",
        "startIndex": 22,
        "endIndex": 22 + length
      },
      "inheritFromBefore": True
    }
  }]}
  sh.batch_update(insert_row_request)
  update_request.append(
    {
      'range': f'A3:I{2 + length}',
      'values': [[
        '\'' + rev['asset_id'],
        '\'' + rev['label'],
        '\'' + rev['artist'],
        '\'' + rev['isrc'],
        '\'' + rev['album_code'],
        '\'' + rev['album'],
        '\'' + rev["asset_title"],
        int(rev["owned_views"]),
        float(rev["partner_revenue"])
      ] for rev in sound_recording.to_dict('row')]
    }
  )
  update_request.append({
    'range': f'A{3 + length}:B{4 + length}',
    'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
  })
  update_request.append({
    'range': f'H{3 + length}:I{4 + length}',
    'values': [[f'=SUM(H3:H{2 + length})', f'=SUM(I3:I{2 + length})'],
               ['', f'=SUM(I3:I{2 + length})*{float(client.sr_split)}']],
  })
  ws.batch_update(update_request, value_input_option='USER_ENTERED')
  batch_update_request = format_srat(batch_update_request, length, ws)
  # Insert Art Track
  ws = sh.worksheets()[4]
  length = len(art_track)
  insert_row_request = {'requests': [{
    "insertDimension": {
      "range": {
        "sheetId": ws.id,
        "dimension": "ROWS",
        "startIndex": 22,
        "endIndex": 22 + length
      },
      "inheritFromBefore": True
    }
  }]}
  sh.batch_update(insert_row_request)
  update_request = []
  update_request.append(
    {
      'range': f'A3:I{2 + length}',
      'values': [[
        '\'' + rev['asset_id'],
        '\'' + rev['label'],
        '\'' + rev['artist'],
        '\'' + rev['isrc'],
        '\'' + rev['album_code'],
        '\'' + rev['album'],
        '\'' + rev["asset_title"],
        int(rev["owned_views"]),
        float(rev["partner_revenue"])
      ] for rev in art_track.to_dict('row')]
    }
  )
  update_request.append({
    'range': f'A{3 + length}:B{4 + length}',
    'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
  })
  update_request.append({
    'range': f'H{3 + length}:I{4 + length}',
    'values': [[f'=SUM(H3:H{2 + length})', f'=SUM(I3:I{2 + length})'],
               ['', f'=SUM(I3:I{2 + length})*{float(client.at_split)}']],
  })
  ws.batch_update(update_request, value_input_option='USER_ENTERED')
  batch_update_request = format_srat(batch_update_request, length, ws)

  # Add Channel Assets
  update_request = {}
  for i, ag in enumerate(ch_revenues):
    insert_row_request = {}
    insert_row_request['requests'] = []
    leng = len(ch_revenues[ag])
    if leng > 0:
      update_request[ag] = []
      update_request[ag].append({'range': 'A1:B1', 'values': [['', ag.split(' - ')[-1] + ' 채널']]})
      update_request[ag].append(
        {
          'range': f'A3:C{2 + leng}',
          'values': [[rev['asset_id'], f'{rev["asset_title"]}', float(rev["partner_revenue"])] for rev in ch_revenues[ag]]
        }
      )
      update_request[ag].append(
        {'range': f'A{3 + leng}:C{4 + leng}', 'values': [['', '수익 분배 전 금액', f'=SUM(C3:C{2 + leng})'], ['', '수익 분배 후 금액', f'=SUM(C3:C{2 + leng})*{float(client.channel_split)}']], })
      ws = sh.worksheets()[i + 1]
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
      batch_update_request = asset_title_left(ch_revenues, batch_update_request, ws, ag)
      batch_update_request = bottom_color(ch_revenues, batch_update_request, ws, ag)
      batch_update_request = add_border(ch_revenues, batch_update_request, ws, ag)
      batch_update_request = format_currency(ch_revenues, batch_update_request, ws, ag)

  if len(mc_revenues) > 0:
    # Add Manual Claimed Assets
    length = len(mc_revenues)
    print(length)
    update_request['mc'] = []
    update_request['mc'].append(
      {
        'range': f'A3:I{2 + length}',
        'values': [[
          rev['asset_id'],
          rev['label'] if rev['label'] else '',
          rev['artist'] if rev['artist'] else '',
          rev['isrc'] if rev['isrc'] else '',
          rev['album_code'] if rev['album_code'] else '',
          rev['album'] if rev['album'] else '',
          f'{rev["asset_title"]}',
          int(rev["owned_views"]) if rev['owned_views'] else '',
          float(rev["partner_revenue"])
        ] for rev in mc_revenues]
      }
    )
    update_request["mc"].append({
      'range': f'A{3 + length}:B{4 + length}',
      'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
    })
    update_request["mc"].append({
      'range': f'H{3 + length}:I{4 + length}',
      'values': [[f'=SUM(H3:H{2 + length})', f'=SUM(I3:I{2 + length})'],
                 ['', f'=SUM(I3:I{2 + length})*{float(client.mc_split)}']],
    })
    ws = sh.worksheet(sh.worksheets()[5].title)
    ws.batch_update(update_request["mc"], value_input_option='USER_ENTERED')
    batch_update_request = format_srat(batch_update_request, length, ws)
    # batch_update_request = asset_title_left(mc_revenues, batch_update_request, ws, "mc")
    # batch_update_request = bottom_color(mc_revenues, batch_update_request, ws, "mc")
    # batch_update_request = add_border(mc_revenues, batch_update_request, ws, "mc")
    # batch_update_request = format_currency(mc_revenues, batch_update_request, ws, "mc")

  # Summary
  total_sheet = len(sh.worksheets())
  ws = sh.worksheets()[0]

  length = [0]
  for ag in ch_revenues:
    if len(ch_revenues[ag]) > 0:
      length.append(len(ch_revenues[ag]))
  length.append(len(sound_recording))
  length.append(len(art_track))
  if len(mc_revenues) > 0:
    length.append(len(mc_revenues))

  item_list = [
    [f"='KDM-KPOP'!C{length[1] + 4}"],
    [f"='KDM'!C{length[2] + 4}"],
    [f"='음원'!I{length[3] + 4}"],
    [f"='아트트랙'!I{length[4] + 4}"],
    [f"='직접소유권주장'!I{length[5] + 4}"],
  ]
  sh.batch_update(batch_update_request)
  summary_update = []
  summary_update.append({'range': f'D22:D26', 'values': item_list})
  summary_update.append({'range': f'D17', 'values': [[f'{year_month.split("-")[0]}년 {year_month.split("-")[1]}월 수익 내역']]})
  summary_update.append({'range': f'B13', 'values': [[client.payment_method]]})
  summary_update.append({'range': f'B8', 'values': [[client.client_name]]})
  summary_update.append({'range': f'B9', 'values': [['']]})
  summary_update.append({'range': f'B10', 'values': [[client.email]]})
  ws.batch_update(summary_update, value_input_option='USER_ENTERED')
  return redirect('payment_history', client_id=client_id, year_month=year_month)