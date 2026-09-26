import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

# Streamlit Cloud ရဲ့ Secrets ထဲက firebase အချက်အလက်များကို ခေါ်ယူခြင်း
if "firebase" in st.secrets:
    cred_dict = dict(st.secrets["firebase"])
    
    # private_key ထဲက newline (\n) လွဲနေတာတွေကို ပြန်လည်ပြင်ဆင်ခြင်း
    if "private_key" in cred_dict:
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

    # Firebase app ကို တစ်ကြိမ်ပဲ initialize လုပ်ရန် စစ်ဆေးခြင်း
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        initialize_app(cred)

    db = firestore.client()
else:
    st.error("Firebase secrets not found in Streamlit settings!")
    