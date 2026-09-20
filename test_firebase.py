from firebase_config import db

try:
    # Firestore database ထဲကို စမ်းသပ်ဒေတာ တစ်ခု ပို့ကြည့်ခြင်း
    doc_ref = db.collection("test_connection").document("connection_test")
    doc_ref.set({"status": "Connected Successfully!", "shop": "Honey Nails 'n' Beauty"})
    
    print("✨ Firebase နဲ့ အောင်မြင်စွာ ချိတ်ဆက်နိုင်ပါပြီ! ✨")
    
    # ပို့လိုက်တဲ့ ဒေတာကို ပြန်ဖတ်ကြည့်ခြင်း
    doc = doc_ref.get()
    if doc.exists:
        print(f"📄 ရရှိသော ဒေတာ: {doc.to_dict()}")
        
except Exception as e:
    print(f"❌ ချိတ်ဆက်ရာတွင် အမှားအယွင်း ရှိနေပါသည်: {e}")