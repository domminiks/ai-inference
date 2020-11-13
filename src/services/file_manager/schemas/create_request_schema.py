create_request_schema = {
    "title": "JSON Schema for models request",
    "type": "object",
    "properties": {
        "name": {
            "description": "The name of the model",
            "type": "string",
            "minLength": 1,
        },
        "version": {
            "description": "The version of the model",
            "type": "integer",
            "minimum": 1
        },
        "id": {
            "description": "The ID of the Google Drive file",
            "type": "string",
            "minLength": 1
        },
        "async_request": {
            "description": "If the request should be asynchrony (true) or synchrony (false)",
            "type": "boolean",
        }
    },
    "required": ["name", "version", "id"],
    "additionalProperties": False
}
