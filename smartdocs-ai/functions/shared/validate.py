def validate(body, action):
    """
    Validates request body for a given action.
    Returns a list of all errors found — empty list means valid.

    Actions: "count", "upload", "get", "list"
    """
    errors = []

    if not body:
        return ["Request body is missing"]

    if not action:
        return ["Action is required"]

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
        pass  # no fields required

    else:
        errors.append(f"unknown action: {action}")

    return errors
