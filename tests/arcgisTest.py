import responses
import unittest

from arcgis import ArcgisToken, FeatureLayer

import logging
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

class arcgisTest(unittest.TestCase):

    @responses.activate
    def test_arcgis_refresh(self):
        responses.add(responses.POST, 'https://google.com/login', json={'token': 'A', 'expires': 1697052852647, 'ssl': True}, status=200)
        responses.add(responses.GET, 'https://google.com/featureLayer/query', json={'objectIdFieldName': 'objectid', 'globalIdFieldName': '', 'geometryType': 'esriGeometryPoint', 'spatialReference': {'wkid': 4326, 'latestWkid': 4326}, 'fields': [{'name': 'objectid', 'alias': 'OBJECTID', 'type': 'esriFieldTypeOID'}, {'name': 'uniqueid', 'alias': 'uniqueid', 'type': 'esriFieldTypeString', 'length': 20}], 'features': [{'attributes': {'objectid': 12815, 'uniqueid': 'A'}, 'geometry': {'x': 1.1100000000000136, 'y': 1.1100000000000136}}]}, status=200)
        responses.add(responses.POST, 'https://google.com/featureLayer/applyEdits', json={'addResults': [], 'updateResults': [{'objectId': 12815, 'success': True}], 'deleteResults': []}, status=200)
        
        token = ArcgisToken("A","B","https://google.com/login","google.com")
        logging.info(str(token))
        layer = FeatureLayer("https://google.com/featureLayer", token)

        features = [{'geometry': {'x': 1.11, 'y': 1.11}, 'attributes': {'timestamp': 1695039838000, 'uniqueid': 'A','lng': 1.11, 'lat': 1.11}}]
        layer.upsert(features, 'uniqueid', 'dt').json()

if __name__ == '__main__':
    unittest.main()