import requests

BASE_URL = "http://45.82.249.153:8008"

# Step 1: Admin login
login_payload = {"name": "admin", "password": "8834.FyJ"}
resp = requests.post(f"{BASE_URL}/login/", json=login_payload)
data = resp.json()

if data.get("code") == "200":
    token = data["data"]["openid"]
    headers = {"Token": token}

    # --- Get Suppliers ---
    suppliers_resp = requests.get(f"{BASE_URL}/supplier/", headers=headers)
    suppliers = suppliers_resp.json().get("results", [])
    print("📦 Suppliers:")
    for s in suppliers:
        print("-", s.get("supplier_name"))

    # --- Get Goods ---
    goods_resp = requests.get(f"{BASE_URL}/goods/", headers=headers)
    goods = goods_resp.json().get("results", [])
    print("\n🛒 Goods Codes:")
    for g in goods:
        print("-", g.get("goods_code"), g.get("goods_desc"))

else:
    print("❌ Login failed:", data)

if data.get("code") == "200":
    token = data["data"]["openid"]
    headers = {"Token": token}

    # --- Get all ASN list ---
    asn_list_resp = requests.get(f"{BASE_URL}/asn/list/", headers=headers)
    if asn_list_resp.status_code == 200:
        asn_list = asn_list_resp.json().get("results", [])
        print("📦 Current ASN List:")
        for a in asn_list:
            print("-", a.get("asn_code"), "| supplier:", a.get("supplier"), "| status:", a.get("asn_status"))
    else:
        print("⚠️ Could not fetch ASN list:", asn_list_resp.text)

    # --- Create new ASN header ---
    new_asn_payload = {"creater": "admin"}
    res_asn = requests.post(f"{BASE_URL}/asn/list/", json=new_asn_payload, headers=headers)
    if res_asn.status_code == 200:
        asn_code = res_asn.json().get("asn_code")
        print("\n✅ New ASN created:", asn_code)
    else:
        print("⚠️ ASN init failed:", res_asn.text)
        exit()

    # --- Add ASN details ---
    detail_payload = {
        "asn_code": asn_code,
        "supplier": "Supplier Name-17",     # must exist in /supplier/
        "goods_code": ["A000041", "A000042"],  # must exist in /goods/
        "goods_qty": [100, 50],
        "creater": "admin"
    }
    res_detail = requests.post(f"{BASE_URL}/asn/detail/", json=detail_payload, headers=headers)
    print("ASN detail status:", res_detail.status_code)
    # print("ASN detail raw:", res_detail.text)

else:
    print("❌ Login failed:", data)