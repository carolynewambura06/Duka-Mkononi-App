import os
import streamlit as st
import pandas as pd
import datetime

from auth import signup, login
from lang import swahili, english
from utils import get_col_names, migrate_data_columns 

DEFAULT_LANGUAGE = "Swahili"

# Initialize language session state
if "language" not in st.session_state:
    st.session_state.language = "Swahili"  # Default language

# Language selector
selected_lang = st.selectbox(
    "Chagua Lugha / Select Language",
    ["Swahili", "English"],
    index=0 if st.session_state.language == "Swahili" else 1
)
# Update session state when language changes
if selected_lang != st.session_state.language:
    st.session_state.language = selected_lang
    st.rerun()

# Load translations
t = swahili if selected_lang == "Swahili" else english

# Initialize auth state
if "username" not in st.session_state:
    st.session_state.username = ""
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

# File paths
user = st.session_state.username or "guest"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

INVENTORY_FILE = os.path.join(DATA_DIR, f"inventory_{user}.csv")
SALES_FILE = os.path.join(DATA_DIR, f"sales_{user}.csv")
PURCHASE_FILE = os.path.join(DATA_DIR, f"purchases_{user}.csv")

# Load and save helpers
def load_inventory():
    columns = {
        "Swahili": ["Bidhaa", "Bei_ya_ununuzi", "Hifadhi"],
        "English": ["product", "cost_price", "stock"]
    }
    if not os.path.exists(INVENTORY_FILE):
        pd.DataFrame(columns=columns[st.session_state.language]).to_csv(INVENTORY_FILE, index=False)
    return pd.read_csv(INVENTORY_FILE)

def load_sales(data_dir="data", username=None):
    """
    Robust sales data loader with automatic repair and validation
    Args:
        data_dir: Directory where data files are stored
        username: Current user's username for personalized data files
    """
    try:
        # Initialize paths
        username = username or st.session_state.get("username", "guest")
        os.makedirs(data_dir, exist_ok=True)
        sales_file = os.path.join(data_dir, f"sales_{username}.csv")
        
        # Initialize empty dataframe if file doesn't exist
        if not os.path.exists(sales_file):
            cols = get_col_names()
            return pd.DataFrame(columns=[cols.get(col, col) for col in [
                "product", "cost_price", "stock", "date", 
                "qty", "unit_price", "total_price", "profit"
            ]])
            
        # Load with error handling for malformed files
        df = pd.read_csv(sales_file, encoding='utf-8', on_bad_lines='warn')
        
        # Convert date column with validation
        date_col = get_col_names().get("date", "date")
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df[date_col] = df[date_col].fillna(pd.Timestamp.now())
        
        # Ensure required columns exist
        required_cols = ["product", "cost_price", "stock", "date"]
        col_names = get_col_names()
        
        for col in required_cols:
            target_col = col_names.get(col, col)
            if target_col not in df.columns:
                df[target_col] = 0 if col != "date" else pd.Timestamp.now()
        
        # Migrate to current language
        current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
        df = migrate_data_columns(df, current_lang)
        
        # Final validation
        def validate_dataframe(df, required_cols):
            # Check if all required columns are present in the DataFrame
            col_names = get_col_names()
            target_cols = [col_names.get(col, col) for col in required_cols]
            return all(col in df.columns for col in target_cols)

        if not validate_dataframe(df, required_cols):
            st.error("Sales data failed validation. Some columns may be missing.")
            
        return df
        
    except Exception as e:
        st.error(f"Failed to load sales data: {str(e)}")
        # Return empty dataframe with correct columns
        cols = get_col_names()
        return pd.DataFrame(columns=[cols.get(col, col) for col in [
            "product", "cost_price", "stock", "date", 
            "qty", "unit_price", "total_price", "profit"
        ]])

def load_purchases():
    columns = {
        "Swahili": ["Tarehe", "Bidhaa", "Idadi", "Bei_ya_ununuzi"],
        "English": ["date", "product", "qty", "cost_price"]
    }
    if not os.path.exists(PURCHASE_FILE):
        pd.DataFrame(columns=columns[st.session_state.language]).to_csv(PURCHASE_FILE, index=False)
    return pd.read_csv(PURCHASE_FILE)

def save_inventory(df): df.to_csv(INVENTORY_FILE, index=False)
def save_sales(df): df.to_csv(SALES_FILE, index=False)
def save_purchases(df): df.to_csv(PURCHASE_FILE, index=False)

# Page settings
st.set_page_config(page_title=t["app_title"], layout="centered")
st.title(t["app_title"])

# Authentication Interface
if not st.session_state.auth_status:
    tab1, tab2 = st.tabs([t["login"], t["signup"]])

    with tab1:
        uname = st.text_input(t["username"], key="login_username")
        pwd = st.text_input(t["password"], type="password", key="login_password")
        if st.button(t["login_button"]):
            success, msg = login(uname, pwd)
            if success:
                st.session_state.auth_status = True
                st.session_state.username = uname
                st.session_state.language = selected_lang  
                st.success(t["login_success"])
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        uname = st.text_input(t["username"], key="signup_username")
        pwd = st.text_input(t["password"], type="password", key="signup_password")
        if st.button(t["signup_button"]):
            success, msg = signup(uname, pwd)
            if success:
                st.session_state.language = selected_lang  
                st.success(f"{msg} Please login.")
            else:
                st.error(msg)
    st.stop()

# Sidebar Navigation
menu = st.sidebar.radio("Navigate", [
    t["dashboard"],
    t["add_product"],
    t["record_sale"],
    t["view_inventory"],
    t["reports"]
])

if st.sidebar.button(t["logout"]):
    st.session_state.auth_status = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown(t["logged_in_as"].format(st.session_state.username))


# Dashboard page
if menu == t["dashboard"]:
    st.subheader(t["dashboard"])
    try:
        sales = load_sales()
        cols = get_col_names()
        
        # Verify we have required columns
        required_cols = {cols["date"], cols["total_price"], cols["profit"]}
        if not required_cols.issubset(set(sales.columns)):
            st.error("Data format error. Please delete and regenerate your data files.")
            st.stop()
            
        # Convert date and filter today's sales
        sales[cols["date"]] = pd.to_datetime(sales[cols["date"]])
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        today_sales = sales[sales[cols["date"]].dt.strftime('%Y-%m-%d') == today_str]
    
        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t["todays_revenue"], f"TZS {today_sales[cols['total_price']].sum():,.0f}")
        with col2:
            st.metric(t["estimated_profit"], f"TZS {today_sales[cols['profit']].sum():,.0f}")
        
        # Sales Trends Section
        st.subheader(t["sales_trends"])
        
        # Weekly data
        weekly_data = sales[sales[cols["date"]] >= (datetime.datetime.now() - datetime.timedelta(days=7))]
        if not weekly_data.empty:
            weekly_summary = weekly_data.groupby(cols["date"]).agg({
                cols["total_price"]: "sum", 
                cols["profit"]: "sum"
            }).reset_index()
            
            tab1, tab2 = st.tabs([t["weekly_sales"], t["weekly_profit"]])
            
            with tab1:
                st.line_chart(weekly_summary, x=cols["date"], y=cols["total_price"])
            
            with tab2:
                st.line_chart(weekly_summary, x=cols["date"], y=cols["profit"])
        else:
            st.info(t["no_data_weekly"])
        
        # Monthly data
        monthly_data = sales[sales[cols["date"]].dt.month == datetime.datetime.now().month]
        if not monthly_data.empty:
            monthly_summary = monthly_data.groupby(cols["date"]).agg({
                cols["total_price"]: "sum", 
                cols["profit"]: "sum"
            }).reset_index()
            
            tab3, tab4 = st.tabs([t["monthly_sales"], t["monthly_profit"]])
            
            with tab3:
                st.line_chart(monthly_summary, x=cols["date"], y=cols["total_price"])
            
            with tab4:
                st.line_chart(monthly_summary, x=cols["date"], y=cols["profit"])
        else:
            st.info(t["no_data_monthly"])
        
        # Today's sales table - FIXED SECTION
        st.subheader(t["today_sales"])
        if today_sales.empty:
            st.info(t["no_sales_today"])
        else:
            # Ensure we're only passing DataFrame to st.dataframe()
            st.dataframe(today_sales.reset_index(drop=True))

    except Exception as e:
        st.error(f"{t['error_loading_data']}: {str(e)}")
        st.info(t["try_regenerate_data"])

# Add or Restock Product
elif menu == t["add_product"]:
    st.subheader(t["add_product"])
    inventory = load_inventory()
    cols = get_col_names()
    action = st.radio(t["what_do"], [t["add_new_product"], t["restock_product"]])

    if action == t["add_new_product"]:
        name = st.text_input(t["product_name"])
        price = st.number_input(t["cost_price"], min_value=100)
        qty = st.number_input(t["initial_stock"], min_value=1, step=1)

        if st.button(t["add_product_btn"]):
            new_product = pd.DataFrame([{
                cols["product"]: name, 
                cols["cost_price"]: price, 
                cols["stock"]: qty
            }])
            inventory = pd.concat([inventory, new_product], ignore_index=True)
            save_inventory(inventory)
            st.success(f"{name} {t['add_product_success']}")

    else:
        name = st.selectbox(t["select_product"], inventory[cols["product"]])
        qty = st.number_input(t["quantity_to_add"], min_value=1)
        price = st.number_input(t["purchase_price"], min_value=100)

        if st.button(t["restock_btn"]):
            inventory.loc[inventory[cols["product"]] == name, cols["stock"]] += qty
            inventory.loc[inventory[cols["product"]] == name, cols["cost_price"]] = price
            save_inventory(inventory)

            purchases = load_purchases()
            today = str(datetime.date.today())
            new_row = pd.DataFrame([{
                cols["date"]: today,
                cols["product"]: name,
                cols["qty"]: qty,
                cols["cost_price"]: price
            }])
            purchases = pd.concat([purchases, new_row], ignore_index=True)
            save_purchases(purchases)

            st.success(f"{qty} {name} {t['restock_success']}")

# Record Sale
elif menu == t["record_sale"]:
    st.subheader(t["record_new_sale"])
    inventory = load_inventory()
    cols = get_col_names()

    if inventory.empty:
        st.info(t["no_products_yet"])
    else:
        # Get products with available stock only
        available_products = inventory[inventory[cols["stock"]] > 0]
        
        if available_products.empty:
            st.warning(t["no_products_in_stock"])
        else:
            name = st.selectbox(t["choose_product"], available_products[cols["product"]])
            product_data = inventory[inventory[cols["product"]] == name].iloc[0]
            
            st.write(f"{t['available_stock']}: {product_data[cols['stock']]}")
            
            max_qty = int(product_data[cols["stock"]])
            qty = st.number_input(
                t["quantity_sold"], 
                min_value=1, 
                max_value=max_qty,
                value=1
            )
            
            suggested_price = product_data[cols["cost_price"]] * 1.3  # 30% markup
            price = st.number_input(
                t["selling_price_per_item"], 
                min_value=100, 
                step=100,
                value=int(suggested_price)
            )

            if st.button(t["save_sale_btn"]):
                profit = (price - product_data[cols["cost_price"]]) * qty
                today = str(datetime.date.today())
                
                new_sale = pd.DataFrame([{
                    cols["date"]: today,
                    cols["product"]: name,
                    cols["qty"]: qty,
                    cols["unit_price"]: price,
                    cols["total_price"]: price * qty,
                    cols["cost_price"]: product_data[cols["cost_price"]],
                    cols["profit"]: profit
                }])

                try:
                    sales = load_sales()
                    sales = pd.concat([sales, new_sale], ignore_index=True)
                    save_sales(sales)

                    inventory.loc[inventory[cols["product"]] == name, cols["stock"]] -= qty
                    save_inventory(inventory)

                    st.success(t["sale_success"].format(qty, name))
                    st.balloons()
                except Exception as e:
                    st.error(f"{t['sale_failed']}: {str(e)}")

# Inventory View
elif menu == t["view_inventory"]:
    st.subheader(t["current_stock"])
    inventory = load_inventory()
    st.dataframe(inventory)


# Reports page
elif menu == t["reports"]:
    st.subheader(t["weekly_monthly_reports"])
    sales = load_sales()
    cols = get_col_names()
    sales[cols["date"]] = pd.to_datetime(sales[cols["date"]])
    today = pd.to_datetime(datetime.date.today())

    option = st.selectbox(t["choose_report"], [t["last_7_days"], t["this_month"]])

    if option == t["last_7_days"]:
        start = today - pd.Timedelta(days=7)
        report = sales[sales[cols["date"]] >= start]
    else:
        report = sales[sales[cols["date"]].dt.month == today.month]

    st.metric(t["total_revenue"], f"TZS {report[cols['total_price']].sum():,.0f}")
    st.metric(t["total_profit"], f"TZS {report[cols['profit']].sum():,.0f}")
    st.dataframe(report)
