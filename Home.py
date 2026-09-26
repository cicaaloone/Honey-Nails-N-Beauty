import base64
import os
import streamlit as st
from firebase_config import db  # firebase_config.py ထဲက db ကို ယူသုံးခြင်း
import json
import firebase_admin
from firebase_admin import credentials

# Firebase ကို တစ်ကြိမ်တည်းသာ initialize လုပ်ရန် စစ်ဆေးခြင်း
if not firebase_admin._apps:
  cred = credentials.Certificate("firebase_credentials.json")
  firebase_admin.initialize_app(cred)

st.set_page_config(
    page_title="Honey Nails 'n' Beauty - Management System",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)


def set_bg_local(image_file):
  if os.path.exists(image_file):
    with open(image_file, "rb") as f:
      data = f.read()
    encoded = base64.b64encode(data).decode()
    css = f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpg;base64,{encoded});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


set_bg_local("landscape_logo.jfif")

# 1. Initialize Session States
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""
if "role" not in st.session_state:
  st.session_state.role = ""
if "permissions" not in st.session_state:
  st.session_state.permissions = {}

# Sample Inventory & Sales State initialization (Default values set to blank/0)
if "inventory_items" not in st.session_state:
  st.session_state.inventory_items = [
      {
          "Item Code": "",
          "Item Description": "",
          "Buying Price (¥)": 0,
          "Selling Price (Ks)": 0,
          "Stock Qty": 0,
      }
  ]

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
  st.title("🔐 Honey Nails 'n' Beauty - Login")
  st.write(
      "စနစ်ကို အသုံးပြုရန် ကျေးဇူးပြု၍ Login ဝင်ပါ (Admin သို့မဟုတ် Staff)"
  )

  with st.form("login_form"):
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    submit_button = st.form_submit_button("Login ဝင်မည်")

    if submit_button:
      # Admin Authentication
      if username_input == "admin" and password_input == "123":
        st.session_state.logged_in = True
        st.session_state.username = "Admin"
        st.session_state.role = "Admin"
        st.session_state.permissions = {
            "sales": True,
            "inventory_view": True,
            "inventory_edit": True,
            "restock": True,
        }
        st.success("Admin အဖြစ် ဝင်ရောက်မှု အောင်မြင်ပါသည်။")
        st.rerun()
      else:
        # Firebase မှ Staff အကောင့်များနှင့် Permissions များကို စစ်ဆေးခြင်း
        try:
          user_doc = db.collection("users").document(username_input).get()
          if user_doc.exists:
            user_data = user_doc.to_dict()
            if (
                user_data.get("password") == password_input
                and user_data.get("role") == "Staff"
            ):
              st.session_state.logged_in = True
              st.session_state.username = user_data.get("username")
              st.session_state.role = "Staff"
              st.session_state.permissions = user_data.get(
                  "permissions",
                  {
                      "sales": True,
                      "inventory_view": False,
                      "inventory_edit": False,
                      "restock": False,
                  },
              )
              st.success("Staff အဖြစ် ဝင်ရောက်မှု အောင်မြင်ပါသည်။")
              st.rerun()
            else:
              st.error("Password မှားယွင်းနေပါသည်။")
          else:
            st.error("Username မရှိပါ။ (သို့မဟုတ်) အချက်အလက် မှားယွင်းနေပါသည်။")
        except Exception as e:
          st.error(f"Login စစ်ဆေးရာတွင် အမှားရှိပါသည်: {e}")

  st.stop()


# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.success(
    f"👤 Current User: {st.session_state.username} ({st.session_state.role})"
)

st.sidebar.markdown("---")
st.sidebar.title("Navigation")

st.sidebar.page_link("Home.py", label="Home")

if st.session_state.role == "Admin" or st.session_state.get(
    "permissions", {}
).get("sales", False):
  st.sidebar.page_link("pages/Sales.py", label="Sales & Receipt")

if st.session_state.role == "Admin" or st.session_state.get(
    "permissions", {}
).get("inventory_view", False):
  st.sidebar.page_link("pages/Inventory.py", label="Inventory Management")

if st.session_state.role == "Admin" or st.session_state.get(
    "permissions", {}
).get("restock", False):
  st.sidebar.page_link("pages/Restock.py", label="Restock Management")

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout ထွက်မည်", use_container_width=True):
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.role = ""
  st.session_state.permissions = {}
  st.rerun()


# --- MAIN DASHBOARD (LOGGED IN) ---
st.title("🌟 Honey Nails 'n' Beauty Management System")
st.write(
    f"ကြိုဆိုပါတယ်၊ **{st.session_state.username}**။ ဘယ်လိုလုပ်ဆောင်ချက်ကို"
    " ဆောင်ရွက်လိုပါသလဲ?"
)

st.markdown("---")
st.info(
    "👈 ဘယ်ဘက် Sidebar မှတစ်ဆင့် သင့်ရဲ့ လုပ်ပိုင်ခွင့်ရှိသော စာမျက်နှာများသို့"
    " သွားရောက်နိုင်ပါသည်။"
)

if st.session_state.role == "Admin":
  st.markdown(
      "👑 **Admin Privileges:** သင်သည် Admin ဖြစ်သောကြောင့် ဈေးနှုန်းများ၊"
      " Inventory နှင့် Staff အကောင့်များကိုပါ အပြည့်အစုံ စီမံခန့်ခွဲခွင့်ရှိပါသည်။"
  )

  st.markdown("---")
  st.subheader("👥 Admin Panel: Staff Accounts & Permissions Management")

  tab1, tab2 = st.tabs(
      ["➕ Staff အကောင့်အသစ် ဖန်တီးရန်", "📋 ရှိပြီးသား Staff များကို စီမံရန်"]
  )

  with tab1:
    with st.form("create_staff_form"):
      new_staff_user = st.text_input("Staff Username")
      new_staff_pass = st.text_input("Staff Password", type="password")

      st.write("🔒 **Staff ၏ လုပ်ပိုင်ခွင့်များ (Permissions) သတ်မှတ်ရန်**")
      p_sales = st.checkbox("Sales (အရောင်းနှင့် Receipt) အသုံးပြုခွင့်", value=True)
      p_inv_view = st.checkbox("Inventory (ပစ္စည်းလက်ကျန်) ကြည့်ရှုခွင့်", value=True)
      p_inv_edit = st.checkbox(
          "Inventory ဈေးနှုန်း/ပစ္စည်း အပြောင်းအလဲလုပ်ခွင့်", value=False
      )
      p_restock = st.checkbox(
          "Restock (ပစ္စည်းအသစ်ထပ်ဝယ်မှု) စီမံခန့်ခွဲခွင့်", value=False
      )

      create_btn = st.form_submit_button("Staff အကောင့် ဖန်တီးမည်")

      if create_btn:
        if new_staff_user and new_staff_pass:
          staff_data = {
              "username": new_staff_user,
              "password": new_staff_pass,
              "role": "Staff",
              "permissions": {
                  "sales": p_sales,
                  "inventory_view": p_inv_view,
                  "inventory_edit": p_inv_edit,
                  "restock": p_restock,
              },
          }
          try:
            db.collection("users").document(new_staff_user).set(staff_data)
            st.success(
                f"Staff အကောင့် '{new_staff_user}' ကို အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!"
            )
          except Exception as e:
            st.error(f"အကောင့် သိမ်းဆည်းရာတွင် အမှားရှိပါသည်: {e}")
        else:
          st.warning("Username နှင့် Password ထည့်ရန် လိုအပ်ပါသည်။")

  with tab2:
    st.write("🗑️ **Staff အကောင့်များ ဖျက်သိမ်းခြင်း**")
    try:
      users_docs = db.collection("users").where("role", "==", "Staff").stream()
      staff_list = [doc.to_dict() for doc in users_docs]

      if staff_list:
        staff_usernames = [s["username"] for s in staff_list]
        selected_staff_to_delete = st.selectbox(
            "ဖျက်မည့် Staff အကောင့် ရွေးပါ", staff_usernames
        )

        if st.button("❌ ရွေးချယ်ထားသော Staff အကောင့်ကို ဖျက်မည်", type="primary"):
          db.collection("users").document(selected_staff_to_delete).delete()
          st.success(
              f"Staff အကောင့် '{selected_staff_to_delete}' ကို ဖျက်ပြီးပါပြီ!"
          )
          st.rerun()
      else:
        st.info("ဖန်တီးထားသော Staff အကောင့်များ မရှိသေးပါ။")
    except Exception as e:
      st.error(f"ဒေတာဖတ်ရှုရာတွင် အမှားရှိပါသည်: {e}")

else:
  st.markdown(
      "🛠️ **Staff Privileges:** သင်သည် Staff ဖြစ်သောကြောင့် ခွင့်ပြုထားသော"
      " လုပ်ဆောင်ချက်များကိုသာ အဓိက ထုတ်ပေးနိုင်ပါသည်။"
  )