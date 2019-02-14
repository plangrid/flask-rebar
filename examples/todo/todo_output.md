# cURL and examples/todo.py
Here's a snippet of playing with the application inside todo.py.

Swagger for free!
```
$ curl -s -XGET http://127.0.0.1:5000/swagger
{
  "consumes": [
    "application/json"
  ],
  "definitions": {
    "CreateTodoSchema": {
      "properties": {
        "complete": {
          "type": "boolean"
        },
        "description": {
          "type": "string"
        }
      },
      "required": [
        "complete",
        "description"
      ],
      "title": "CreateTodoSchema",
      "type": "object"
    },
    "Error": {
      "properties": {
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
    "TodoListSchema": {
      "properties": {
        "data": {
          "items": {
            "$ref": "#/definitions/TodoSchema"
          },
          "type": "array"
        }
      },
      "title": "TodoListSchema",
      "type": "object"
    },
    "TodoResourceSchema": {
      "properties": {
        "data": {
          "$ref": "#/definitions/TodoSchema"
        }
      },
      "title": "TodoResourceSchema",
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
        "id",
        "complete",
        "description"
      ],
      "title": "TodoSchema",
      "type": "object"
    },
    "UpdateTodoSchema": {
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
            "description": "TodoListSchema",
            "schema": {
              "$ref": "#/definitions/TodoListSchema"
            }
          },
          "default": {
            "description": "Error",
            "schema": {
              "$ref": "#/definitions/Error"
            }
          }
        },
        "tags": [
          "todo"
        ]
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
            "description": "TodoResourceSchema",
            "schema": {
              "$ref": "#/definitions/TodoResourceSchema"
            }
          },
          "default": {
            "description": "Error",
            "schema": {
              "$ref": "#/definitions/Error"
            }
          }
        },
        "tags": [
          "todo"
        ]
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
            "description": "TodoResourceSchema",
            "schema": {
              "$ref": "#/definitions/TodoResourceSchema"
            }
          },
          "default": {
            "description": "Error",
            "schema": {
              "$ref": "#/definitions/Error"
            }
          }
        },
        "tags": [
          "todo"
        ]
      }
    }
  },
  "produces": [
    "application/json"
  ],
  "schemes": [
    "http",
    "https"
  ],
  "security": [
    {
      "sharedSecret": []
    }
  ],
  "securityDefinitions": {
    "sharedSecret": {
      "in": "header",
      "name": "X-MyApp-Key",
      "type": "apiKey"
    }
  },
  "swagger": "2.0",
  "tags": [
    {
      "description": "All operations to managing the todo list portion of             the API",
      "name": "todo"
    }
  ]
}
```

Request validation!
```
$ curl -s -XPATCH http://127.0.0.1:5000/todos/1 -H "X-MyApp-Key: my-api-key" -H "Content-Type: application/json" -d '{"complete": "wrong type, for demonstration of validation"}'
{
  "errors": {
    "complete": "Not a valid boolean."
  },
  "message": "JSON body parameters are invalid."
}
```

Authentication!
```
$ curl -s -XGET http://127.0.0.1:5000/todos
{
  "message": "No auth token provided."
}
$ curl -s -XGET http://127.0.0.1:5000/todos -H "X-MyApp-Key: my-api-key"
{
  "data": []
}
```

CRUD!
```
$ curl -s -XPOST http://127.0.0.1:5000/todos -H "X-MyApp-Key: my-api-key" -H "Content-Type: application/json" -d '{"complete": false, "description": "Find product market fit"}'
{
  "data": {
    "complete": false,
    "description": "Find product market fit",
    "id": 1
  }
}
$ curl -s -XPATCH http://127.0.0.1:5000/todos/1 -H "X-MyApp-Key: my-api-key" -H "Content-Type: application/json" -d '{"complete": true}'
{
  "data": {
    "complete": true,
    "description": "Find product market fit",
    "id": 1
  }
}
$ curl -s -XGET http://127.0.0.1:5000/todos -H "X-MyApp-Key: my-api-key"
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
