import requests
import json
import sys
from collections import OrderedDict
from datetime import datetime
from datetime import datetime, timedelta

class LaudusAPIsales:
    
    hostAPI = "https://api.laudus.cl"
    credential = {"token": "", "expiration": ""}
    account = {}
    customer = {}

    def getToken(self):

        vReturn = False
        self.credential = {}

        requestLoginSchema = {"userName": "", "password": "", "companyVATId": ""}
        requestLoginSchema["userName"] = "api guias"
        requestLoginSchema["password"] = "77VV77VV"
        requestLoginSchema["companyVATId"] = "76278745-8"
        # requestLoginSchema["companyVATId"] = "76194079-1"
        
        requestBodyJson = json.dumps(requestLoginSchema)
        requestHeaders = {"Content-type": "application/json", "Accept": "application/json"}
        
        print("-----------------------<< Get Token >>-----------------------")
        
        try:
            request = requests.post(self.hostAPI + "/security/login", data=requestBodyJson, headers=requestHeaders)
            respondStatusCode = request.status_code

            if respondStatusCode == requests.codes.ok:
                vReturn = True
                self.credential = json.loads(request.text)
                print("token = " + self.credential["token"])
                print("expiration = " + self.credential["expiration"])
            else:
                vReturn = False
                requestError = json.loads(request.text)
                requestErrorMessage = requestError.get('message', '')
                print('Login error: ' + requestErrorMessage)
        except:
            vReturn = False
            print("Unexpected error:", sys.exc_info()[0])
        
        return vReturn
    
    ##########################################################################################

    def isValidToken(self):
        # Checks if the stored token is valid; if not, retrieves a new one

        vReturn = True

        if "expiration" in self.credential and len(self.credential["expiration"]) > 0:
            ltNow = datetime.now()
            ltToken = datetime.fromisoformat(self.credential["expiration"])
            ltToken = ltToken.replace(tzinfo=None)
            if ltToken < ltNow:
                return self.getToken()
            else:
                return vReturn
        else:
            return self.getToken()

    ##########################################################################################

    def getWaybillsList(self):
        print("-----------------------<< Get Waybills List >>-----------------------")

        yesterday = datetime.now() - timedelta(days=8)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = start_date  # Same day range

        payload = {
            "options": {
                "offset": 0,
                "limit": 100
            },
            "fields": [
                "salesWaybillId", "issuedDate"
            ],
            "filterBy": [
                {
                    "field": "issuedDate",
                    "operator": ">=",
                    "value": start_date + "T00:00:00"
                },
                {
                    "field": "issuedDate",
                    "operator": "<=",
                    "value": start_date + "T23:59:59"
                }
            ],
            "orderBy": [
                {
                    "field": "issuedDate",
                    "direction": "DESC"
                }
            ]
        }

        if not self.isValidToken():
            print("Failed to get a valid token")
            return []

        url = self.hostAPI + "/sales/waybills/list"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == requests.codes.ok:
                result = response.json()
                sales_ids = [item["salesWaybillId"] for item in result]
                print(f"Waybill IDs: {sales_ids}")
                return sales_ids
            else:
                print("Error:", response.status_code, response.text)
                return []
        except Exception as e:
            print("Unexpected error:", e)
            return []

    def getSalesWaybill(self, salesWaybillId: int):
        print(f"-----------------------<< Get Waybill {salesWaybillId} >>-----------------------")

        if not self.isValidToken():
            print("Failed to get a valid token")
            return None

        url = f"{self.hostAPI}/sales/waybills/{salesWaybillId}"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == requests.codes.ok:
                data = response.json()

                customer_id = data.get("customer", {}).get("customerId")
                dte = data.get("DTE", {})
                track_id = dte.get("trackId")
                document_status = dte.get("documentStatus")
                upload_status = dte.get("uploadStatus")
                sent_to_customer_at = dte.get("sentToCustomerAt")

                if (
                    customer_id == 336 and
                    track_id and
                    document_status == "0" and
                    upload_status == "" and
                    sent_to_customer_at is not None
                ):
                    # Save the original waybill
                    with open(f"waybill_{salesWaybillId}.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    # print(f"✅ Saved to waybill_{salesWaybillId}.json")

                    # Create new simplified JSON
                    transformed = {
                        "docType": data.get("docType"),
                        "docNumber": abs(data.get("salesWaybillId", 0)),
                        "description": "",
                        "supplier": {
                            "supplierId": 1,
                            "name": "IMPORTADORA NECGROUP SPA",
                            "legalName": "IMPORTADORA NECGROUP SPA",
                            "VATId": "76.278.745-8"
                        },
                        "warehouse": {
                            "warehouseId": data.get("warehouse", {}).get("warehouseId"),
                            "name": "MALL QUILIN" 
                        },
                        "issuedDate": data.get("issuedDate"), 
                        "nullDoc": data.get("nullDoc"),
                        "notes": "",
                        "isSale": False,
                        "items": []
                    }

                    for item in data.get("items", []):
                        product = item.get("product", {})
                        transformed_item = {
                            "product": {
                                "sku": product.get("sku"),
                                "description": product.get("description"),
                                "unitOfMeasure": product.get("unitOfMeasure"),
                                "allowFreeDescription": product.get("allowFreeDescription"),
                                "applyGeneralVATRate": product.get("applyGeneralVATRate"),
                                "VATRate": 19,  # Hardcoded as per example
                                "productUnitCost": item.get("unitPrice")  # Hardcoded as per example
                            },
                            "itemDescription": item.get("itemDescription"),
                            "quantity": int(item.get("quantity", 1)),
                            "originalUnitCost": item.get("originalUnitPrice"),
                            "currencyCode": item.get("currencyCode", "CLP"),
                            "parityToMainCurrency": item.get("parityToMainCurrency", 1),
                            "unitCost": item.get("UnitPrice")
                        }
                        transformed["items"].append(transformed_item)

                    with open(f"transformed_{salesWaybillId}.json", "w", encoding="utf-8") as f:
                        json.dump(transformed, f, ensure_ascii=False, indent=2)
                    # print(f"✅ Saved transformed file to transformed_{salesWaybillId}.json")

                    return data

                else:
                    print(f"Waybill {salesWaybillId} does not meet filter conditions.")
                    return None

            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print("Unexpected error:", e)
            return None
        
class LaudusAPIpurchase:
    
    hostAPI = "https://api.laudus.cl"
    credential = {"token": "", "expiration": ""}
    account = {}
    customer = {}

    def getToken(self):

        vReturn = False
        self.credential = {}

        requestLoginSchema = {"userName": "", "password": "", "companyVATId": ""}
        requestLoginSchema["userName"] = "api guias"
        requestLoginSchema["password"] = "77VV77VV"
        # requestLoginSchema["companyVATId"] = "76278745-8"
        requestLoginSchema["companyVATId"] = "76194079-1"
        
        requestBodyJson = json.dumps(requestLoginSchema)
        requestHeaders = {"Content-type": "application/json", "Accept": "application/json"}
        
        print("-----------------------<< Get Token >>-----------------------")
        
        try:
            request = requests.post(self.hostAPI + "/security/login", data=requestBodyJson, headers=requestHeaders)
            respondStatusCode = request.status_code

            if respondStatusCode == requests.codes.ok:
                vReturn = True
                self.credential = json.loads(request.text)
                print("token = " + self.credential["token"])
                print("expiration = " + self.credential["expiration"])
            else:
                vReturn = False
                requestError = json.loads(request.text)
                requestErrorMessage = requestError.get('message', '')
                print('Login error: ' + requestErrorMessage)
        except:
            vReturn = False
            print("Unexpected error:", sys.exc_info()[0])
        
        return vReturn

    ##########################################################################################

    def isValidToken(self):
        # Checks if the stored token is valid; if not, retrieves a new one

        vReturn = True

        if "expiration" in self.credential and len(self.credential["expiration"]) > 0:
            ltNow = datetime.now()
            ltToken = datetime.fromisoformat(self.credential["expiration"])
            ltToken = ltToken.replace(tzinfo=None)
            if ltToken < ltNow:
                return self.getToken()
            else:
                return vReturn
        else:
            return self.getToken()

    ##########################################################################################

    def getWaybillsList(self):
        print("-----------------------<< Get Waybills List >>-----------------------")

        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')  # Same day range

        payload = {
            "options": {
                "offset": 0,
                "limit": 100
            },
            "fields": [
                "salesWaybillId", "createdAt"
            ],
            "filterBy": [
                {
                    "field": "createdAt",
                    "operator": ">=",
                    "value": start_date + "T00:00:00"
                },
                {
                    "field": "createdAt",
                    "operator": "<=",
                    "value": end_date + "T23:59:59"
                }
            ],
            "orderBy": [
                {
                    "field": "createdAt",
                    # "direction": "ASC"
                    "direction": "DESC"
                }
            ]
        }   
 
        if not self.isValidToken():
            print("Failed to get a valid token")
            return []

        url = self.hostAPI + "/purchases/waybills/list"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == requests.codes.ok:
                result = response.json()
                sales_ids = [item["purchaseWaybillId"] for item in result]
                print(f"Waybill IDs: {sales_ids}")
                return sales_ids
            else:
                print("Error:", response.status_code, response.text)
                return []
        except Exception as e:
            print("Unexpected error:", e)
            return []

    def getpurchaseWaybill(self, purchaseWaybillId: int):
        print(f"-----------------------<< Get Waybill {purchaseWaybillId} >>-----------------------")

        if not self.isValidToken():
            print("Failed to get a valid token")
            return None

        url = f"{self.hostAPI}/purchases/waybills/{purchaseWaybillId}"
        headers = {
            'Authorization': 'Bearer ' + self.credential["token"],
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == requests.codes.ok:
                data = response.json()
                with open(f"purchasewaybill_{purchaseWaybillId}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ Saved to waybill_{purchaseWaybillId}.json")
                return data
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print("Unexpected error:", e)
            return None

if __name__ == '__main__':
    
    saleswaybill = LaudusAPIsales()
    purchasewaybill = LaudusAPIpurchase()
    # if saleswaybill.getToken():
    #     waybill_ids = saleswaybill.getWaybillsList()
    #     for wid in waybill_ids:
    #         saleswaybill.getSalesWaybill(wid)

    # purchasewaybill = LaudusAPIpurchase()
    
    if purchasewaybill.getToken():
        waybill_ids = purchasewaybill.getWaybillsList()
        for wid in waybill_ids:
            purchasewaybill.getpurchaseWaybill(wid)