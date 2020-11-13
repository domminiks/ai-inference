file_schema = {
    "title": "JSON Schema for model description",
    "type": "object",
    "properties": {
        "model": {
            "type": "object",
            "description": "Model details",
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
                "backend": {
                    "description": "The backend of the model",
                    "type": "object",
                    "properties": {
                        "type": {
                            "description": "The backend of the model",
                            "type": "string",
                            "enum": ["tensorflow", "spark", "sklearn", "pytorch", "onnx"]
                        },
                        "parameters": {}
                    },
                    "if": {
                        "properties": {"type": {"const": "tensorflow"}}
                    },
                    "then": {
                        "properties": {
                            "parameters": {
                                "description": "Details of the input data for the model",
                                "type": "object",
                                "properties": {
                                    "input": {
                                        "description": "Details of the input data for the model",
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "description": "The type of the input",
                                                "type": "string",
                                                "enum": ["image", "number", "text"]
                                            },
                                            "labels": {
                                                "description": "The name of the input tensors",
                                                "type": "array",
                                                "items": {
                                                    "type": "string",
                                                    "minLength": 1
                                                },
                                                "minItems": 1
                                            },
                                        },
                                        "required": ["type", "labels"],
                                        "additionalProperties": False,
                                    },
                                    "output": {
                                        "description": "The name of the output tensors",
                                        "type": "object",
                                        "properties": {
                                            "labels": {
                                                "description": "The name of the output tensors",
                                                "type": "array",
                                                "items": {
                                                    "type": "string",
                                                    "minLength": 1
                                                },
                                                "minItems": 1
                                            },
                                        },
                                        "required": ["labels"],
                                        "additionalProperties": False,
                                    },
                                },
                                "required": ["input", "output"],
                                "additionalProperties": False,
                            }
                        }
                    },
                    "else": {
                        "properties": {
                            "parameters": {
                                "description": "Details of the input data for the model",
                                "type": "object",
                                "properties": {
                                    "input": {
                                        "description": "Details of the input data for the model",
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "description": "The type of the input",
                                                "type": "string",
                                                "enum": ["image", "number", "text"]
                                            },
                                            "dtype": {
                                                "description": "The data type of the input",
                                                "type": "string"
                                            },
                                            "shape": {
                                                "description": "The size of the input",
                                                "type": "array",
                                                "items": {
                                                    "type": "integer"
                                                },
                                                "minItems": 2
                                            },
                                        },
                                        "required": ["type", "dtype", "shape"],
                                        "additionalProperties": False,
                                    },
                                    "output": {
                                        "description": "Details of the output data for the model",
                                        "type": "object",
                                        "properties": {
                                            "shape": {
                                                "description": "The shape of the output",
                                                "type": "array",
                                                "items": {
                                                    "type": "integer"
                                                },
                                                "minItems": 2
                                            },
                                        },
                                        "required": ["shape"],
                                        "additionalProperties": False,
                                    },
                                },
                                "required": ["input", "output"],
                                "additionalProperties": False,
                            }
                        }
                    },
                    "required": ["type", "parameters"],
                    "additionalProperties": False,
                },
                "script": {
                    "description": "Details of the formatting script",
                    "type": "object",
                    "properties": {
                        "folder": {
                            "description": "The folder containing the formatting script",
                            "type": "string",
                            "minLength": 1
                        },
                    },
                    "required": ["folder"],
                    "additionalProperties": False,
                },
            },
            "required": ["name", "version", "backend", "script"],
            "additionalProperties": False,
        },
    },
    "required": ["model"],
    "additionalProperties": False,
}
