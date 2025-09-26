import requests
import json
import sys
from datetime import datetime, timedelta
import time
import os
import csv 

SALESMAN_MAP = {
    "OS ÑUÑOA": "OS ÑUÑOA",
    "OS FLORIDA": "OS FLORIDA",
    "OS PUENTE": "OS PUENTE",
    "OS APUMANQUE": "OS LAS CONDES",
    "OS INDEPENDENCIA": "OS INDEPENDENCIA",
    "OS QUILIN": "OS QUILIN",
    "OS WEB": "OS WEB"
}

BASE_URL = "http://45.82.249.153:8008"
CSV_FILE = "processed_orders.csv"

def load_existing_order_ids():
    """Load all salesOrderIds already logged in CSV file"""
    if not os.path.isfile(CSV_FILE):
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {int(row["salesOrderId"]) for row in reader if row.get("salesOrderId")}
    
def append_to_csv(order_id):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["salesOrderId", "timestamp"])  # header
        writer.writerow([order_id, datetime.now().isoformat()])
    print(f"📂 Logged SalesOrder {order_id} to {CSV_FILE}")

def get_all_customers(base_url, headers):
    url = f"{base_url}/customer/"
    customers = []
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print("❌ Error fetching customers:", resp.status_code, resp.text)
            break
        data = resp.json()
        customers.extend(data.get("results", []))
        url = data.get("next")   # follow pagination
    return customers

def get_all_goods(base_url, headers):
    url = f"{base_url}/goods/"
    goods = []
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print("❌ Error fetching goods:", resp.status_code, resp.text)
            break
        data = resp.json()
        goods.extend(data.get("results", []))
        url = data.get("next")   # follow pagination
    return goods

def create_new_DN(salesorder):
        
    # --- Step 1: Login ---
    login_payload = {"name": "admin", "password": "8834.FyJ"}
    resp = requests.post(f"{BASE_URL}/login/", json=login_payload)
    data = resp.json()

    if data.get("code") == "200":
        token = data["data"]["openid"]

        headers = {
            "token": token,
            "operator": "81"  
        }

        # # --- Step 2: Get all customers ---
        # customers = get_all_customers(BASE_URL, headers)
        # # print(f"📋 Total customers fetched: {len(customers)}")
        # for c in customers:
        #     print("-", c.get("customer_name"))

        # customer_name = customers[0]["customer_name"] if customers else "Customer-1"

        # # --- Step 3: Get all goods ---
        # goods = get_all_goods(BASE_URL, headers)
        # # print(f"\n🛒 Total goods fetched: {len(goods)}")
        # for g in goods:
        #     print("-", g.get("goods_code"), "|", g.get("goods_desc"))

        # goods_codes = [g["goods_code"] for g in goods] if goods else ["A000041"]
        # goods_qtys = [10] * len(goods_codes)
        # --- Step 4: Show existing DN list ---
        # dn_list_resp = requests.get(f"{BASE_URL}/dn/list/", headers=headers)
        # if dn_list_resp.status_code == 200:
        #     dn_list = dn_list_resp.json().get("results", [])
        #     print("\n📑 Existing DNs:")
        #     for dn in dn_list:
        #         print("-", dn)
                # time.sleep(1000)
        # --- Extract from salesorder JSON ---
        customer_name = salesorder.get("salesman", "OS WEB")
        items = salesorder.get("items", [])

        goods_codes = [item["sku"] for item in items]
        goods_qtys = [item["quantity"] for item in items]

        # --- Step 4: Create DN header ---
        new_dn_payload = {"creater": "admin"}
        res_dn = requests.post(f"{BASE_URL}/dn/list/", json=new_dn_payload, headers=headers)
        # print("\n📦 DN header raw response:", res_dn.status_code, res_dn.text)

        dn_code = res_dn.json().get("dn_code")
        if dn_code:
            print("✅ Got dn_code:", dn_code)

            # --- Step 5: Add DN details ---
            detail_payload = {
                "dn_code": dn_code,
                "customer": customer_name,
                "goods_code": goods_codes,
                "goods_qty": goods_qtys,
                "creater": "admin"
            }

            # print("\n➡️ JSON to send:", json.dumps(detail_payload, indent=2))
            res_detail = requests.post(f"{BASE_URL}/dn/detail/", json=detail_payload, headers=headers)
            print("DN detail response:", res_detail.status_code, res_detail.text)
            return res_detail.status_code

    else:
        print("❌ Login failed:", data)

class LaudusAPIsales:
    hostAPI = "https://api.laudus.cl"
    credential = {"token": "", "expiration": ""}

    def getToken(self):
        requestLoginSchema = {
            "userName": "api guias",
            "password": "77VV77VV",
            "companyVATId": "76278745-8"
        }
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        try:
            request = requests.post(self.hostAPI + "/security/login",
                                    data=json.dumps(requestLoginSchema),
                                    headers=headers)
            if request.status_code == 200:
                self.credential = request.json()
                print("✅ token =", self.credential["token"])
                return True
            else:
                print("❌ Login error:", request.text)
                return False
        except Exception as e:
            print("Unexpected error:", e)
            return False

    def isValidToken(self):
        if "expiration" in self.credential and self.credential["expiration"]:
            ltNow = datetime.now()
            ltToken = datetime.fromisoformat(self.credential["expiration"]).replace(tzinfo=None)
            if ltToken < ltNow:
                return self.getToken()
            return True
        return self.getToken()

    def getSalesOrdersList(self):
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

        payload = {
            "options": {"offset": 0, "limit": 100},
            "fields": ["salesOrderId", "createdAt"],
            "filterBy": [
                {"field": "createdAt", "operator": ">=", "value": start_date + "T00:00:00"},
                {"field": "createdAt", "operator": "<=", "value": end_date + "T23:59:59"}
            ],
            "orderBy": [{"field": "createdAt", "direction": "ASC"}]
        }

        if not self.isValidToken():
            return []

        url = self.hostAPI + "/sales/orders/list"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            return [item["salesOrderId"] for item in result]
        elif response.status_code == 204:
            print("✅ No sales orders in given date range")
            return []
        else:
            print("❌ Error:", response.status_code, response.text)
            return []

    def getSalesorder(self, salesOrderId: int, save_dir="sales_orders"):
        if not self.isValidToken():
            return None

        url = f"{self.hostAPI}/sales/orders/{salesOrderId}"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()

            # Safely extract salesman name (might be null)
            raw_salesman = data.get("salesman", {}).get("name") if data.get("salesman") else None
            salesman_name = SALESMAN_MAP.get(raw_salesman, raw_salesman)  # map if exists, else keep raw/null

            # Default to OS WEB if missing/None
            if not salesman_name:
                salesman_name = "OS WEB"

            # Extract items (sku + quantity only)
            items = []
            for item in data.get("items", []):
                sku = item.get("product", {}).get("sku")
                qty = int(item.get("quantity"))
                items.append({"sku": sku, "quantity": qty})

            filtered_data = {
                "salesOrderId": data.get("salesOrderId"),
                "salesman": salesman_name,
                "items": items
            }

            # # ensure save folder exists
            # os.makedirs(save_dir, exist_ok=True)
            # filtered_file_path = os.path.join(save_dir, f"salesorder_{salesOrderId}_filtered.json")

            # # save to JSON file
            # with open(filtered_file_path, "w", encoding="utf-8") as f:
            #     json.dump(filtered_data, f, ensure_ascii=False, indent=2)

            # print(f"✅ Saved filtered SalesOrder {salesOrderId} → {filtered_file_path}")
            # file_path = os.path.join(save_dir, f"salesorder_{salesOrderId}.json")
            # # save to JSON file
            # with open(file_path, "w", encoding="utf-8") as f:
            #     json.dump(data, f, ensure_ascii=False, indent=2)

            # print(f"✅ Saved SalesOrder {salesOrderId} → {file_path}")
            return filtered_data
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None


if __name__ == '__main__':
    salesorder = LaudusAPIsales()
    if salesorder.getToken():
        processed_ids = load_existing_order_ids()
        order_ids = salesorder.getSalesOrdersList()
        print(f"Sales Order ID list: {order_ids}")

        for oid in order_ids:
            if oid in processed_ids:
                print(f"⏭️ Skipping already processed order {oid}")
                continue

            print(f"Processing Sales Order ID: {oid}")
            filtered_data = salesorder.getSalesorder(oid)
            if not filtered_data:
                continue

            status = create_new_DN(filtered_data)
            if status == 200:
                append_to_csv(oid, filtered_data["salesman"])

    input("\n✅ Finished. Press Enter to close...")

