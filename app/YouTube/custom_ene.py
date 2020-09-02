import gspread
import pandas as pd
import pygsheets
from django.db import connections
from django.shortcuts import redirect
from oauth2client.service_account import ServiceAccountCredentials

from .models import Client, AssetGroup


def format_srat(batch_update_request, length, ws):
  batch_update_request['requests'].append({
    "mergeCells": {
      "range": {
        "sheetId": ws.id,
        "startRowIndex": 2 + length,
        "endRowIndex": 4 + length,
        "startColumnIndex": 1,
        "endColumnIndex": 3
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
        "endColumnIndex": 7
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
        "endColumnIndex": 7
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
        "endColumnIndex": 7
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
        "startColumnIndex": 4,
        "endColumnIndex": 7
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
  at_group = asset_groups.filter(asset_type='at').first()
  sr_group = asset_groups.filter(asset_type='sr').first()

  # Art Track Assets to List
  art_track = pd.read_sql_query(f"""
    select *
    from (select asset_id, artist, album, asset_title
          from (select asset_id,
                       artist,
                       case when B.album is null then C.album else B.album end     as album,
                       asset_title,
                       row_number() over (partition by asset_id order by asset_id) as seqnum
                from "YouTube_asset" A
                         left join (select upc, album from "YouTube_asset" where album is not null) B using (upc)
                         left join (select grid, album from "YouTube_asset" where album is not null) C using (grid)
                where asset_group_id = {at_group.id}) t
          where seqnum = 1) X
             join (select asset_id,
                          coalesce(A.partner_revenue, 0)                                  as ads_revenue,
                          coalesce(B.partner_revenue, 0)                                  as red_revenue,
                          coalesce(A.partner_revenue, 0) + coalesce(B.partner_revenue, 0) as partner_revenue
                   from (select asset_id, sum(owned_views) as owned_views, sum(partner_revenue) as partner_revenue
                         from "YouTube_assetrevenueview"
                         where asset_id in
                               (select asset_id
                                from "YouTube_asset"
                                where asset_group_id = {at_group.id})
                           and year_month = '{year_month}'
                           and revenue_type = 'ads'
                         group by asset_id
                         order by partner_revenue desc) A
                            full outer join (select asset_id,
                                                    sum(owned_views)     as owned_views,
                                                    sum(partner_revenue) as partner_revenue
                                             from "YouTube_assetrevenueview"
                                             where asset_id in
                                                   (select asset_id
                                                    from "YouTube_asset"
                                                    where asset_group_id = {at_group.id})
                                               and year_month = '{year_month}'
                                               and revenue_type = 'red'
                                             group by asset_id
                                             order by partner_revenue desc) B using (asset_id)) Y using (asset_id)
    order by partner_revenue desc
    """, connections['default']).fillna('')
  for col in art_track.columns:
    if col not in ['owned_views', 'partner_revenue']:
      art_track[col] = art_track[col].map(lambda x: str(x), na_action='ignore')

  # Sound Recording Assets to List
  sound_recording = pd.read_sql_query(f"""
    select asset_id,
           artist,
           album,
           asset_title,
           coalesce(J.partner_revenue, 0)                                  as ads_revenue,
           coalesce(K.partner_revenue, 0)                                  as red_revenue,
           coalesce(J.partner_revenue, 0) + coalesce(K.partner_revenue, 0) as partner_revenue
    from (
             select asset_id, coalesce(partner_revenue, 0) + coalesce(promotion_partner_revenue, 0) as partner_revenue
             from (select asset_id, sum(owned_views) as owned_views, sum(partner_revenue) as partner_revenue
                   from "YouTube_assetrevenueview"
                   where asset_id in (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})
                     and year_month = '{year_month}'
                     and revenue_type = 'ads'
                     and manual_claimed = FALSE
                   group by asset_id) O
                      full outer join (select asset_id, sum(split_partner_revenue) as promotion_partner_revenue
                                       from (
                                                select included_asset_id                  as asset_id,
                                                       split_onwed_views,
                                                       split_partner_revenue * 0.4 / {float(client.sr_split)} as split_partner_revenue
                                                from (select YTp.asset_id     as promotion_asset_id,
                                                             include.asset_id as included_asset_id
                                                      from "YouTube_promotionvideo_included_asset" as include
                                                               join "YouTube_promotionvideo" YTp
                                                                    on "include".promotionvideo_id = YTp.video_id
                                                      where include.asset_id in
                                                            (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})) J
                                                         left join (select asset_id,
                                                                           cast(owned_views / total as int) as split_onwed_views,
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
                                                                            and revenue_type = 'ads'
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
                                       group by asset_id) P using (asset_id)) J
             full outer join (select asset_id,
                                     coalesce(partner_revenue, 0) + coalesce(promotion_partner_revenue, 0) as partner_revenue
                              from (select asset_id,
                                           sum(owned_views)     as owned_views,
                                           sum(partner_revenue) as partner_revenue
                                    from "YouTube_assetrevenueview"
                                    where asset_id in (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})
                                      and year_month = '{year_month}'
                                      and revenue_type = 'red'
                                      and manual_claimed = FALSE
                                    group by asset_id) O
                                       full outer join (select asset_id,
                                                               sum(split_partner_revenue) as promotion_partner_revenue
                                                        from (
                                                                 select included_asset_id                  as asset_id,
                                                                        split_onwed_views,
                                                                        split_partner_revenue * 0.4 / {float(client.sr_split)} as split_partner_revenue
                                                                 from (select YTp.asset_id     as promotion_asset_id,
                                                                              include.asset_id as included_asset_id
                                                                       from "YouTube_promotionvideo_included_asset" as include
                                                                                join "YouTube_promotionvideo" YTp
                                                                                     on "include".promotionvideo_id = YTp.video_id
                                                                       where include.asset_id in
                                                                             (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})) J
                                                                          left join (select asset_id,
                                                                                            cast(owned_views / total as int) as split_onwed_views,
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
                                                                                             and revenue_type = 'red'
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
                                                                                         group by Y.asset_id) B
                                                                                                        using (asset_id)) K
                                                                                    on J.promotion_asset_id = K.asset_id) M
                                                        group by asset_id) P using (asset_id)) K using (asset_id)
             join (select * from "YouTube_asset") S using (asset_id)
    order by partner_revenue desc;
    """, connections['default']).fillna('')

  # Manual Claim Assets to List
  manual_claiming = pd.read_sql_query(f"""
    select asset_id,
           artist,
           album,
           asset_title,
           ads_revenue,
           red_revenue,
           partner_revenue
    from (select asset_id,
                 coalesce(A.partner_revenue, 0)                                  as ads_revenue,
                 coalesce(B.partner_revenue, 0)                                  as red_revenue,
                 coalesce(A.partner_revenue, 0) + coalesce(B.partner_revenue, 0) as partner_revenue
          from (select asset_id, sum(owned_views) as owned_views, sum(partner_revenue) as partner_revenue
                from "YouTube_assetrevenueview"
                where asset_id in (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})
                  and year_month = '{year_month}'
                  and manual_claimed = TRUE
                  and revenue_type = 'ads'
                group by asset_id) A
                   full outer join (select asset_id,
                                           sum(owned_views)     as owned_views,
                                           sum(partner_revenue) as partner_revenue
                                    from "YouTube_assetrevenueview"
                                    where asset_id in (select asset_id from "YouTube_asset" where asset_group_id = {sr_group.id})
                                      and year_month = '{year_month}'
                                      and manual_claimed = TRUE
                                      and revenue_type = 'red'
                                    group by asset_id) B using (asset_id)) R
             join (select * from "YouTube_asset") S using (asset_id)
    order by partner_revenue desc;
    """, connections['default']).fillna('')

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

  sample_report_id = '1s3sEXKxi1NVz6BTl8DPLKJt4LSUcnOF3ZZyrE2bzo4s'

  new_ss = pyg.drive.copy_file(file_id=sample_report_id, title=f'{year_month.split("-")[0]}년 {int(year_month.split("-")[1])}월 수익 정산서 [{client}]', folder=folder_id)
  sh = gc.open_by_key(new_ss['id'])

  # Batch Update List
  update_request = {}
  batch_update_request = {}
  batch_update_request['requests'] = []

  # Insert Sound Recording
  ws = sh.worksheets()[1]
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
      'range': f'A3:G{2 + length}',
      'values': [[
        '\'' + rev['asset_id'],
        '\'' + rev['artist'],
        '\'' + rev['album'],
        '\'' + rev["asset_title"],
        float(rev["ads_revenue"]),
        float(rev["red_revenue"]),
        float(rev["partner_revenue"])
      ] for rev in sound_recording.to_dict('row')]
    }
  )
  update_request.append({
    'range': f'A{3 + length}:B{4 + length}',
    'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
  })
  update_request.append({
    'range': f'E{3 + length}:G{4 + length}',
    'values': [[f'=SUM(E3:E{2 + length})', f'=SUM(F3:F{2 + length})', f'=SUM(G3:G{2 + length})'],
               [f'=SUM(E3:E{2 + length})*{float(client.sr_split)}', f'=SUM(F3:F{2 + length})*{float(client.sr_split)}', f'=SUM(G3:G{2 + length})*{float(client.sr_split)}']],
  })
  ws.batch_update(update_request, value_input_option='USER_ENTERED')
  batch_update_request = format_srat(batch_update_request, length, ws)

  # Insert Art Track
  ws = sh.worksheets()[2]
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
      'range': f'A3:G{2 + length}',
      'values': [[
        '\'' + rev['asset_id'],
        '\'' + rev['artist'],
        '\'' + rev['album'],
        '\'' + rev["asset_title"],
        float(rev["ads_revenue"]),
        float(rev["red_revenue"]),
        float(rev["partner_revenue"])
      ] for rev in art_track.to_dict('row')]
    }
  )
  update_request.append({
    'range': f'A{3 + length}:B{4 + length}',
    'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
  })
  update_request.append({
    'range': f'E{3 + length}:G{4 + length}',
    'values': [[f'=SUM(E3:E{2 + length})', f'=SUM(F3:F{2 + length})', f'=SUM(G3:G{2 + length})'],
               [f'=SUM(E3:E{2 + length})*{float(client.sr_split)}', f'=SUM(F3:F{2 + length})*{float(client.sr_split)}', f'=SUM(G3:G{2 + length})*{float(client.sr_split)}']],
  })
  ws.batch_update(update_request, value_input_option='USER_ENTERED')
  batch_update_request = format_srat(batch_update_request, length, ws)

  if len(manual_claiming) > 0:
    # Add Manual Claimed Assets
    ws = sh.worksheets()[3]
    length = len(manual_claiming)
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
        'range': f'A3:G{2 + length}',
        'values': [[
          '\'' + rev['asset_id'],
          '\'' + rev['artist'],
          '\'' + rev['album'],
          '\'' + rev["asset_title"],
          float(rev["ads_revenue"]),
          float(rev["red_revenue"]),
          float(rev["partner_revenue"])
        ] for rev in manual_claiming.to_dict('row')]
      }
    )
    update_request.append({
      'range': f'A{3 + length}:B{4 + length}',
      'values': [['', '수익 분배 전 금액'], ['', '수익 분배 후 금액']],
    })
    update_request.append({
      'range': f'E{3 + length}:G{4 + length}',
      'values': [[f'=SUM(E3:E{2 + length})', f'=SUM(F3:F{2 + length})', f'=SUM(G3:G{2 + length})'],
                 [f'=SUM(E3:E{2 + length})*{float(client.sr_split)}', f'=SUM(F3:F{2 + length})*{float(client.sr_split)}', f'=SUM(G3:G{2 + length})*{float(client.mc_split)}']],
    })
    ws.batch_update(update_request, value_input_option='USER_ENTERED')
    batch_update_request = format_srat(batch_update_request, length, ws)

  # Summary
  total_sheet = len(sh.worksheets())
  ws = sh.worksheets()[0]

  length = [0]
  length.append(len(sound_recording))
  length.append(len(art_track))
  if len(manual_claiming) > 0:
    length.append(len(manual_claiming))

  item_list = [
    [f"='음원'!G{length[1] + 4}"],
    [f"='아트트랙'!G{length[2] + 4}"],
    [f"='직접소유권주장'!G{length[3] + 4}"],
  ]

  sh.batch_update(batch_update_request)
  summary_update = []
  summary_update.append({'range': f'D22:D25', 'values': item_list})
  summary_update.append({'range': f'D17', 'values': [[f'{year_month.split("-")[0]}년 {year_month.split("-")[1]}월 수익 내역']]})
  summary_update.append({'range': f'B13', 'values': [[client.payment_method]]})
  summary_update.append({'range': f'B8', 'values': [[client.client_name]]})
  summary_update.append({'range': f'B9', 'values': [['']]})
  summary_update.append({'range': f'B10', 'values': [[client.email]]})
  ws.batch_update(summary_update, value_input_option='USER_ENTERED')
  return redirect('payment_history', client_id=client_id, year_month=year_month)
