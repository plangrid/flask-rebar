# cURL and example.py

Here's a snippet of playing with the application inside [examples/todo.py](examples/todo.py).

Swagger for free!
```
$ curl -XGET http://127.0.0.1:5000/swagger
{
  "consumes": [
    "application/json"
  ],
  "definitions": {
    "CreateTodoSchema": {
      "additionalProperties": false,
      "properties": {
        "complete": {
          "type": "boolean"
        },
        "description": {
          "type": "string"
        }
      },
      "required": [
        "description",
        "complete"
      ],
      "title": "CreateTodoSchema",
      "type": "object"
    },
    "Error": {
      "properties": {
        "code": {
          "type": "string"
        },
        "details": {
          "type": "object"
        },
        "errors": {
          "type": "object"
        },
        "message": {
          "type": "string"
        }
      },
      "required": [
        "message"
      ],
      "title": "Error",
      "type": "object"
    },
    "ListOfTodoSchema": {
      "properties": {
        "data": {
          "items": {
            "$ref": "#/definitions/TodoSchema"
          },
          "type": "array"
        }
      },
      "title": "ListOfTodoSchema",
      "type": "object"
    },
    "TodoSchema": {
      "properties": {
        "complete": {
          "type": "boolean"
        },
        "description": {
          "type": "string"
        },
        "id": {
          "type": "integer"
        }
      },
      "required": [
        "description",
        "id",
        "complete"
      ],
      "title": "TodoSchema",
      "type": "object"
    },
    "UpdateTodoSchema": {
      "additionalProperties": false,
      "properties": {
        "complete": {
          "type": "boolean"
        },
        "description": {
          "type": "string"
        }
      },
      "title": "UpdateTodoSchema",
      "type": "object"
    }
  },
  "host": "127.0.0.1:5000",
  "info": {
    "description": "",
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {
    "/todos": {
      "get": {
        "operationId": "get_todos",
        "parameters": [
          {
            "in": "query",
            "name": "complete",
            "required": false,
            "type": "boolean"
          }
        ],
        "responses": {
          "200": {
            "description": "ListOfTodoSchema",
            "schema": {
              "$ref": "#/definitions/ListOfTodoSchema"
            }
          },
          "default": {
            "description": "Error",
            "schema": {
              "$ref": "#/definitions/Error"
            }
          }
        }
      },
      "post": {
        "operationId": "create_todo",
        "parameters": [
          {
            "in": "body",
            "name": "CreateTodoSchema",
            "required": true,
            "schema": {
              "$ref": "#/definitions/CreateTodoSchema"
            }
          }
        ],
        "responses": {
          "201": {
            "description": "TodoSchema",
            "schema": {
              "$ref": "#/definitions/TodoSchema"
            }
          },
          "default": {
            "description": "Error",
            "schema": {
              "$ref": "#/definitions/Error"
            }
          }
        }
      }
    },
    "/todos/{todo_id}": {
      "parameters": [
        {
          "in": "path",
          "name": "todo_id",
          "required": true,
          "type": "integer"
        }
      ],
      "patch": {
        "operationId": "update_todo",
        "parameters": [
          {
            "in": "body",
            "name": "UpdateTodoSchema",
            "required": true,
            "schema": {
              "$ref": "#/definitions/UpdateTodoSchema"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "TodoSchema",
            "schema": {
              "$ref": "#/definitions/TodoSchema"
            }
          },
          "default": {
            "description": "Error",
            "schema": {
              "$ref": "#/definitions/Error"
            }
          }
        }
      }
    }
  },
  "produces": [
    "application/vnd.plangrid+json"
  ],
  "schemes": [
    "http"
  ],
  "security": [
    {
      "sharedSecret": []
    }
  ],
  "securityDefinitions": {
    "sharedSecret": {
      "in": "header",
      "name": "X-PG-Auth",
      "type": "apiKey"
    }
  },
  "swagger": "2.0"
}
```

Authentication!
```
$ curl -XGET http://127.0.0.1:5000/todos
{
  "message": "No auth token provided."
}

$ curl -XGET http://127.0.0.1:5000/todos -H "X-PG-Auth: my-api-key"
{
  "data": []
}
```

Validation!
```
$ curl -XPATCH http://127.0.0.1:5000/todos/1 -H "X-PG-Auth: my-api-key" -H "Content-Type: application/json" -d '{"complete": "wrong type, for demonstration of validation"}'
{
  "errors": {
    "complete": "Not a valid boolean."
  },
  "message": "JSON body parameters are invalid."
}
```

CRUD!
```
$ curl -XPOST http://127.0.0.1:5000/todos -H "X-PG-Auth: my-api-key" -H "Content-Type: application/json" -d '{"complete": false, "description": "Find product market fit"}'
{
  "complete": false,
  "description": "Find product market fit",
  "id": 1
}

$ curl -XPATCH http://127.0.0.1:5000/todos/1 -H "X-PG-Auth: my-api-key" -H "Content-Type: application/json" -d '{"complete": true}'
{
  "complete": true,
  "description": "Find product market fit",
  "id": 1
}

$ curl -XGET http://127.0.0.1:5000/todos -H "X-PG-Auth: my-api-key"
{
  "data": [
    {
      "complete": true,
      "description": "Find product market fit",
      "id": 1
    }
  ]
}
```
