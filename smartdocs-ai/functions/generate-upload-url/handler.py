import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.types import TypeDeserializer

s3 = boto3.client("s3")
dynamodb = boto3.client("dynamodb")
BUCKET_NAME = "smartdocs-ai-347152105990"
TABLE_NAME = "smartdocs-documents"
EXPIRY_SECONDS = 300  # 5 minutes


def lambda_handler(event, context):
    """
    Two actions:
    1. Generate a pre-signed S3 URL for direct browser uploads
    2. Count characters in an existing .txt file in S3
    """
    
    try:
        body = json.loads(event.get("body", "{}"))

        # Read all possible inputs upfront — clean routing below
        filename = body.get("filename")
        content_type = body.get("content_type", "application/octet-stream")
        count_characters = body.get("count_characters")
        count_words = body.get("count_words")
        s3_key = body.get("s3_key")  # caller provides this for character count
        doc_id = body.get("doc_id")
        list_documents = body.get("list_documents")

        
        if list_documents:
            result = dynamodb.scan(TableName=TABLE_NAME,
                                   Limit=10)
            deserializer = TypeDeserializer()
            clean_items = [ {k: deserializer.deserialize(v) for k, v in item.items()} for item in result['Items'] ]
            return response(200, {"documents": clean_items})
        
        
        
        if count_characters or count_words:
            if not s3_key:
                return response(400, {"error": "s3_key is required for counting"})
            if not s3_key.endswith(".txt"):
                return response(400, {"error": "only .txt files are supported"})
            try:
                obj = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                text = obj["Body"].read().decode("utf-8")
                timestamp = datetime.utcnow().strftime("%Y/%m/%d")
                item = dynamodb.put_item(
                TableName = TABLE_NAME,
                Item={
                    "doc_id": {"S": str(uuid.uuid4())},
                    "char_count": {"N": str(len(text))},
                    "word_count": {"N": str(len(text.split()))},
                    "timestamp": {"S": timestamp},
                    "s3_key": {"S": s3_key}
                }
                )
                if count_characters: 
                    return response(200, {"s3_key": s3_key, "character_count": len(text)})
                if count_words:
                    return response(200, {"s3_key": s3_key, "word_count": len(text.split())})
                   
            except s3.exceptions.NoSuchKey:
                return response(404, {"error": "key not found in S3"})
                    
        if doc_id:
            result = dynamodb.get_item(
                TableName=TABLE_NAME,
                Key={"doc_id": {"S": doc_id}}
            )
            if "Item" not in result:
                return response(404, {"error": "document not found"})
            
            deserializer = TypeDeserializer()

            clean_item = {k: deserializer.deserialize(v) for k, v in result['Item'].items()}
            return response(200, clean_item)

        # --- Action: generate a pre-signed upload URL ---
        if not filename:
            return response(400, {"error": "filename is required"})

        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        s3_key = f"documents/{timestamp}/{doc_id}/{filename}"

        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=EXPIRY_SECONDS,
        )

        return response(200, {
            "upload_url": presigned_url,
            "doc_id": doc_id,
            "s3_key": s3_key,
            "expires_in": EXPIRY_SECONDS,
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {"error": "Internal server error"})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=lambda x: int(x) if isinstance(x, Decimal) else str(x))
    }
