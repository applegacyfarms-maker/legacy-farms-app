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

# 3. Build the core inventory list (this part is the same for everyone)
inventory_list = "<ul>"
for item in available_items:
    inventory_list += f"<li><b>{item['Item Name']}</b>: {item['Quantity Available']} available at ${item['Price']}</li>"
inventory_list += "</ul><p>Reply to this email to reserve your order before we hit the road!</p>"

# 4. Email Credentials
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
        
        # 3. Create the Footer with personalized greeting
# Replace placeholder details as needed.
LOGOUT_URL = "https://raw.githubusercontent.com/applegacyfarms-maker/legacy-farms-app/main/legacy_logo.png"
FOOTER_HTML = f"""
    <div style="border-top: 2px solid #2e8b57; padding-top: 15px; margin-top: 25px; font-family: sans-serif; text-align: center; color: #1c452e;">
        <img src="{LOGOUT_URL}" alt="Legacy Farm" style="max-width: 200px; width: 100%; height: auto; display: block; margin: 0 auto 10px auto;"><br>
        <div style="margin-top: 5px;">
            <strong>Walt Turner, Farm Manager</strong><br>
            <a href="mailto:walt.legacyfarms@gmail.com" style="color: #2e8b57; text-decoration: none;">walt.legacyfarms@gmail.com</a><br>
            <a href="tel:(251)331-2132" style="color: #1c452e; text-decoration: none;">(251)331-2132</a><br>
            Legacy Farms and Nursery, 14051 Boothtown Rd, Citronelle, AL 36522<br>
            <a href="http://www.legacyfarm.net" style="color: #2e8b57; text-decoration: none;">www.legacyfarmsandnursery.com/</a><br>
            <div style="margin-top: 10px; font-size: 0.9em;">
                Follow us: | <a href="https://www.facebook.com/p/Legacy-Farms-and-Nursery-100084808846225" style="color: #2e8b57; text-decoration: none;">Facebook @Legacy-Farms-and-Nursery</a> | 
            </div>
        </div>
    </div>
"""

# ... rest of Section 3 (available_items loop, inventory list, etc.) ...
# ... after Section 4 and def send_update_email ...

# 5. Send personalized emails with the new footer
for customer in customers:
    # ... get name and email ...

    if email:
        # Combine everything, including the new footer variable
        personalized_html = f"<h2>Hi {{customer_name}}, here is what's fresh this week at Legacy Farms!</h2>" + inventory_list + FOOTER_HTML
        
        send_update_email(email, personalized_html)
        print(f"Sent update to {{customer_name}} at {{email}}.")

# 5. Send personalized emails to everyone
for customer in customers:
    email = customer.get('Email Address', '').strip()
    
    # Grab the name from the sheet. If it's blank, default to "Friend"
    customer_name = str(customer.get('Name', 'Friend')).strip()
    if not customer_name:
        customer_name = "Friend"

    if email:
        # Combine the custom greeting with the inventory list
        personalized_html = f"<h2>Hi {customer_name}, here is what's fresh this week at Legacy Farms!</h2>" + inventory_list + FOOTER_HTML
        
        send_update_email(email, personalized_html)
