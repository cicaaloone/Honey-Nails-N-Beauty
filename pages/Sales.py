import datetime
import io
import pandas as pd
import streamlit as st
from firebase_config import db

st.set_page_config(
    page_title="Honey Nails 'n' Beauty - Sales Order & Receipt", layout="wide"
)

if not st.session_state.get("logged_in", False):
  st.warning("ကျေးဇူးပြု၍ ပထမဦးစွာ Login ဝင်ပါ။")
  st.stop()

st.sidebar.write(f"👤 User: {st.session_state.username}")

if "inventory_items" not in st.session_state:
  try:
    docs = db.collection("inventory").stream()
    st.session_state.inventory_items = [doc.to_dict() for doc in docs]
  except Exception as e:
    st.session_state.inventory_items = []

if "sales_orders" not in st.session_state:
  try:
    s_docs = db.collection("sales_orders").stream()
    st.session_state.sales_orders = [doc.to_dict() for doc in s_docs]
  except Exception as e:
    st.session_state.sales_orders = []


def save_sales_to_firebase():
  try:
    for order in st.session_state.sales_orders:
      db.collection("sales_orders").document(str(order["order_id"])).set(order)
  except Exception as e:
    st.error(f"❌ Sales Orders သိမ်းဆည်းရာတွင် အမှားရှိပါသည်: {e}")


@st.dialog("🧾 Official Receipt / ငွေပြေစာ", width="large")
def show_receipt_dialog(order):
  print_mode_key = f"print_mode_{order['order_id']}"
  if print_mode_key not in st.session_state:
    st.session_state[print_mode_key] = False

  cust_name = order.get("customer", "Customer")
  rec_id = order.get("order_id", "01")

  if st.session_state[print_mode_key]:
    st.markdown(
        f"<script>document.title = 'Honey Nails 'n' Beauty - Receipt - "
        f"{cust_name} ({rec_id})';</script>",
        unsafe_allow_html=True,
    )

  with st.container(border=True):
    col_t1, col_t2 = st.columns([1.5, 4])
    with col_t1:
      if st.session_state[print_mode_key]:
        if st.button("✏️ Edit Mode သို့ ပြန်ရန်", key=f"btn_edit_{order['order_id']}"):
          st.session_state[print_mode_key] = False
          st.rerun()
      else:
        if st.button(
            "🖨️ Print View သို့ ပြောင်းမည်",
            key=f"btn_pview_{order['order_id']}",
            type="primary",
        ):
          st.session_state[print_mode_key] = True
          st.rerun()
    st.markdown("---")

    st.markdown(
        "<h2 style='text-align: center; color: #78350f;'>Honey Nails 'n'"
        " Beauty</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h4 style='text-align: center; color: #92400e;'>OFFICIAL RECEIPT /"
        " ငွေပြေစာ</h4>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    col_info1, col_info2 = st.columns(2)
    with col_info1:
      st.write("**Shop Name:** Honey Nails 'n' Beauty")
      st.write(f"**Customer Name:** {cust_name}")
      st.write(f"**Date & Time:** {order['time']}")
    with col_info2:
      st.write(f"**Receipt No:** REC-{rec_id}")

    st.markdown("---")

    if not st.session_state[print_mode_key]:
      st.markdown(
          "💡 **Inventory မှ ပစ္စည်းအသစ် ထည့်သွင်းရန် (Suggestion / Select)**"
      )
      if "inventory_items" in st.session_state and st.session_state[
          "inventory_items"
      ]:
        inv_options = {
            f"[{item['Item Code']}] {item['Item Description']} (Sell: {item.get('Selling Price (Ks)', 0):,.0f} Ks)": item
            for item in st.session_state["inventory_items"]
        }

        selected_inv_label = st.selectbox(
            "ပစ္စည်း ရွေးချယ်ပါ",
            options=["-- ရွေးချယ်ရန် --"] + list(inv_options.keys()),
            key=f"select_inv_{order['order_id']}",
        )

        if selected_inv_label != "-- ရွေးချယ်ရန် --":
          selected_item_data = inv_options[selected_inv_label]
          if st.button(
              "➕ ရွေးချယ်ထားသော ပစ္စည်းကို ဇယားသို့ ထည့်မည်",
              key=f"add_btn_{order['order_id']}",
          ):
            code_to_add = str(selected_item_data.get("Item Code", "HNB-001"))
            order["items"].append({
                "Item Code": code_to_add,
                "Item Description": selected_item_data["Item Description"],
                "Qty": 1,
                "Price": selected_item_data.get("Selling Price (Ks)", 0.0),
                "Discount": 0.0,
                "Tax": 0.0,
            })
            save_sales_to_firebase()
            st.success("ပစ္စည်း ထည့်ပြီးပါပြီ!")
            st.rerun()
      else:
        st.warning("Inventory ထဲတွင် ပစ္စည်းများ မရှိသေးပါ။")

    st.markdown("---")

    if not order.get("items"):
      order["items"] = []

    df_items = pd.DataFrame(order["items"])
    if not df_items.empty and "Qty" in df_items.columns and "Price" in df_items.columns:
      df_items["Amount"] = (
          df_items["Qty"] * df_items["Price"]
          - df_items.get("Discount", 0)
          + df_items.get("Tax", 0)
      )
    else:
      df_items = pd.DataFrame(columns=[
          "Item Code",
          "Item Description",
          "Qty",
          "Price",
          "Discount",
          "Tax",
          "Amount",
      ])

    if st.session_state[print_mode_key]:
      st.info(
          f"💡 **Print View** (ဖောက်သည်: **{cust_name}**) သို့ ရောက်ရှိနေပါပြီ။"
      )
      st.dataframe(df_items, use_container_width=True, hide_index=True)
      edited_df = df_items
    else:
      st.write("📋 **Receipt Items List (တည်းဖြတ်ရန်)**")
      edited_df = st.data_editor(
          df_items,
          use_container_width=True,
          hide_index=True,
          num_rows="dynamic",
          key=f"editor_{order['order_id']}",
      )

      code_to_desc = {}
      desc_to_code = {}
      if "inventory_items" in st.session_state:
        for inv_item in st.session_state["inventory_items"]:
          c_str = str(inv_item.get("Item Code", "")).strip()
          d_str = str(inv_item.get("Item Description", "")).strip()
          if c_str:
            code_to_desc[c_str] = d_str
          if d_str:
            desc_to_code[d_str] = c_str

      updated_items = []
      for _, row in edited_df.iterrows():
        code = str(row["Item Code"]).strip() if pd.notna(row["Item Code"]) else ""
        desc = (
            str(row["Item Description"]).strip()
            if pd.notna(row["Item Description"])
            else ""
        )

        if code and code in code_to_desc and (not desc or desc == "New Item"):
          desc = code_to_desc[code]
        elif desc and desc in desc_to_code and (not code or code == "HNB-999"):
          code = desc_to_code[desc]

        if not code:
          code = "HNB-999"
        if not desc:
          desc = "New Item"

        qty = int(row["Qty"]) if pd.notna(row["Qty"]) else 1
        price = float(row["Price"]) if pd.notna(row["Price"]) else 0.0
        discount = float(row["Discount"]) if pd.notna(row["Discount"]) else 0.0
        tax = float(row["Tax"]) if pd.notna(row["Tax"]) else 0.0

        updated_items.append({
            "Item Code": code,
            "Item Description": desc,
            "Qty": qty,
            "Price": price,
            "Discount": discount,
            "Tax": tax,
        })
      order["items"] = updated_items
      save_sales_to_firebase()

    if not edited_df.empty and "Qty" in edited_df.columns and "Price" in edited_df.columns:
      total_amount = (
          edited_df["Qty"] * edited_df["Price"]
          - edited_df.get("Discount", 0)
          + edited_df.get("Tax", 0)
      ).sum()
    else:
      total_amount = 0.0

    st.markdown("---")
    input_col1, input_col2 = st.columns(2)
    with input_col1:
      currency_choice = st.selectbox(
          "💱 Currency ရွေးချယ်ပါ",
          ["ကျပ် (Ks)", "ယွမ် (¥)"],
          key=f"curr_{order['order_id']}",
      )
      curr_symbol = "¥" if "ယွမ်" in currency_choice else "Ks"

    with input_col2:
      default_paid = order.get("paid_amount", total_amount)
      paid_amount = st.number_input(
          f"💵 ပေးချေပြီးငွေ ({curr_symbol})",
          min_value=0.0,
          max_value=float(total_amount if total_amount > 0 else 10000000.0),
          value=float(
              default_paid if default_paid <= total_amount else total_amount
          ),
          step=1000.0,
          key=f"paid_input_{order['order_id']}",
      )
      order["paid_amount"] = paid_amount
      save_sales_to_firebase()

    balance_due = total_amount - paid_amount

    st.markdown("---")
    st.markdown(f"**စုစုပေါင်းကျသင့်ငွေ:** {total_amount:,.0f} {curr_symbol}")
    st.markdown(f"**ပေးချေပြီးငွေ:** {paid_amount:,.0f} {curr_symbol}")
    st.markdown(
        f"<span style='color:red; font-weight:bold;'>ကျန်ငွေ:</span>"
        f" {balance_due:,.0f} {curr_symbol}",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.write("Thank you for choosing Honey Nails 'n' Beauty! / ကျေးဇူးတင်ရှိပါသည်။")


@st.dialog("➕ New Sales Order ဖန်တီးရန်")
def new_order_dialog():
  next_order_num = len(st.session_state.sales_orders) + 1
  auto_order_id = f"SO-{next_order_num:02d}"
  current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  st.write(f"**Order ID (Auto):** {auto_order_id}")
  customer = st.text_input("Customer Name")
  st.write(f"**Time (Now):** {current_time}")

  if st.button("Order အသစ် သိမ်းဆည်းမည်"):
    if customer:
      new_order = {
          "order_id": auto_order_id,
          "customer": customer,
          "time": current_time,
          "items": [],
          "paid_amount": 0.0,
      }
      st.session_state.sales_orders.append(new_order)
      save_sales_to_firebase()
      st.success("Order အသစ် အောင်မြင်စွာ ထည့်ပြီးပါပြီ!")
      st.rerun()
    else:
      st.warning("ကျေးဇူးပြု၍ Customer Name ထည့်ပါ။")


@st.dialog("🗑️ Sales Order ဖျက်ရန်")
def delete_order_dialog():
  if not st.session_state.sales_orders:
    st.warning("ဖျက်ရန် Order များ မရှိသေးပါ။")
    return

  order_ids = [ord["order_id"] for ord in st.session_state.sales_orders]
  selected_id = st.selectbox("ဖျက်မည့် Order ID ကို ရွေးချယ်ပါ", order_ids)

  if st.button("သေချာပေါက် ဖျက်မည်", type="primary"):
    st.session_state.sales_orders = [
        ord
        for ord in st.session_state.sales_orders
        if ord["order_id"] != selected_id
    ]
    try:
      db.collection("sales_orders").document(str(selected_id)).delete()
    except Exception as e:
      st.error(f"ဖျက်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")
    st.success(f"Order ID: {selected_id} ကို ဖျက်ပြီးပါပြီ!")
    st.rerun()


st.title("📊 Sales Orders Management")
st.write(
    f"လက်ရှိဝင်ရောက်ထားသူ: **{st.session_state.username}** ("
    f"{st.session_state.role})"
)

top_col1, top_col2, top_col3 = st.columns([6, 1.2, 1.2])
with top_col2:
  if st.button("🗑️ Delete"):
    delete_order_dialog()
with top_col3:
  if st.button("➕ New Order"):
    new_order_dialog()

st.markdown("---")

# ==========================================
# 📦 CONTAINER 1: Orders List (အပေါ်ပိုင်း - Original View Receipt Button Restored)
# ==========================================
with st.container(border=True):
  st.subheader("📋 Orders List (အရောင်းစာရင်းများ)")

  header_cols = st.columns([1.5, 2, 2, 2, 1.5])
  header_cols[0].markdown("**Order ID**")
  header_cols[1].markdown("**Customer Name**")
  header_cols[2].markdown("**Payment Status**")
  header_cols[3].markdown("**Time**")
  header_cols[4].markdown("**Actions**")
  st.markdown("---")

  if "sales_orders" in st.session_state and st.session_state.sales_orders:
    for index, ord_data in enumerate(st.session_state.sales_orders):
      items_list = ord_data.get("items", [])
      if items_list:
        items_df = pd.DataFrame(items_list)
        if "Qty" in items_df.columns and "Price" in items_df.columns:
          tot = (
              items_df["Qty"] * items_df["Price"]
              - items_df.get("Discount", 0)
              + items_df.get("Tax", 0)
          ).sum()
        else:
          tot = 0.0
      else:
        tot = 0.0

      paid = ord_data.get("paid_amount", tot)
      bal = tot - paid

      if paid == 0:
        p_status = "Unpaid"
      elif bal == 0:
        p_status = "Paid"
      else:
        p_status = "Deposit"

      cols = st.columns([1.5, 2, 2, 2, 1.5])
      cols[0].write(f"**{ord_data['order_id']}**")
      cols[1].write(ord_data["customer"])
      cols[2].write(p_status)
      cols[3].write(ord_data["time"])

      with cols[4]:
        if st.button("🔍 View Receipt", key=f"btn_{ord_data['order_id']}_{index}"):
          show_receipt_dialog(ord_data)
  else:
    st.info("အရောင်းအော်ဒါများ မရှိသေးပါ။")

st.markdown("---")

# ==========================================
# 🛒 CONTAINER 2: All Items Summary (အောက်ပိုင်း)
# ==========================================
with st.container(border=True):
  st.subheader("🛍️ Best Selling Items Summary (အရောင်းရဆုံး ပစ္စည်းများ အကျဉ်းချုပ်)")

  if "sales_orders" in st.session_state and st.session_state.sales_orders:
    all_sales_items = []
    for ord_data in st.session_state.sales_orders:
      for itm in ord_data.get("items", []):
        all_sales_items.append({
            "Item Code": itm.get("Item Code"),
            "Item Description": itm.get("Item Description"),
            "Qty": int(itm.get("Qty", 0)),
            "Price": float(itm.get("Price", 0.0)),
            "Amount": (
                int(itm.get("Qty", 0)) * float(itm.get("Price", 0.0))
            )
            - float(itm.get("Discount", 0.0))
            + float(itm.get("Tax", 0.0)),
        })

    if all_sales_items:
      df_items = pd.DataFrame(all_sales_items)

      df_grouped = df_items.groupby(
          ["Item Code", "Item Description"], as_index=False
      ).agg({"Qty": "sum", "Price": "mean", "Amount": "sum"})

      df_grouped = df_grouped.sort_values(by="Qty", ascending=False)

      st.dataframe(df_grouped, use_container_width=True, hide_index=True)
    else:
      st.info("ပြေစာများထဲတွင် ပစ္စည်းအချက်အလက်များ မရှိသေးပါ။")
  else:
    st.info("ပြသရန် အရောင်းအချက်အလက်များ မရှိသေးပါ။")