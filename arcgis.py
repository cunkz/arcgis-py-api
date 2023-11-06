import json
import requests
import time
import os

time.sleep(5)

DEFAULT_TOKEN_URL = os.getenv('TOKEN_URL')
DEFAULT_REFERER = os.getenv('TOKEN_REFERER')

class ArcgisToken:
    def __current_milli_time(self):
        return int(round(time.time() * 1000))

    def __init__(self, username, password, token_url=DEFAULT_TOKEN_URL, referer=DEFAULT_REFERER,
                 expiration=1000):
        self.username = username
        self.password = password
        self.referer = referer
        self.token_url = token_url
        self.expiration = expiration
        self.refresh()

    def refresh(self):
        token_req_data = {
            "f": "json",
            "username": self.username,
            "password": self.password,
            "referer": self.referer,
            "expiration": self.expiration,
        }
        token_req = requests.post(self.token_url, data=token_req_data)
        token_resp = token_req.json()
        self.token = token_resp['token']
        self.expiry = token_resp['expires']

    def get_token(self):
        if self.__current_milli_time() > self.expiry:
            self.refresh()
        return self.token

    # def get_expiry(self):
    #     return self.expiry

class FeatureLayer:
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def query(self, where="1=1", out_fields="*", return_geometry="true"):
        params = {
            "f": "json",
            "token": self.token.get_token(),
            "outFields": out_fields,
            "where": where,
            "returnGeometry": return_geometry
        }
        query = requests.get(self.url + "/query", params=params)
        return query.json()

    # def add(self, features):
    #     data = {
    #         'f': 'json',
    #         'token': self.token.get_token(),
    #         'features': json.dumps(features),
    #         'rollbackOnFailure': 'false'
    #     }

    #     return requests.post(self.url + "/addFeatures", data=data)

    # def delete(self, where):
    #     data = {
    #         'f': 'json',
    #         'token': self.token.get_token(),
    #         'where': where
    #     }

    #     return requests.post(self.url + "/deleteFeatures", data=data)

    def upsert(self, features, key_column, order_column=None):
        # Compact features given key and time column
        if order_column:
            bk = {}
            for feat in features:
                key = feat['attributes'][key_column]
                if key not in bk or feat['attributes'][order_column] > bk[key]['last']:
                    bk[key] = { 'last': feat['attributes'][order_column], 'feature': feat }
            features = [ val['feature'] for key, val in bk.items()]

        # Create mapping between objectid and feature key
        in_clause = ",".join(["'%s'" % x["attributes"][key_column] for x in features])
        feat_result = self.query(where="%s in (%s)" % (key_column, in_clause), out_fields="objectid,"+key_column)
        objectid_map = dict([(x["attributes"][key_column], x["attributes"]["objectid"])
                             for x in feat_result["features"]])

        # Simultaneously update and add data
        adds = []
        updates = []
        for feat in features:
            if feat["attributes"][key_column] in objectid_map:
                feat["attributes"]["objectid"] = objectid_map[feat["attributes"][key_column]]
                updates.append(feat)
            else:
                adds.append(feat)
        data = {"f": "json", "token": self.token.get_token(), "adds": json.dumps(adds), "updates": json.dumps(updates)}
        return requests.post(self.url + "/applyEdits", data=data)
