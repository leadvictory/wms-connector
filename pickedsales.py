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

def load_existing_order_ids(picked_dns=None):
    """
    Load salesOrderIds already logged in CSV file.
    1. Match only records with dn_code in picked_dns
    2. Skip orders where salesWaybillId is empty/null
    """
    if not os.path.isfile(CSV_FILE):
        return set()

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = []
        for row in reader:
            if not row.get("salesOrderId"):
                continue
            sales_order_id = int(row["salesOrderId"])
            dn_code = row.get("DN code")
            waybill_id = row.get("salesWaybillId") or ""

            # skip if waybill not created yet
            if waybill_id.strip():
                continue  

            records.append((sales_order_id, dn_code))

    if picked_dns:
        picked_dn_codes = {dn["dn_code"] for dn in picked_dns}
        return {oid for oid, dn_code in records if dn_code in picked_dn_codes}

    return {oid for oid, _ in records}

def log_waybill_created(order_id, waybill_id):
    """Update existing row with waybillId, or add new row if not present"""
    rows = []
    file_exists = os.path.isfile(CSV_FILE)
    
    if file_exists:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

    updated = False
    for row in rows:
        if str(row.get("salesOrderId")) == str(order_id):
            row["salesWaybillId"] = str(waybill_id)
            # print(row)
            updated = True
            break

    if not updated:
        # add new row if not found
        rows.append({
            "salesOrderId": str(order_id),
            "DN code": "",
            "timestamp": datetime.now().isoformat(),
            "salesWaybillId": str(waybill_id)
        })

    # write all rows back
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["salesOrderId", "DN code", "timestamp", "salesWaybillId"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"📂 Updated SalesOrder {order_id} → Waybill {waybill_id}")

def get_picked_dns():
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
        all_dns = []
        url = f"{BASE_URL}/dn/list/"

        while url:
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                print("❌ Error fetching:", resp.status_code, resp.text)
                break

            data = resp.json()
            results = data.get("results", [])
            all_dns.extend(results)

            # follow pagination
            url = data.get("next")
            if url:
                # convert "none://" → "http://"
                if url.startswith("none://"):
                    url = url.replace("none://", "http://")
            else:
                url = None

        # ✅ Filter only dn_status == 4
        filtered_dns = [dn for dn in all_dns if dn.get("dn_status") == 4]
        return filtered_dns

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
                # print("✅ token =", self.credential["token"])
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

            # remove unwanted top-level fields
            for field in [
                "salesOrderId", "createdAt", "dueDate", "locked", "approved", "approvedBy",
                "deliveryDate", "deliveryTimeFrame", "source", "sourceOrderId",
                "amountPaid", "amountPaidCurrencyCode", "invoiceDocType"
            ]:
                data.pop(field, None)

            # 🔹 Add warehouse and isSale
            data["warehouse"] = {
                "warehouseId": "005",
                "name": "BODEGA MACUL"
            }
            data["isSale"] = True
            data["docType"] = {
                "docTypeId": 52,
                "name": "Guía de Despacho Electrónica"
            }
            data["deliverySIIType"] = "2"
            data["customFields"]["LOCAL_"] = "WEB"

            # 🔹 Clean up items
            if "items" in data and isinstance(data["items"], list):
                for item in data["items"]:
                    item.pop("itemId", None)
                    item.pop("itemOrder", None)
                    if "product" in item and isinstance(item["product"], dict):
                        item["product"].pop("productId", None)
            # Optional: save modified JSON
            os.makedirs(save_dir, exist_ok=True)
            filename = os.path.join(save_dir, f"sales_order_{salesOrderId}.json")
            with open(filename, "w", encoding="utf-8") as f:
                import json
                json.dump(data, f, indent=4, ensure_ascii=False)

            return data
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None

    def createsalesWaybill(self, payload: str, order_id=None):
        if not self.isValidToken():
            print("Failed to get a valid token")
            return None

        url = f"{self.hostAPI}/sales/waybills/"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            "Content-Type": "application/json",
            'Accept': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=payload.encode('utf-8'))

            if response.status_code == 200:
                data = response.json()
                waybill_id = data.get("salesWaybillId", "unknown")
                print(f"✅ success: Waybill {waybill_id} created")

                if order_id:
                    log_waybill_created(order_id, waybill_id)
                return waybill_id

            elif response.status_code == 422:
                print(f"⚠️ Already exists: {response.text}")
            else:
                print("Upload failed:", response.text)
        except Exception as e:
            print("Request failed:", e)
        return None 
      
if __name__ == '__main__':
    picked_dns = get_picked_dns()
    print("\n📑 DNs with Picked status:")
    for dn in picked_dns:
        print(f"- {dn['dn_code']} | Customer: {dn['customer']} | ID: {dn['id']}")

    processed_ids = load_existing_order_ids(picked_dns)
    print(f"Matching SalesOrder Ids: {processed_ids}")

    salesorder = LaudusAPIsales()
    if salesorder.getToken():
        for oid in processed_ids:
            filtered_data = salesorder.getSalesorder(oid)
            if filtered_data:
                payload_str = json.dumps(filtered_data, ensure_ascii=False)
                salesorder.createsalesWaybill(payload_str, order_id=oid)
                time.sleep(1)