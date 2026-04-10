import json
# import boto3
from datetime import datetime
from decimal import Decimal
#from boto3.dynamodb.types import TypeDeserializer

# s3 = boto3.client("s3")
# dynamodb = boto3.client("dynamodb")

BUCKET_NAME = "smartdocs-ai-347152105990"
TABLE_NAME = "smartdocs-documents"

def validate(body, action, user_id=None):
    """
    Do you think i care about the comments ?
    """
    errors = []
    
    # if not user_id:
    #     errors.append("User not authenticated")

    if not body:
        return ["Request body missing"]

    if not action:
        return ["Action is required"]

    # Action Validation
    if action == "count":
        s3_key = body.get("s3_key")

        if not s3_key:
            errors.append("s3_key is required for count")

        elif not s3_key.endswith(".txt"):
            errors.append("s3_key must end with .txt")

    elif action == "upload":
        if not body.get("filename"):
            errors.append("filename is required for upload")

        if not body.get("content_type"):
            errors.append("content_type is required for upload")

    elif action == "get":
        if not body.get("doc_id"):
            errors.append("doc_id is required for get")

    elif action == "list":
        pass  # no validation needed

    else:
        errors.append("unknown action")

    return errors
    