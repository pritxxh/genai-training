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

