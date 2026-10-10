import datetime
import pandas as pd
import streamlit as st
from firebase_config import db  # firebase_config.py ထဲက db ကို ယူသုံးခြင်း

st.set_page_config(
    page_title="Honey Nails 'n' Beauty - Inventory Management", layout="wide"
)

if not st.session_state.get("logged_in", False):
    st.warning("ကျေးဇူးပြု၍ ပထမဦးစွာ Login ဝင်ပါ။")
    st.stop()

st.sidebar.write(f"👤 User: {st.session_state.username}")

st.title("📦 Inventory Management")
user_role = st.session_state.get("role", "Staff")
st.write(
    f"လက်ရှိဝင်ရောက်ထားသူ: **{st.session_state.username}** ("
    f"{user_role})"
)
st.markdown("---")

# 1. Firebase Firestore မှ Inventory ဒေတာများကို ဖတ်ယူခြင်း
try:
    docs = db.collection("inventory").stream()
    inventory_list = [doc.to_dict() for doc in docs]
except Exception as e:
    inventory_list = []
    st.error(f"❌ Database မှ ဒေတာဖတ်ရှုရာတွင် အမှားအယွင်းရှိပါသည်: {e}")

current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if not inventory_list:
    inventory_list = [
        {
            "Item Code": "",
            "Item Description": "",
            "Current Qty": 0,
            "Buying Price (¥)": 0.0,
            "Selling Price (Ks)": 0.0,
            "Selling Price (¥)": 0.0,
            "Cargo Deli Fee": 0.0,
            "Time": current_time,
        }
    ]

df_inv = pd.DataFrame(inventory_list)

desired_columns = [
    "Item Code",
    "Item Description",
    "Current Qty",
    "Buying Price (¥)",
    "Selling Price (Ks)",
    "Selling Price (¥)",
    "Cargo Deli Fee",
    "Time",
]
for col in desired_columns:
    if col not in df_inv.columns:
        df_inv[col] = (
            current_time
            if col == "Time"
            else 0
            if "Qty" in col or "Fee" in col
            else 0.0
            if "Price" in col
            else ""
        )

df_inv = df_inv[desired_columns]

if user_role == "Admin":
    st.success(
        "👑 **Admin Mode:** ဤစာမျက်နှာတွင် Inventory ပစ္စည်းများနှင့်"
        " ဈေးနှုန်းများကို တည်းဖြတ် သိမ်းဆည်းနိုင်ပါသည်။"
    )

    st.subheader("📋 Base Inventory & Pricing Editor")
    edited_inv = st.data_editor(
        df_inv,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="inventory_editor",
    )

    if st.button("💾 Inventory အပြောင်းအလဲများကို သိမ်းဆည်းမည်"):
        try:
            save_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for _, row in edited_inv.iterrows():
                code = str(row["Item Code"])
                if code and code != "nan" and code.strip() != "":
                    db.collection("inventory").document(code).set({
                        "Item Code": code,
                        "Item Description": str(row["Item Description"]),
                        "Current Qty": int(row["Current Qty"])
                        if pd.notna(row["Current Qty"])
                        else 0,
                        "Buying Price (¥)": float(row["Buying Price (¥)"])
                        if pd.notna(row["Buying Price (¥)"])
                        else 0.0,
                        "Selling Price (Ks)": float(row["Selling Price (Ks)"])
                        if pd.notna(row["Selling Price (Ks)"])
                        else 0.0,
                        "Selling Price (¥)": float(row["Selling Price (¥)"])
                        if pd.notna(row["Selling Price (¥)"])
                        else 0.0,
                        "Cargo Deli Fee": float(row["Cargo Deli Fee"])
                        if pd.notna(row["Cargo Deli Fee"])
                        else 0.0,
                        "Time": save_time,
                    })
            st.success(
                "Inventory အချက်အလက်များ Firebase Database သို့ အောင်မြင်စွာ"
                " သိမ်းဆည်းပြီးပါပြီ!"
            )
            st.rerun()
        except Exception as e:
            st.error(f"❌ သိမ်းဆည်းရာတွင် အမှားအယွင်းရှိပါသည်: {e}")
else:
    st.info(
        "👀 **Staff Mode (View Only):** ဝန်ထမ်းများသည် Inventory စာရင်းများကို"
        " ကြည့်ရှုနိုင်သော်လည်း ဈေးနှုန်းနှင့် ပစ္စည်းအချက်အလက်များ"
        " ပြင်ဆင်ခွင့် မရှိပါ။"
    )
    edited_inv = df_inv.copy()
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 🔍 Item History Dialog (Item Code အလိုက် အဝင်/အထွက် မှတ်တမ်းကြည့်ရန်)
# ---------------------------------------------------------
@st.dialog("📊 Item History / ပစ္စည်းအဝင်အထွက် မှတ်တမ်း", width="large")
def show_item_history_dialog(selected_code):
    # 1. Firebase မှ ဤ Item Code ၏ Description ကို ရှာဖွေခြင်း
    item_desc_str = ""
    try:
        inv_doc = db.collection("inventory").document(selected_code).get()
        if inv_doc.exists:
            item_desc_str = inv_doc.to_dict().get("Item Description", "")
    except Exception as e:
        st.error(f"❌ Error occurred while fetching item description: {e}")

    # Header မှာ Item Code နဲ့ Description ကို ပူးတွဲပြသရန်
    if item_desc_str:
        st.markdown(f"### 🏷️ Item: **{selected_code} - {item_desc_str}** ၏ အဝင်/အထွက် မှတ်တမ်းများ")
    else:
        st.markdown(f"### 🏷️ Item Code: **{selected_code}** ၏ အဝင်/အထွက် မှတ်တမ်းများ")
    
    # 2. Fetch Restock History (အဝင်)
    restock_history = []
    try:
        r_docs = db.collection("restock_orders").stream()
        for doc in r_docs:
            r_data = doc.to_dict()
            r_id = r_data.get("order_id")
            r_time = r_data.get("time")
            supplier = r_data.get("supplier")
            for itm in r_data.get("items", []):
                if str(itm.get("Item Code")).strip() == selected_code:
                    desc_val = itm.get("Item Description", item_desc_str)
                    restock_history.append({
                        "Type": "📥 Restock (အဝင်)",
                        "ID / Ref": r_id,
                        "Item Description": desc_val,
                        "Name / Customer": f"Supplier: {supplier}",
                        "Qty": int(itm.get("Qty", 0)),
                        "Time": r_time
                    })
    except Exception as e:
        pass

    # 3. Fetch Sales History (အထွက်)
    sales_history = []
    try:
        s_docs = db.collection("sales_orders").stream()
        for doc in s_docs:
            s_data = doc.to_dict()
            s_id = s_data.get("order_id")
            s_time = s_data.get("time")
            customer = s_data.get("customer")
            for itm in s_data.get("items", []):
                if str(itm.get("Item Code")).strip() == selected_code:
                    desc_val = itm.get("Item Description", item_desc_str)
                    sales_history.append({
                        "Type": "📤 Sale (အထွက်)",
                        "ID / Ref": s_id,
                        "Item Description": desc_val,
                        "Name / Customer": f"Customer: {customer}",
                        "Qty": int(itm.get("Qty", 0)),
                        "Time": s_time
                    })
    except Exception as e:
        pass

    all_history = restock_history + sales_history
    if all_history:
        df_history = pd.DataFrame(all_history)
        # Columns များကို စနစ်တကျ စီစဥ်ခြင်း
        df_history = df_history[["Type", "ID / Ref", "Item Description", "Name / Customer", "Qty", "Time"]]
        # Sort by time descending
        df_history = df_history.sort_values(by="Time", ascending=False)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.info("ဤ Item Code အတွက် အဝင်/အထွက် မှတ်တမ်း မရှိသေးပါ။")


st.markdown("---")
st.subheader("🔍 Item History စစ်ဆေးရန် (ပစ္စည်းကုဒ် ရွေးချယ်ပါ)")

# ရယူနိုင်သော Item Codes များကို Selectbox ထဲထည့်ရန်
available_codes = [str(c) for c in edited_inv["Item Code"].tolist() if str(c).strip() and str(c) != "nan"]
if available_codes:
    selected_item_code = st.selectbox("မှတ်တမ်းကြည့်လိုသော Item Code ကို ရွေးပါ", available_codes)
    if st.button("🔍 ဤပစ္စည်း၏ မှတ်တမ်းကို ကြည့်မည်"):
        show_item_history_dialog(selected_item_code)
else:
    st.info("စစ်ဆေးရန် Item Code များ မရှိသေးပါ။")


# ဇယား (၂): Final Calculated Inventory (Status ဖြင့်တွက်ချက်ပြသခြင်း)
st.markdown("---")
st.subheader("📊 Final Calculated Inventory (Prices & Stock တိကျစွာ တွက်ချက်ပြီး)")

calc_df = edited_inv.copy()

def get_status(qty):
    try:
        q = int(qty)
        if q <= 5:
            return "🔴 Low Stock"
        elif q <= 15:
            return "🟡 Medium"
        else:
            return "🟢 In Stock"
    except:
        return "🟢 In Stock"

calc_df["Status"] = calc_df["Current Qty"].apply(get_status)
st.dataframe(calc_df, use_container_width=True, hide_index=True)