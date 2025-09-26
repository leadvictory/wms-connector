import requests

BASE_URL = "http://45.82.249.153:8008"

def delete_all_dns():
    # --- Step 1: Login ---
    login_payload = {"name": "admin", "password": "8834.FyJ"}
    resp = requests.post(f"{BASE_URL}/login/", json=login_payload)
    data = resp.json()

    if data.get("code") != "200":
        print("❌ Login failed:", data)
        return

    token = data["data"]["openid"]
    headers = {"token": token, "operator": "81"}

    # --- Step 2: Get all DN list ---
    url = f"{BASE_URL}/dn/list/"
    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print("❌ Error fetching DN list:", res.status_code, res.text)
            break

        data = res.json()
        for dn in data.get("results", []):
            dn_id = dn.get("id")
            dn_code = dn.get("dn_code")
            if dn_id:
                del_url = f"{BASE_URL}/dn/list/{dn_id}/"
                del_res = requests.delete(del_url, headers=headers)
                if del_res.status_code in (200, 204):
                    print(f"🗑️ Deleted DN {dn_code} (id={dn_id})")
                else:
                    print(f"⚠️ Failed to delete DN {dn_code} (id={dn_id}): {del_res.status_code} {del_res.text}")

        url = data.get("next")  # follow pagination if needed

if __name__ == "__main__":
    delete_all_dns()
