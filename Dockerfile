FROM python:3.7

RUN pip install aiohttp jsonschema coverage requests responses

EXPOSE 8080

COPY . .

CMD ["python", "service.py"]
