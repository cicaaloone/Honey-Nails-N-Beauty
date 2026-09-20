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
st.write(
    f"လက်ရှိဝင်ရောက်ထားသူ: **{st.session_state.username}** ("
    f"{st.session_state.role})"
)
st.markdown("---")

user_role = st.session_state.get("role", "Staff")

# 1. Firebase Firestore မှ Inventory ဒေတာများကို ဖတ်ယူခြင်း
try:
  docs = db.collection("inventory").stream()
  inventory_list = [doc.to_dict() for doc in docs]
except Exception as e:
  inventory_list = []
  st.error(f"❌ Database မှ ဒေတာဖတ်ရှုရာတွင် အမှားအယွင်းရှိပါသည်: {e}")

current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# အကယ်၍ Firebase ထဲမှာ ဒေတာမရှိသေးရင် Base Inventory ထည့်ရန်
if not inventory_list:
  inventory_list = [
      {
          "Item Code": "HNB-001",
          "Item Description": "Nail Polish Gel",
          "Current Qty": 50,
          "Buying Price (¥)": 50.0,
          "Selling Price (Ks)": 25000.0,
          "Selling Price (¥)": 65.0,
          "Cargo Deli Fee": 1000,
          "Time": current_time,
      },
      {
          "Item Code": "HNB-002",
          "Item Description": "B.O Matte Top Coat",
          "Current Qty": 30,
          "Buying Price (¥)": 30.0,
          "Selling Price (Ks)": 15000.0,
          "Selling Price (¥)": 40.0,
          "Cargo Deli Fee": 500,
          "Time": current_time,
      },
  ]

df_inv = pd.DataFrame(inventory_list)

# လိုအပ်သော Columns များ အစုံအလင် ပါဝင်စေရန် စစ်ဆေးခြင်း (Time Column ပါဝင်သည်)
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

  # ဇယား (၁): Base Inventory & Pricing Editor
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
      # Firestore ထဲသို့ တစ်ခုချင်းစီ ပြန်လည်သိမ်းဆည်းခြင်း
      for _, row in edited_inv.iterrows():
        code = str(row["Item Code"])
        if code and code != "nan":
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
              "Time": save_time,  # သိမ်းဆည်းသည့်အချိန်ကို ထည့်သွင်းခြင်း
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
  st.dataframe(df_inv, use_container_width=True, hide_index=True)

# ဇယား (၂): Final Calculated Inventory (Status ဖြင့်တွက်ချက်ပြသခြင်း)
st.markdown("---")
st.subheader("📊 Final Calculated Inventory (Prices & Stock တိကျစွာ တွက်ချက်ပြီး)")

calc_df = edited_inv if user_role == "Admin" else df_inv


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