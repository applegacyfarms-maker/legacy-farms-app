import streamlit as st
import gspread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
st.set_page_config(page_title="Legacy Farms", page_icon="🌱")

# 1. Recreate the physical JSON file in the cloud server's temporary memory
with open("/tmp/service_account.json", "w") as f:
    f.write(st.secrets["google_credentials"])

# 2. Connect exactly how you did on your home PC
gc = gspread.service_account(filename="/tmp/service_account.json")

sh = gc.open("Legacy Farms Inventory")
worksheet = sh.worksheet("Inventory")
# Fetch data from the sheet
data = worksheet.get_all_records()
customers_data = sh.worksheet("Customers").get_all_records() # ADD THIS LINE

# ... skipping down to your tabs section ...

# Stop the app if the sheet only has headers and no data
if not data:
    st.warning("Inventory is empty! Add items directly in Google Sheets first.")
    st.stop()

item_names = [str(row['Item Name']) for row in data]

st.title("🌱 Legacy Farms Inventory")

tab1, tab2, tab3 = st.tabs(["Log Daily Sales", "Fix Errors / Restock", "Broadcast Emails"])

with tab1:
    st.header("Log a Sale")
    sale_item = st.selectbox("What was sold?", item_names, key="sale_item")
    sale_qty = st.number_input("Quantity sold:", min_value=1, step=1, key="sale_qty")
    
    if st.button("Subtract from Inventory"):
        row_index = item_names.index(sale_item) + 2
        current_qty = int(data[row_index - 2]['Quantity Available'])
        new_qty = current_qty - sale_qty
        
        worksheet.update_cell(row_index, 2, new_qty)
        st.success(f"Success! Sold {sale_qty} {sale_item}. New total is {new_qty}.")

with tab2:
    st.header("Fix Errors / Audit Stock")
    fix_item = st.selectbox("Select item to update:", item_names, key="fix_item")
    
    current_stock = int(data[item_names.index(fix_item)]['Quantity Available'])
    st.info(f"Current recorded stock for {fix_item}: **{current_stock}**")
    
    new_total = st.number_input("Enter the CORRECT total quantity:", min_value=0, value=current_stock, step=1, key="fix_qty")
    
    if st.button("Overwrite Inventory"):
        row_index = item_names.index(fix_item) + 2
        worksheet.update_cell(row_index, 2, new_total)
        st.success(f"Fixed! {fix_item} inventory is now set to {new_total}.")
        st.rerun() # Refreshes the screen instantly after overwriting

    st.divider() # Draws a clean visual line between the two tools
    
    st.subheader("Quick Restock")
    restock_qty = st.number_input("Quantity to add:", min_value=1, step=1, key="add_qty")
    
    if st.button("Add to Inventory"):
        row_index = item_names.index(fix_item) + 2
        new_qty = current_stock + restock_qty
        
        worksheet.update_cell(row_index, 2, new_qty)
        st.success(f"Successfully added {restock_qty} to {fix_item}! New total: {new_qty}")
        st.rerun()
with tab3:
    st.header("Broadcast Stock Email")
    st.write("Clicking this button will instantly email the current inventory to all customers.")
    
    if st.button("Send Email Blast Now"):
        with st.spinner("Compiling inventory and sending emails..."):
            available_items = [
                item for item in data 
                if str(item['Ready to Ship?']).strip().lower() == 'yes' and int(item['Quantity Available']) > 0
            ]
            
            if not available_items:
                st.warning("Nothing to ship this week. Emails cancelled.")
            else:
                inventory_list = "<ul>"
                for item in available_items:
                    inventory_list += f"<li><b>{item['Item Name']}</b>: {item['Quantity Available']} available at ${item['Price']}</li>"
                inventory_list += "</ul><p>Reply to this email to reserve your order before we hit the road!</p>"
                
                # Define the footer and hosted image URL
                LOGOUT_URL = "https://raw.githubusercontent.com/applegacyfarms-maker/legacy-farms-app/main/legacy_logo.png"
                FOOTER_HTML = f"""
                    <div style="border-top: 2px solid #2e8b57; padding-top: 15px; margin-top: 25px; font-family: sans-serif; text-align: center; color: #1c452e;">
                    <img src="{LOGOUT_URL}" alt="Legacy Farm" style="max-width: 200px; width: 100%; height: auto; display: block; margin: 0 auto 10px auto;"><br>
                    <div style="margin-top: 5px;">
                        <strong>Sarah Jenkins, Farm Manager</strong><br>
                        <a href="mailto:sjenkins@legacyfarm.net" style="color: #2e8b57; text-decoration: none;">sjenkins@legacyfarm.net</a><br>
                        <a href="tel:(251)331-2132" style="color: #1c452e; text-decoration: none;">(555) 555-0199</a><br>
                        Legacy Farms and Nursery, 14051 Boothtown Rd, Citronelle, AL 36522<br>
                        <a href="http://www.legacyfarm.net" style="color: #2e8b57; text-decoration: none;">www.legacyfarmsandnursery.com/</a><br>
                        <div style="margin-top: 10px; font-size: 0.9em;">
                            Follow us: | <a href="https://www.facebook.com/p/Legacy-Farms-and-Nursery-100084808846225" style="color: #2e8b57; text-decoration: none;">Facebook @Legacy-Farms-and-Nursery</a> | 
                        </div>
                    </div>
                </div>
            """
                
                SENDER_EMAIL = "app.legacyfarms@gmail.com"
                APP_PASSWORD = st.secrets["GMAIL_PASSWORD"]
                
                # Loop through customers_data to send the emails
                for customer in customers_data:
                    email = str(customer.get('Email Address', '')).strip()
                    customer_name = str(customer.get('Name', 'Friend')).strip()
                    if not customer_name:
                        customer_name = "Friend"
                    
                    if email:
                        # Single braces format the variable correctly, + FOOTER_HTML attaches the design
                        personalized_html = f"<h2>Hi {customer_name}, here is what's fresh this week at Legacy Farms!</h2>" + inventory_list + FOOTER_HTML
                        msg = MIMEMultipart("alternative")
                        msg['Subject'] = "Legacy Farms: Fresh stock is ready!"
                        msg['From'] = SENDER_EMAIL
                        msg['To'] = email
                        msg.attach(MIMEText(personalized_html, "html"))
                        
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                            server.login(SENDER_EMAIL, APP_PASSWORD)
                            server.sendmail(SENDER_EMAIL, email, msg.as_string())
                            
                st.success("Boom! Emails successfully sent to all customers.")
