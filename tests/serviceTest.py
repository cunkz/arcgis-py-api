from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

import service as serviceLibrary
# import responses

# from arcgis import ArcgisToken, FeatureLayer

import logging
import os

TEST_BASIC_DEFAULT=os.getenv('TEST_BASIC_DEFAULT', 'dGVzdDp0ZXN0')
TEST_BASIC_DUMMY=os.getenv('TEST_BASIC_DUMMY', 'QTpC')

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)
logging.info(TEST_BASIC_DEFAULT)
logging.info(TEST_BASIC_DUMMY)

class serviceTest(AioHTTPTestCase):

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """
        async def hello(request):
            return web.Response(text='Hello, world')

        app = web.Application()
        app.router.add_get('/', hello)

        services = serviceLibrary.get_services(isTest=True)
        for service in services:
            app.router.add_post(service['url'], serviceLibrary.handler_closure(service))
        
        return app

    # the unittest_run_loop decorator can be used in tandem with
    # the AioHTTPTestCase to simplify running
    # tests that are asynchronous
    async def test_example(self):
        resp = await self.client.request("GET", "/")
        assert resp.status == 200
        text = await resp.text()
        assert "Hello, world" in text

    async def test_success(self):
        resp = await self.client.request("POST", "/test", data='{"data":[{"timestamp":1695039838000,"uniqueid":"A","lng":1.11,"lat":1.11}]}'
, headers={'AUTHORIZATION':'Basic '+ TEST_BASIC_DEFAULT})
        assert resp.status == 200
    
    async def test_error_invalid_data(self):
        resp = await self.client.request("POST", "/test", data='{"data":"B"}', headers={'AUTHORIZATION':'Basic '+ TEST_BASIC_DEFAULT})
        assert resp.status == 400

    async def test_error_not_found_data(self):
        resp = await self.client.request("POST", "/test", data='{"A":"B"}', headers={'AUTHORIZATION':'Basic '+ TEST_BASIC_DEFAULT})
        assert resp.status == 400

    async def test_error_decode_payload(self):
        resp = await self.client.request("POST", "/test", data={"A":"B"}, headers={'AUTHORIZATION':'Basic '+ TEST_BASIC_DEFAULT})
        assert resp.status == 400

    async def test_error_invalid_auth(self):
        resp = await self.client.request("POST", "/test", data={"A":"B"}, headers={'AUTHORIZATION':'Basic '+ TEST_BASIC_DUMMY})
        assert resp.status == 403

    async def test_error_not_found_auth(self):
        resp = await self.client.request("POST", "/test", data={"A":"B"})
        assert resp.status == 403

