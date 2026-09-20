import os
import firebase_admin
from firebase_admin import credentials, firestore

# `firebase_config.py` တည်ရှိရာ ဖိုင်တွဲလမ်းကြောင်းကို အခြေခံ၍ JSON ဖိုင်ကို တိကျစွာ ရှာဖွေခြင်း
current_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(current_dir, "firebase_credentials.json")

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        raise FileNotFoundError(
            f"'{cred_path}' ဖိုင်ကို မတွေ့ရှိရပါ။ ကျေးဇူးပြု၍ Project ဖိုင်တွဲထဲသို့ ထည့်ပါ။"
        )

# Firestore Database Client ကို ခေါ်ယူသုံးစွဲရန်
db = firestore.client()