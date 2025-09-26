import requests, json
import time 

BASE_URL = "http://45.82.249.153:8008"

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


# --- Step 1: Login ---
login_payload = {"name": "admin", "password": "8834.FyJ"}
resp = requests.post(f"{BASE_URL}/login/", json=login_payload)
data = resp.json()

if data.get("code") == "200":
    token = data["data"]["openid"]

    headers = {
        "token": token,
        "operator": "81"   # replace with valid staff.id you captured
    }

    # --- Step 2: Get all customers ---
    customers = get_all_customers(BASE_URL, headers)
    print(f"📋 Total customers fetched: {len(customers)}")
    for c in customers:
        print("-", c.get("customer_name"))

    customer_name = customers[0]["customer_name"] if customers else "Customer-1"

    # --- Step 3: Get all goods ---
    goods = get_all_goods(BASE_URL, headers)
    print(f"\n🛒 Total goods fetched: {len(goods)}")
    for g in goods:
        print("-", g.get("goods_code"), "|", g.get("goods_desc"))

    time.sleep(1000)
    goods_codes = [g["goods_code"] for g in goods] if goods else ["A000041"]
    goods_qtys = [10] * len(goods_codes)

    # --- Step 4: Create DN header ---
    new_dn_payload = {"creater": "admin"}
    res_dn = requests.post(f"{BASE_URL}/dn/list/", json=new_dn_payload, headers=headers)
    print("\n📦 DN header raw response:", res_dn.status_code, res_dn.text)

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

        print("\n➡️ JSON to send:", json.dumps(detail_payload, indent=2))
        res_detail = requests.post(f"{BASE_URL}/dn/detail/", json=detail_payload, headers=headers)
        print("DN detail response:", res_detail.status_code, res_detail.text)

else:
    print("❌ Login failed:", data)
