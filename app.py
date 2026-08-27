import streamlit as st
import gspread
import json

# Load credentials securely from Streamlit secrets
creds_dict = json.loads(st.secrets["google_credentials"])

# Force the private key to read real line breaks
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

gc = gspread.service_account_from_dict(creds_dict)
sh = gc.open("Legacy Farms Inventory")
worksheet = sh.worksheet("Inventory")

# Fetch data from the sheet
data = worksheet.get_all_records()

# Stop the app if the sheet only has headers and no data
if not data:
    st.warning("Inventory is empty! Add items directly in Google Sheets first.")
    st.stop()

item_names = [str(row['Item Name']) for row in data]

st.title("🌱 Legacy Farms Inventory")

tab1, tab2 = st.tabs(["Log Daily Sales", "Fix Errors / Restock"])

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
