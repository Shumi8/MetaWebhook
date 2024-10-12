import logging
import hashlib
import hmac
import json
import azure.functions as func
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.identity import DefaultAzureCredential
from config import Config
from azure.storage.blob import BlobServiceClient
import time
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

VERIFY_TOKEN = ""
ACCESS_TOKEN = Config.ACCESS_TOKEN
APP_ID = Config.APP_ID
APP_SECRET = Config.APP_SECRET
FULLY_QUALIFIED_NAMESPACE = Config.FULLY_QUALIFIED_NAMESPACE
SERVICE_BUS_TOPIC_NAME = Config.SERVICE_BUS_TOPIC_NAME
BLOB_STORAGE_CONNECTION_STRING = Config.BLOB_STORAGE_CONNECTION_STRING
BLOB_CONTAINER_NAME = Config.BLOB_CONTAINER_NAME

@app.function_name(name="webhook")
@app.route(route="webhook")
def webhook(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Webhook triggered.')

    # Step 1: Verify webhook subscription
    hub_mode = req.params.get('hub.mode')
    hub_challenge = req.params.get('hub.challenge')
    hub_verify_token = req.params.get('hub.verify_token')

    if hub_mode == "subscribe" and hub_challenge:
        logging.info('Verification request received.')
        if hub_verify_token == VERIFY_TOKEN:
            logging.info('Verification token matched. Returning challenge.')
            return func.HttpResponse(hub_challenge, status_code=200)
        else:
            logging.warning('Verification token mismatch.')
            return func.HttpResponse("Verification token mismatch", status_code=403)

    # Step 2: Handle event notifications (POST request)
    try:
        req_body = req.get_json()
        logging.info('Request body parsed successfully.')
    except ValueError as e:
        logging.error(f'Failed to parse request body: {e}')
        return func.HttpResponse("Invalid JSON", status_code=400)

    # Step 3: Validate the signature
    x_hub_signature = req.headers.get('X-Hub-Signature-256')
    if not x_hub_signature:
        logging.warning('Missing X-Hub-Signature-256 header.')
        return func.HttpResponse("Missing signature", status_code=400)

    payload = req.get_body()
    hash_object = hmac.new(APP_SECRET.encode('utf-8'), msg=payload, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    logging.info(f'Expected Signature: {expected_signature}')

    if not hmac.compare_digest(expected_signature, x_hub_signature):
        logging.warning('Invalid signature. Request not authenticated.')
        return func.HttpResponse("Invalid signature", status_code=403)

    logging.info(f"Signature validated. Processing event: {json.dumps(req_body)}")

    # Log the entire req_body (contains all fields) before uploading
    full_payload = json.dumps(req_body, indent=4)  # This is the full payload
    logging.info(f"Full JSON payload to be written to Blob Storage: {full_payload}")

    try:
        # Initialize the Blob Service Client using the connection string
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)
        
        # Get a reference to the container
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        
        # Unique blob name using timestamp
        blob_name = f"full_webhook_payload_{int(time.time())}.json"
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the entire request body to the blob
        blob_client.upload_blob(full_payload, overwrite=True)
        logging.info(f'Successfully uploaded full webhook payload to blob: {blob_name}')

    except Exception as e:
        logging.error(f'Error uploading to Azure Blob Storage: {e}')
        return func.HttpResponse("Failed to upload full webhook payload to blob storage", status_code=500)

    # Step 4: Extract all IDs from the webhook payload
    ids = []
    try:
        for entry in req_body.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'some_field':
                    id_value = change.get('value', {}).get('id')
                    if id_value:
                        ids.append(id_value)
        logging.info(f'Extracted ids: {ids}')
    except Exception as e:
        logging.error(f'Error while extracting ids: {e}')
        return func.HttpResponse("Error processing IDs", status_code=500)

    # Initialize ServiceBusClient
    try:
        credential = DefaultAzureCredential()
        servicebus_client = ServiceBusClient(fully_qualified_namespace=FULLY_QUALIFIED_NAMESPACE, credential=credential)
    except Exception as e:
        logging.error(f'Failed to initialize Service Bus Client: {e}')
        return func.HttpResponse("Failed to initialize Service Bus Client", status_code=500)

    # Step 5: Fetch details for each id and send to Service Bus
    try:
        with servicebus_client:
            sender = servicebus_client.get_topic_sender(topic_name=SERVICE_BUS_TOPIC_NAME)
            with sender:
                for id_value in ids:
                    try:
                        logging.info(f'Fetching details for id: {id_value}')
                        
                        # Fetch the data using an API
                        url = f'https://api.example.com/v1/{id_value}/'
                        params = {
                            'access_token': ACCESS_TOKEN
                        }
                        
                        response = requests.get(url, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            logging.info(f"Data fetched for id {id_value}: {json.dumps(data, indent=4)}")
                            
                            # Send data to Service Bus
                            message = ServiceBusMessage(json.dumps(data))
                            sender.send_messages(message)
                            
                            logging.info(f'Details fetched for id {id_value} and sent to Service Bus.')
                        else:
                            logging.error(f"Failed to fetch data for id {id_value}, status code: {response.status_code}")
                            return func.HttpResponse(f"Error fetching data for id {id_value}", status_code=500)
                    except Exception as e:
                        logging.error(f'Error fetching details or sending to Service Bus for id {id_value}: {e}')
                        return func.HttpResponse(f"Error processing id {id_value}", status_code=500)
    except Exception as e:
        logging.error(f'Error with Service Bus: {e}')
        return func.HttpResponse("Error with Service Bus", status_code=500)

    logging.info('Event processing completed successfully.')
    return func.HttpResponse("Event received", status_code=200)
