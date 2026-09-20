import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Streamlit Secrets ထဲက firebase အချက်အလက်များကို ယူ၍ ချိတ်ဆက်ခြင်း
if not firebase_admin._apps:
    cred_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
