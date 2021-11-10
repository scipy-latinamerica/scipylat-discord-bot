import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

wks = client.open_by_key('1R0fYLV32a4TpDL0AxO-pxgjEI0XToRu9tU-lw0wL51A')

all_emails = []
for i in range(3):
    worksheet = wks.get_worksheet(i)
    emails = worksheet.col_values(4)[1:]
    all_emails.extend(emails)

assert "eu@arthuralvim.com" in all_emails
