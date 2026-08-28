import gspread
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load credentials securely from GitHub Actions
creds_dict = json.loads(os.environ["GCP_CREDENTIALS"])
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
gc = gspread.service_account_from_dict(creds_dict)

sh = gc.open("Legacy Farms Inventory")
inventory_data = sh.worksheet("Inventory").get_all_records()
customers = sh.worksheet("Customers").get_all_records()

available_items = [
    item for item in inventory_data 
    if str(item['Ready to Ship?']).strip().lower() == 'yes' and int(item['Quantity Available']) > 0
]

if not available_items:
    exit()

html_content = "<h2>This Week at Legacy Farms!</h2><ul>"
for item in available_items:
    html_content += f"<li><b>{item['Item Name']}</b>: {item['Quantity Available']} available at ${item['Price']}</li>"
html_content += "</ul><p>Reply to this email to reserve your order before we hit the road!</p>"

SENDER_EMAIL = "app.legacyfarms@gmail.com"
APP_PASSWORD = os.environ["GMAIL_PASSWORD"]

def send_update_email(customer_email, html_body):
    msg = MIMEMultipart("alternative")
    msg['Subject'] = "Legacy Farms: Fresh stock is ready!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = customer_email
    msg.attach(MIMEText(html_body, "html"))
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, customer_email, msg.as_string())

for customer in customers:
    email = customer.get('Email Address', '').strip()
    if email:
        send_update_email(email, html_content)