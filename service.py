from aiohttp import web, BasicAuth
from jsonschema import validate, ValidationError
import json
import os
import logging

from datetime import datetime

from arcgis import ArcgisToken, FeatureLayer

LONGITUDE_FIELD = "lng"
LATITUDE_FIELD = "lat"
TIMESTAMP_FIELD = "timestamp"
KEY_FIELD = "uniqueid"
FEATURE_LAYER_URL = os.getenv('FEATURE_LAYER_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
TOKEN_REFERER = os.getenv('TOKEN_REFERER')

GIS_USERNAME = os.getenv('GIS_USERNAME')
GIS_PASSWORD = os.getenv('GIS_PASSWORD')

TEST_DUMMY = os.getenv('TEST_DUMMY','test')

def get_services(isTest=False):
    if isTest:
        services = [
            {
                'id': 'test',
                'username': TEST_DUMMY,
                'password': TEST_DUMMY,
                'url': '/test',
                'key': 'uniqueid',
                'feature_layer_id': '-1',
                'isTest': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'timestamp': {'type': 'string'},
                        'uniqueid': {'type': 'string'},
                        'lng': {'type': 'number'},
                        'lat': {'type': 'number'}
                    },
                    'required': ['timestamp', 'uniqueid', 'lng', 'lat']
                }
            }
        ]
    else:
        services = [
            {
                'id': 'uniqueid-location-updater',
                'username': os.getenv('AUTH_BASIC_USER'),
                'password': os.getenv('AUTH_BASIC_PASSWORD'),
                'topic': 'siis-mobi1',
                'url': '/api/v1/location',
                'key': 'uniqueid',
                'feature_layer': 'uniqueid-location',
                'feature_layer_id': '0',
                'isTest': False,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'timestamp': {'type': 'string'},
                        'uniqueid': {'type': 'string'},
                        'lng': {'type': 'number'},
                        'lat': {'type': 'number'}
                    },
                    'required': ['timestamp', 'uniqueid', 'lng', 'lat']
                }
            }
        ]
    return services

def handler_closure(service):
    username = service['username']
    password = service['password']
    schema = service['schema']
    feature_layer = service['feature_layer']
    feature_layer_id = service['feature_layer_id']
    isTest = service['isTest']

    async def handler(request):
        time_start = datetime.now()
        auth_str = request.headers.get('AUTHORIZATION')
        if auth_str is None:
            raise web.HTTPForbidden()
        auth = BasicAuth.decode(auth_str)

        if auth.login != username or auth.password != password:
            raise web.HTTPForbidden(headers={'Content-Type': 'json'}, text='{"status":"failed","code":1,"msg":"Forbidden"}')

        invalid_request = web.HTTPBadRequest(headers={'Content-Type': 'json'}, text='{"status":"failed","code":1,"msg":"Invalid data"}')
        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            logging.error("JSON Decode error: %s", e)
            return invalid_request

        if 'data' not in data:
            logging.error("No data found")
            return invalid_request

        features = []
        for row in data['data']:
            try:
                validate(row, schema)
                row['vendor'] = service['id']
                logging.info(json.dumps(row).encode('utf-8'))
                try:
                    row[TIMESTAMP_FIELD] = int(row[TIMESTAMP_FIELD])
                except ValueError:
                    dt = datetime.strptime(row[TIMESTAMP_FIELD], "%Y-%m-%d %H:%M:%S")
                    epoch = datetime.utcfromtimestamp(0)
                    row[TIMESTAMP_FIELD] = int((dt-epoch).total_seconds() * 1000.0)

                feature = {"geometry": {"x": row[LONGITUDE_FIELD],
                                        "y": row[LATITUDE_FIELD]}}
                feature["attributes"] = row
                features.append(feature)
                # p.produce(topic, json.dumps(row).encode('utf-8'), row[service['key']])
            except ValidationError as e:
                logging.error("Invalid data: %s", e.message)
                return invalid_request
        # p.flush()
        if(len(features) > 0):
            upsert_arcgis(feature_layer, feature_layer_id, features, isTest)

        return web.json_response({"status": "success", "code": 0})
    return handler

def upsert_arcgis(feature_layer, feature_layer_id, features, isTest=False):
    result = {
        'updateResults': [{ 'success': True }],
        'addResults': [{ 'success': True }],
    }
    upsert_start = datetime.now()
    if isTest is False:
        token = ArcgisToken(GIS_USERNAME, GIS_PASSWORD, TOKEN_URL, TOKEN_REFERER)
        layer = FeatureLayer(FEATURE_LAYER_URL + feature_layer + '/FeatureServer/' + feature_layer_id, token)
        result = layer.upsert(features, KEY_FIELD, TIMESTAMP_FIELD).json()
    
    upsert_end = datetime.now()
    upsert_delta = upsert_end - upsert_start
    updates = sum(1 for x in result['updateResults'] if 'success' in x and x['success'])
    adds = sum(1 for x in result['addResults'] if 'success' in x and x['success'])
    logging.info("Adds: %d, updates: %d, %d ms", adds, updates, int(upsert_delta.total_seconds() * 1000))
    return True

async def hello(request):
    return web.json_response({"success":True,"data":"Index","message":"This service is running properly","code":200})

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

    app = web.Application()
    app.router.add_get('/', hello)
    services = get_services()
    for service in services:
        app.router.add_post(service['url'], handler_closure(service))

    web.run_app(app)
