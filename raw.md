Step 2 — write four separate handle_* functions directly in handler.py.

Each function takes only what it needs and returns a plain dict (no response() wrapping — that's the handler's job).

Hints per function:

handle_upload(body)

needs filename and content_type from body
generates a doc_id (uuid), a timestamp, builds an s3_key
calls s3.generate_presigned_url()
returns dict with upload_url, doc_id, s3_key, expires_in
handle_count(body)

needs s3_key from body
fetches file from S3, decodes text
calculates word_count and char_count
writes to DynamoDB with a new doc_id
returns dict with s3_key, word_count, char_count
handle_get(body)

needs doc_id from body
calls dynamodb.get_item()
deserialises with TypeDeserializer
returns the clean item dict, or raises/returns error if not found
handle_list()

no parameters needed
calls dynamodb.scan() with Limit=10
deserialises each item
returns {"documents": [...]}
Write all four functions. Keep them focused — no routing logic, no response() calls, just the action logic. Show me when done.