# Arcgis Python API Example

Example of API for Arcgis via Python

## Usage

To use this example, you can follow the steps below :

1. Make sure you already install python3.7 or higher
2. Install requirement library : `pip install aiohttp jsonschema coverage requests responses`
3. Create .env file based on .env.example
4. Run example : `python service.py`
5. Run this curl from your command line or other app 
(this curl use env `AUTH_BASIC_USER=test` and `AUTH_BASIC_PASSWORD=test`):
```
curl --location 'http://localhost:8080/api/v1/location' \
--header 'Content-Type: application/json' \
--header 'Authorization: Basic dXNlcjpwYXNzd29yZA==' \
--data '{
    "data": [
        {
            "timestamp": "2023-09-18 12:23:58",
            "uniqueid": "AAA",
            "lng": 1.11,
            "lat": 1.11
        }
    ]
}'
```


Enjoy
