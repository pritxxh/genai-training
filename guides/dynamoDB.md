# DynamoDB Guide

Concepts covered here are ones that've been properly understood and challenged.

---

## What is DynamoDB?

DynamoDB is AWS's fully managed NoSQL database. No servers, no schema migrations, scales automatically. You define a table and start reading/writing.

```
SQL:      table → rows    → columns  (fixed schema, every row looks the same)
DynamoDB: table → items   → attributes (flexible schema, each item can differ)
```

---

## Core Concepts

### Table
Where your data lives. Like a collection in MongoDB, or a table in SQL — but schema-less. You only define the key structure upfront, everything else is free-form.

### Item
A single record inside a table. Like a row in SQL, but each item can have completely different attributes. No two items need to look the same.

### Partition Key
The unique identifier for every item. DynamoDB uses this to decide where to physically store the data on its servers. Every item must have one, and it must be unique across the table.

Good analogy: a barcode on a product. Every product has its own barcode — no two are the same. You scan it and get all the info attached to that product.

Bad choice: timestamp — two users can upload at the same millisecond, causing a collision.
Good choice: `doc_id = str(uuid.uuid4())` — UUID is mathematically guaranteed to be unique every time.

### Sort Key (optional)
A second key that works alongside the partition key. Lets you store multiple related items under the same partition — useful when you want grouping.

Example: `user_id` as partition key + `doc_id` as sort key means one user can own many documents:

```
user_id (partition key)  |  doc_id (sort key)  |  word_count
user-A                   |  abc-123            |  9
user-A                   |  def-456            |  42
user-B                   |  xyz-789            |  15
```

Think of it like a school: each class (I, II, XII) is a partition, and each student inside is identified by their sort key. Students across classes can share names or attributes — but their combination of class + student ID is always unique.

### Attributes
Everything else on an item beyond the keys. Word count, character count, filename, timestamp — all attributes. No fixed schema, add whatever you need per item.

---

## Mental Model: Flat vs Grouped

Flat table (partition key only) — what we're building:
```
doc_id (PK)    |  s3_key              |  word_count  |  uploaded_at
abc-123-uuid   |  documents/.../f1   |  9           |  2026-04-07
def-456-uuid   |  documents/.../f2   |  42          |  2026-04-07
```

Grouped table (partition key + sort key) — useful when users own documents:
```
user_id (PK)   |  doc_id (SK)   |  word_count
user-A         |  abc-123       |  9
user-A         |  def-456       |  42
```

---

## CLI — Creating & Using a Table

```bash
# Create a new table
# --attribute-definitions: declare key attributes and their types (S=String, N=Number, B=Binary)
# --key-schema: assign roles to keys (HASH = partition key, RANGE = sort key)
# --billing-mode PAY_PER_REQUEST: pay only per read/write, no pre-provisioned capacity (ideal for dev/low traffic)
aws dynamodb create-table \
  --table-name smartdocs-documents \
  --attribute-definitions AttributeName=doc_id,AttributeType=S \
  --key-schema AttributeName=doc_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Check table status (CREATING → ACTIVE after a few seconds)
aws dynamodb describe-table \
  --table-name smartdocs-documents \
  --region us-east-1

# Scan — reads EVERY item in the table, no filter
# Fine for dev/small tables, expensive at scale (reads all data regardless)
# Use query instead when you know the partition key
aws dynamodb scan \
  --table-name smartdocs-documents \
  --region us-east-1

# Grant Lambda permission to read/write DynamoDB
# Must be a separate IAM statement from S3 — each service needs its own resource ARN
aws iam put-role-policy \
  --role-name smartdocs-lambda-role \
  --policy-name smartdocs-lambda-policy \
  --policy-document file://smartdocs-ai/infra/lambda-role-policy.json
```

---

## boto3 — Writing Items from Lambda

DynamoDB requires every attribute value to declare its type explicitly using a type descriptor:

```python
dynamodb = boto3.client("dynamodb")

dynamodb.put_item(
    TableName="smartdocs-documents",
    Item={
        "doc_id":     {"S": str(uuid.uuid4())},   # S = String
        "word_count": {"N": str(len(text.split()))}, # N = Number (must be passed as string)
        "char_count": {"N": str(len(text))},
        "s3_key":     {"S": s3_key},
        "timestamp":  {"S": datetime.utcnow().strftime("%Y/%m/%d")}
    }
)
```

Key rules:
- `"S"` for strings, `"N"` for numbers, `"B"` for binary
- Numbers must be passed as strings in boto3 — `{"N": "42"}` not `{"N": 42}`
- `put_item` is an upsert — if an item with the same `doc_id` exists, it gets overwritten

---

## boto3 — Reading a Single Item (get_item)

`get_item` fetches exactly one item by its partition key. No table scan, no cost per extra item — it goes directly to the record.

```python
result = dynamodb.get_item(
    TableName=TABLE_NAME,
    Key={"doc_id": {"S": doc_id}}  # must match the partition key type (S = String)
)
```

The response always comes back — even if the item doesn't exist. The difference is whether `"Item"` is in the result:

```python
if "Item" not in result:
    return response(404, {"error": "document not found"})

return response(200, result["Item"])
```

Key rules:
- `get_item` never throws for a missing item — always check for `"Item"` in the result
- `Key` must use the same type descriptor format as `put_item` — `{"S": ...}`, `{"N": ...}` etc.
- The returned item still has type descriptors attached: `{"word_count": {"N": "24"}}` not `{"word_count": 24}`
- To return clean JSON to a client, you'd need to strip the type wrappers (a pattern called deserialising)

### scan vs get_item — when to use which

```
get_item  → you know the exact doc_id → fast, cheap, direct lookup
scan      → you want all items, no filter → reads everything, expensive at scale
query     → you know the partition key and want to filter by sort key → efficient grouping
```

For a single document lookup, always prefer `get_item` over `scan`.

---

## Deserialising DynamoDB Responses

`TypeDeserializer` strips DynamoDB's type wrappers from a response, turning `{"N": "24"}` into a Python value. But it converts numbers into `Decimal` objects, not plain `int` or `float` — and `json.dumps` can't serialize `Decimal` by default.

### Pattern: deserialise + return clean JSON

```python
from boto3.dynamodb.types import TypeDeserializer
from decimal import Decimal

# In the get_item block:
deserializer = TypeDeserializer()
clean_item = {k: deserializer.deserialize(v) for k, v in result['Item'].items()}
return response(200, clean_item)
```

### Fix: handle Decimal in json.dumps

Add a `default` handler to `json.dumps` in your `response()` helper:

```python
def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=lambda x: int(x) if isinstance(x, Decimal) else str(x))
    }
```

`default` is called by `json.dumps` whenever it hits a type it can't serialize. The lambda says: if it's a `Decimal`, convert to `int` (or `float` if it has decimals). Otherwise convert to string.

### Why this happens

DynamoDB stores numbers as strings internally (e.g. `"24"` not `24`). `TypeDeserializer` converts them to `Decimal` for precision safety. For a simple API response, converting to `int`/`float` is fine.

Raw DynamoDB response:
```json
{"word_count": {"N": "24"}, "s3_key": {"S": "documents/test.txt"}}
```

After `TypeDeserializer` + Decimal fix:
```json
{"word_count": 24, "s3_key": "documents/test.txt"}
```

---

## boto3 — Listing All Items (scan)

`scan` reads every item in the table. Use it when you don't know the partition key and need all records. Always set a `Limit` to avoid reading the entire table in one shot.

```python
result = dynamodb.scan(
    TableName=TABLE_NAME,
    Limit=10  # must be int, not string
)
```

The response uses `"Items"` (plural), unlike `get_item` which uses `"Item"` (singular). Deserialise the list with a list comprehension:

```python
deserializer = TypeDeserializer()
clean_items = [
    {k: deserializer.deserialize(v) for k, v in item.items()}
    for item in result['Items']
]
return response(200, {"documents": clean_items})
```

Key things to know:
- `Limit` caps how many items are *evaluated*, not necessarily returned — DynamoDB may return fewer if items are filtered
- Items without a field (e.g. older items missing `char_count`) are returned as-is — DynamoDB is schema-less, no nulls injected
- If the table has more items than `Limit`, the response includes a `LastEvaluatedKey` — use it as `ExclusiveStartKey` in the next call to paginate

### IAM — don't forget Scan permission

`dynamodb:Scan` is a separate permission from `dynamodb:GetItem`. If you add a new DynamoDB operation, always check the role policy:

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:GetItem",
    "dynamodb:Scan"
  ],
  "Resource": "arn:aws:dynamodb:us-east-1:347152105990:table/smartdocs-documents"
}
```

Rule of thumb: every new boto3 DynamoDB method needs its own IAM action. AWS denies by default.
