import streamlit as st
import gspread
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
