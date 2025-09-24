import requests, json

BASE_URL = "http://45.82.249.153:8008"

# --- Step 1: Login ---
login_payload = {"name": "admin", "password": "8834.FyJ"}

resp = requests.post(f"{BASE_URL}/login/", json=login_payload)
data = resp.json()

if data.get("code") == "200":
    token = data["data"]["openid"]

    # headers must match exactly (lowercase)
    headers = {
        "token": token,
        "operator": "81"   # replace with valid staff.id you captured
    }

    # --- Step 2: Get customers ---
    customers_resp = requests.get(f"{BASE_URL}/customer/", headers=headers)
    customers = customers_resp.json().get("results", [])
    print("📋 Customers:")
    for c in customers:
        print("-", c.get("customer_name"))

    customer_name = customers[0]["customer_name"] if customers else "Customer-1"

    # --- Step 3: Get goods ---
    goods_resp = requests.get(f"{BASE_URL}/goods/", headers=headers)
    goods = goods_resp.json().get("results", [])
    print("\n🛒 Goods available:")
    for g in goods:
        print("-", g.get("goods_code"), "|", g.get("goods_desc"))

    goods_codes = [goods[0]["goods_code"]] if goods else ["A000041"]
    goods_qtys = [10]

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
        print("DN detail response:", res_detail.status_code)

else:
    print("❌ Login failed:", data)
