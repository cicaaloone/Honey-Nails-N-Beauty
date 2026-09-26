import datetime
import io
import pandas as pd
import streamlit as st
from firebase_config import db

st.set_page_config(
    page_title="Honey Nails 'n' Beauty - Restock Management", layout="wide"
)

if not st.session_state.get("logged_in", False):
  st.warning("ကျေးဇူးပြု၍ ပထမဦးစွာ Login ဝင်ပါ။")
  st.stop()

st.sidebar.write(f"👤 User: {st.session_state.username}")


# 1. Firebase မှ Restock Orders များကို ဖတ်ယူခြင်း
if "restock_orders" not in st.session_state:
  try:
    docs = db.collection("restock_orders").stream()
    st.session_state.restock_orders = [doc.to_dict() for doc in docs]
  except Exception as e:
    st.session_state.restock_orders = []

# Inventory items များကို Firebase မှ ခေါ်ယူရန်
if "inventory_items" not in st.session_state:
  try:
    docs = db.collection("inventory").stream()
    st.session_state.inventory_items = [doc.to_dict() for doc in docs]
  except Exception as e:
    st.session_state.inventory_items = []


# Helper Function: Firebase သို့ Restock Orders များ သိမ်းဆည်းရန်
def save_restock_to_firebase():
  try:
    for order in st.session_state.restock_orders:
      db.collection("restock_orders").document(str(order["order_id"])).set(
          order
      )
  except Exception as e:
    st.error(f"❌ Restock Orders သိမ်းဆည်းရာတွင် အမှားရှိပါသည်: {e}")


# Helper Function: Restock Order ထည့်လိုက်/ပြင်လိုက်တိုင်း Inventory ထဲသို့ Stock ပမာဏ အလိုအလျောက် ပေါင်းထည့်ရန်
def update_inventory_stock_on_restock(items):
  try:
    for item in items:
      code = str(item.get("Item Code"))
      qty_to_add = int(item.get("Qty", 0))

      if code and code != "nan" and code != "HNB-000":
        doc_ref = db.collection("inventory").document(code)
        doc = doc_ref.get()

        if doc.exists:
          data = doc.to_dict()
          current_qty = int(data.get("Current Qty", 0)) if data else 0
          new_qty = current_qty + qty_to_add
          doc_ref.update({"Current Qty": new_qty})
        else:
          doc_ref.set({
              "Item Code": code,
              "Item Description": item.get("Item Description", "New Item"),
              "Current Qty": qty_to_add,
              "Buying Price (¥)": 0.0,
              "Selling Price (Ks)": 0.0,
              "Selling Price (¥)": 0.0,
              "Cargo Deli Fee": float(item.get("Deli Fee", 0.0)),
          })
  except Exception as e:
    st.error(f"❌ Stock အလိုအလျောက် တွက်ချက်ရာတွင် အမှားရှိပါသည်: {e}")


# 2. Restock Receipt Dialog
@st.dialog("📥 Restock Receipt / ပစ္စည်းဝယ်ယူမှုပြေစာ", width="large")
def show_restock_dialog(order):

  @st.fragment
  def restock_fragment():
    st.markdown(
        """
        <style>
        @media print {
            .no-print, button, div[data-testid="stInfo"], div.stButton { display: none !important; }
            div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"] { border: none !important; box-shadow: none !important; padding: 0px !important; }
            body { font-size: 12px; }
            hr { margin: 5px 0px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    print_mode_key = f"r_print_mode_{order['order_id']}"
    if print_mode_key not in st.session_state:
      st.session_state[print_mode_key] = False

    with st.container(border=True):
      st.markdown('<div class="no-print">', unsafe_allow_html=True)
      col_t1, col_t2 = st.columns([1.5, 4])
      with col_t1:
        if st.session_state[print_mode_key]:
          if st.button(
              "✏️ Edit Mode သို့ ပြန်ရန်", key=f"r_edit_{order['order_id']}"
          ):
            st.session_state[print_mode_key] = False
            st.rerun(scope="fragment")
        else:
          if st.button(
              "🖨️ Print View သို့ ပြောင်းမည်",
              key=f"r_pview_{order['order_id']}",
              type="primary",
          ):
            st.session_state[print_mode_key] = True
            st.rerun(scope="fragment")
      st.markdown("</div>", unsafe_allow_html=True)
      st.markdown("---")

      st.markdown(
          "<h2 style='text-align: center; color: #1e3a8a;'>Honey Nails 'n'"
          " Beauty</h2>",
          unsafe_allow_html=True,
      )
      st.markdown(
          "<h4 style='text-align: center; color: #1d4ed8;'>RESTOCK RECEIPT /"
          " ပစ္စည်းဝယ်ယူမှုပြေစာ</h4>",
          unsafe_allow_html=True,
      )
      st.markdown("---")

      col_info1, col_info2 = st.columns(2)
      with col_info1:
        st.write(f"**Supplier:** {order['supplier']}")
        st.write(f"**Date & Time:** {order['time']}")
      with col_info2:
        st.write(f"**Restock ID:** {order['order_id']}")

      st.markdown("---")

      raw_items = order.get("items", [])
      formatted_items = []
      for itm in raw_items:
        t_price = itm.get("Total Price", 0)
        d_fee = itm.get("Deli Fee", 0)
        formatted_items.append({
            "Item Code": itm.get("Item Code", "HNB-000"),
            "Item Description": itm.get("Item Description", "New Item"),
            "Qty": itm.get("Qty", 0),
            "Total Price": t_price,
            "Deli Fee": d_fee,
        })

      df_items = pd.DataFrame(formatted_items)
      if "Total Price" not in df_items.columns:
        df_items["Total Price"] = 0.0
      if "Deli Fee" not in df_items.columns:
        df_items["Deli Fee"] = 0.0

      df_items["Total Cost"] = (
          df_items["Qty"] * df_items["Total Price"]
      ) + df_items["Deli Fee"]

      df_items = df_items[[
          "Item Code",
          "Item Description",
          "Qty",
          "Total Price",
          "Deli Fee",
          "Total Cost",
      ]]

      editor_key = f"r_editor_{order['order_id']}"

      if st.session_state[print_mode_key]:
        st.info("💡 **Print View** သို့ ရောက်ရှိနေပါပြီ။")
        st.dataframe(df_items, use_container_width=True, hide_index=True)
        edited_df = df_items
      else:
        edited_df = st.data_editor(
            df_items,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key=editor_key,
        )

        updated_items = []
        for _, row in edited_df.iterrows():
          code = (
              str(row["Item Code"])
              if pd.notna(row["Item Code"]) and str(row["Item Code"]).strip() != ""
              else "HNB-000"
          )
          desc = (
              str(row["Item Description"])
              if pd.notna(row["Item Description"])
              else "New Item"
          )
          qty = int(row["Qty"]) if pd.notna(row["Qty"]) else 0
          tot_price = (
              float(row["Total Price"]) if pd.notna(row["Total Price"]) else 0.0
          )
          deli_fee = float(row["Deli Fee"]) if pd.notna(row["Deli Fee"]) else 0.0

          updated_items.append({
              "Item Code": code,
              "Item Description": desc,
              "Qty": qty,
              "Total Price": tot_price,
              "Deli Fee": deli_fee,
          })

        order["items"] = updated_items
        save_restock_to_firebase()
        update_inventory_stock_on_restock(updated_items)

      total_items_cost = (edited_df["Qty"] * edited_df["Total Price"]).sum()
      total_deli_fee = edited_df["Deli Fee"].sum()
      total_cost = total_items_cost + total_deli_fee

      st.markdown("---")
      st.markdown(f"**ပစ္စည်းတန်ဖိုး စုစုပေါင်း:** {total_items_cost:,.0f} ကျပ်")
      st.markdown(f"**စုစုပေါင်း Deli Fee:** {total_deli_fee:,.0f} ကျပ်")
      st.markdown(
          f"**စုစုပေါင်း ကျသင့်ငွေ (Deli Fee အပါအဝင်):** {total_cost:,.0f} ကျပ်"
      )

      st.markdown("---")
      st.markdown("📥 **Export & Print Options**")
      exp_col1, exp_col2, exp_col3 = st.columns(3)

      with exp_col1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
          edited_df.to_excel(writer, index=False, sheet_name="Restock")
        st.download_button(
            "📥 Download Excel",
            data=output.getvalue(),
            file_name=f"Restock_{order['order_id']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.excel",
            key=f"dl_r_excel_{order['order_id']}",
        )
      with exp_col2:
        st.download_button(
            "📄 Download CSV",
            data=edited_df.to_csv(index=False).encode("utf-8"),
            file_name=f"Restock_{order['order_id']}.csv",
            mime="text/csv",
            key=f"dl_r_csv_{order['order_id']}",
        )
      with exp_col3:
        if st.button("🖨️ Print", key=f"r_print_{order['order_id']}"):
          st.info("💡 Print View သို့ ပြောင်းပြီး Ctrl + P နှိပ်ပါ။")

  restock_fragment()


# 3. New Restock Order Dialog
@st.dialog("➕ New Restock Order ဖန်တီးရန်")
def new_restock_dialog():
  next_num = len(st.session_state.restock_orders) + 1
  auto_id = f"RES-{next_num:02d}"
  current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  st.write(f"**Restock ID (Auto):** {auto_id}")
  st.write(f"**Time:** {current_time}")

  existing_suppliers = list(
      set([
          ord.get("supplier", "")
          for ord in st.session_state.restock_orders
          if ord.get("supplier")
      ])
  )

  supplier_mode = st.radio(
      "Supplier ရွေးချယ်မည့် ပုံစံ",
      ["စာရင်းထဲမှ ရွေးမည် (Selectbox)", "အသစ် ရိုက်ထည့်မည် (Text Input)"],
  )

  if supplier_mode == "စာရင်းထဲမှ ရွေးမည် (Selectbox)" and existing_suppliers:
    supplier = st.selectbox("Supplier ရွေးချယ်ပါ", existing_suppliers)
  else:
    supplier = st.text_input("Supplier အမည်သစ် ထည့်သွင်းပါ")

  if st.button("Restock Order အသစ် သိမ်းဆည်းမည်"):
    if supplier:
      default_items = [{
          "Item Code": "HNB-000",
          "Item Description": "New Item",
          "Qty": 1,
          "Total Price": 0.0,
          "Deli Fee": 0.0,
      }]
      new_restock = {
          "order_id": auto_id,
          "supplier": supplier,
          "time": current_time,
          "items": default_items,
          "paid_amount": 0,
      }
      st.session_state.restock_orders.append(new_restock)
      save_restock_to_firebase()
      update_inventory_stock_on_restock(default_items)

      st.success("Restock Order အသစ် ထည့်ပြီးပါပြီ!")
      st.rerun()
    else:
      st.warning("ကျေးဇူးပြု၍ Supplier Name ထည့်ပါ။")


# 4. Delete Restock Order Dialog
@st.dialog("🗑️ Restock Order ဖျက်ရန်")
def delete_restock_dialog():
  if not st.session_state.restock_orders:
    st.warning("ဖျက်ရန် Restock Order များ မရှိသေးပါ။")
    return

  order_ids = [ord["order_id"] for ord in st.session_state.restock_orders]
  selected_id = st.selectbox("ဖျက်မည့် Restock ID ကို ရွေးပါ", order_ids)

  if st.button("သေချာပေါက် ဖျက်မည်", type="primary"):
    st.session_state.restock_orders = [
        ord
        for ord in st.session_state.restock_orders
        if ord["order_id"] != selected_id
    ]

    try:
      db.collection("restock_orders").document(str(selected_id)).delete()
    except Exception as e:
      st.error(f"ဖျက်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")

    st.success(f"Restock ID: {selected_id} ကို ဖျက်ပြီးပါပြီ!")
    st.rerun()


# --- Main Web App Interface ---
st.title("📥 Restock Orders Management")
st.write(
    "ပစ္စည်းအသစ် ထပ်ဝယ်ယူမှုများကို စီမံခန့်ခွဲရန်နှင့် Stock အလိုအလျောက်"
    " ပေါင်းထည့်ရန်"
)

top_col1, top_col2, top_col3 = st.columns([6, 1.2, 1.2])
with top_col2:
  if st.button("🗑️ Delete"):
    delete_restock_dialog()
with top_col3:
  if st.button("➕ New Order"):
    new_restock_dialog()

st.markdown("---")

# ဇယား (၁): Base Restock Items & Pricing Editor
st.markdown("---")
st.subheader("📋 Base Restock Items & Pricing Editor")
st.write(
    "အောက်ပါ ဇယားတွင် Restock ပစ္စည်းအချက်အလက်များကို တည်းဖြတ်ပြီး အပြောင်းအလဲများကို သိမ်းဆည်းပါ။"
)

if st.session_state.restock_orders:
  all_restock_items = []
  for r_ord in st.session_state.restock_orders:
    for itm in r_ord.get("items", []):
      t_price = itm.get("Total Price", 0)
      d_fee = itm.get("Deli Fee", 0.0)
      all_restock_items.append({
          "Restock ID": r_ord.get("order_id"),
          "Supplier": r_ord.get("supplier"),
          "Time": r_ord.get("time"),
          "Item Code": itm.get("Item Code", "HNB-000"),
          "Item Description": itm.get("Item Description", "New Item"),
          "Qty": itm.get("Qty", 0),
          "Total Price": t_price,
          "Deli Fee": d_fee,
      })

  df_base_restock = pd.DataFrame(all_restock_items)

  edited_base_restock = st.data_editor(
      df_base_restock,
      use_container_width=True,
      hide_index=True,
      num_rows="dynamic",
      key="base_restock_editor",
  )

  if st.button("💾 Save Changes (အပြောင်းအလဲများကို သိမ်းမည်)", type="primary"):
    if edited_base_restock is not None:
      for r_ord in st.session_state.restock_orders:
        o_id = r_ord["order_id"]
        matching_rows = edited_base_restock[
            edited_base_restock["Restock ID"] == o_id
        ]
        if not matching_rows.empty:
          updated_ord_items = []
          for _, row in matching_rows.iterrows():
            code = (
                str(row["Item Code"])
                if pd.notna(row["Item Code"]) and str(row["Item Code"]).strip() != ""
                else "HNB-000"
            )
            desc = (
                str(row["Item Description"])
                if pd.notna(row["Item Description"])
                else "New Item"
            )
            qty = int(row["Qty"]) if pd.notna(row["Qty"]) else 0
            tot_price = (
                float(row["Total Price"]) if pd.notna(row["Total Price"]) else 0.0
            )
            deli_fee = float(row["Deli Fee"]) if pd.notna(row["Deli Fee"]) else 0.0

            updated_ord_items.append({
                "Item Code": code,
                "Item Description": desc,
                "Qty": qty,
                "Total Price": tot_price,
                "Deli Fee": deli_fee,
            })
          r_ord["items"] = updated_ord_items
        save_restock_to_firebase()
      st.success("အပြောင်းအလဲများကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!")
      st.rerun()
else:
  st.info(
    "💡 တည်းဖြတ်ရန် Restock စာရင်းများ မရှိသေးပါ။ အထက်ပါ **'+ New Order'**"
    " ကိုနှိပ်၍ Order အသစ်အရင်ဖန်တီးပါ။"
  )

# Search / Filter လုပ်ရန် UI ပိုင်း
st.markdown("---")
st.markdown("### 🔍 Search & Filter Orders")
filter_col1, filter_col2 = st.columns(2)

all_suppliers = ["အားလုံး (All)"] + list(
    set([
        ord.get("supplier", "")
        for ord in st.session_state.restock_orders
        if ord.get("supplier")
    ])
)

with filter_col1:
  selected_supplier_filter = st.selectbox(
      "Supplier အလိုက် စစ်ထုတ်ရန်", all_suppliers
  )

with filter_col2:
  search_keyword = st.text_input("Restock ID (သို့) Supplier ဖြင့် ရှာဖွေရန်", "")

st.markdown("---")

# ဇယား (၂): Final Calculated / Summary Restock Orders List
st.markdown("---")
st.subheader("📊 Final Calculated Restock Orders List (Summary)")

filtered_orders = st.session_state.restock_orders
if selected_supplier_filter != "အားလုံး (All)":
  filtered_orders = [
      ord
      for ord in filtered_orders
      if ord.get("supplier") == selected_supplier_filter
  ]

if search_keyword.strip() != "":
  keyword = search_keyword.lower()
  filtered_orders = [
      ord
      for ord in filtered_orders
      if keyword in ord.get("order_id", "").lower()
      or keyword in ord.get("supplier", "").lower()
  ]

if filtered_orders:
  summary_data = []
  for index, ord_data in enumerate(filtered_orders):
    items_df = pd.DataFrame(ord_data.get("items", []))
    if not items_df.empty:
      tp_col = "Total Price" if "Total Price" in items_df.columns else "Total Price"
      if tp_col not in items_df.columns:
        items_df[tp_col] = 0.0
      df_tp = pd.to_numeric(items_df[tp_col], errors="coerce").fillna(0)
      df_qty = pd.to_numeric(items_df["Qty"], errors="coerce").fillna(0)

      deli_col = "Deli Fee" if "Deli Fee" in items_df.columns else "Deli Fee"
      if deli_col not in items_df.columns:
        items_df[deli_col] = 0.0
      df_deli = pd.to_numeric(items_df[deli_col], errors="coerce").fillna(0.0)

      tot_cost = ((df_qty * df_tp) + df_deli).sum()
    else:
      tot_cost = 0.0

    summary_data.append({
        "Restock ID": ord_data["order_id"],
        "Supplier Name": ord_data["supplier"],
        "Time": ord_data["time"],
        "Total Items Cost": f"{tot_cost:,.0f} ကျပ်",
    })

  df_summary = pd.DataFrame(summary_data)
  st.dataframe(df_summary, use_container_width=True, hide_index=True)

  st.write("---")
  st.write("🔍 **View Receipt (အသေးစိတ်ကြည့်ရန်)**")
  selected_view_id = st.selectbox(
      "ပြေစာကြည့်မည့် Restock ID ကို ရွေးချယ်ပါ",
      options=[ord["order_id"] for ord in filtered_orders],
      key="restock_summary_select_id",
  )
  if st.button("📄 Selected Receipt ကို ဖွင့်မည်", key="restock_open_receipt_btn"):
    target_order = next(
        (ord for ord in filtered_orders if ord["order_id"] == selected_view_id),
        None,
    )
    if target_order:
      show_restock_dialog(target_order)
else:
  st.info("ရှာဖွေတွေ့ရှိသော Restock Order များ မရှိပါ။")