import requests
import json
import sys
from datetime import datetime, timedelta
import time
import os

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
            "orderBy": [{"field": "createdAt", "direction": "DESC"}]
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

            # ensure save folder exists
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, f"salesorder_{salesOrderId}.json")

            # save to JSON file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ Saved SalesOrder {salesOrderId} → {file_path}")
            return data
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None


if __name__ == '__main__':
    salesorder = LaudusAPIsales()
    if salesorder.getToken():
        order_ids = salesorder.getSalesOrdersList()
        for oid in order_ids:
            salesorder.getSalesorder(oid)
            time.sleep(100)  # small pause between calls
