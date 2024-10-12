import os

class Config:
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
    APP_ID = os.getenv("APP_ID", "")
    APP_SECRET = os.getenv("APP_SECRET", "")
    FULLY_QUALIFIED_NAMESPACE = os.getenv("FULLY_QUALIFIED_NAMESPACE", "")
    SERVICE_BUS_TOPIC_NAME = os.getenv("SERVICE_BUS_TOPIC_NAME", "")
