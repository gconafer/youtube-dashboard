import json
import os

data = {
  "type": "service_account",
  "project_id": "yt-data-261708",
  "private_key_id": os.environ.get("PRIVATE_KEY_ID"),
  "private_key": os.environ.get("PRIVATE_KEY").replace(r'\n', '\n'),
  "client_email": "spreadsheet@yt-data-261708.iam.gserviceaccount.com",
  "client_id": "101887060418858796188",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/spreadsheet%40yt-data-261708.iam.gserviceaccount.com"
}

with open("service_account.json", "w") as json_file:
    json.dump(data, json_file)

print('service account created')