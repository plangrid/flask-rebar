Flask Toolbox
=============
Utilities for jumpstarting a RESTful PlanGrid service.


Summary
-------

What you get:

**Standardized Request and Response Formatting** - No need to reinvent the wheel- flask-toolbox's Rest interface is consistent with PlanGrid best practices.

**Request and Response Validation** - Flask-toolbox is designed to work with [marshmallow](https://marshmallow.readthedocs.io/en/latest/) and is packaged with some common additions (e.g. validating against unexpected fields in request bodies).

**Authentication** - More specifically... lightweight backend service authentication. A service using flask-toolbox is designed to be deployed behind a reverse proxy, so auth is done via a shared token in the ```X-PG-Auth``` header, and ```X-PG-UserId``` is assumed to be trustworthy.

**Error Handling** - All you need to do to get a proper JSON HTTP error response is throw an exception.

**Bugsnag Configuration** - Flask-toolbox forwards uncaught exceptions to bugsnag.

**Healthcheck** - Kubernetes expects a healthcheck to know if a service was properly deployed - flask-toolbox includes one out of the box.

___

What you don't get:

**Content Negotiation** - Just application/json for now

Installation
------------

```
pip install plangrid.flask-toolbox
```


Example Usage
-------------

```python
from flask import Flask
from plangrid.flask_toolbox import (
    Toolbox, 
    response, 
    paginated_response,
    get_query_string_params_or_400,
    get_json_body_params_or_400,
    marshal
)
from plangrid.flask_toolbox.validation import (
    RequestSchema, 
    ResponseSchema, 
    Skip, 
    Limit
)
from marshmallow import fields

app = Flask(__name__)

# Instantiate the toolbox as a Flask extension
Toolbox(app, pagination_limit_max=5, base_url='https://io.todo.com')


todo_database = []


class CreateTodoSchema(RequestSchema):
    complete = fields.Boolean(required=True)
    description = fields.String(required=True)


class UpdateTodoSchema(RequestSchema):
    complete = fields.Boolean()
    description = fields.String()


class GetTodoListSchema(RequestSchema):
    skip = Skip()
    limit = Limit()


class TodoSchema(ResponseSchema):
    id = fields.Integer(required=True)
    complete = fields.Boolean(required=True)
    description = fields.String(required=True)


@app.route('/todos', methods=['POST'])
def create_todos():
    params = get_json_body_params_or_400(schema=CreateTodoSchema())
    todo_database.append(params)
    todo_id = len(todo_database) - 1
    marshaled = marshal(
        data={
            'complete': params['complete'],
            'description': params['description'],
            'id': todo_id
        },
        schema=TodoSchema()
    )
    return response(data=marshaled, status_code=201)


@app.route('/todos', methods=['GET'])
def get_todos():
    params = get_query_string_params_or_400(schema=GetTodoListSchema())
    skip = params['skip']
    limit = params['limit']
    todos = [
        {
            'id': i,
            'complete': todo['complete'],
            'description': todo['description']
        }
        for i, todo in enumerate(todo_database[skip:skip + limit])
    ]
    marshaled = marshal(
        data=todos,
        schema=TodoSchema(many=True)
    )
    return paginated_response(
        data=marshaled,
        total_count=len(todo_database)
    )


@app.route('/todos/<int:todo_id>', methods=['PATCH'])
def update_todo(todo_id):
    params = get_json_body_params_or_400(schema=UpdateTodoSchema)
    todo_database[todo_id].update(params)
    todo = todo_database[todo_id]
    marshaled = marshal(
        data={
            'complete': todo['complete'],
            'description': todo['description'],
            'id': todo_id
        },
        schema=TodoSchema()
    )
    return response(data=marshaled)


if __name__ == '__main__':
    app.run()
```


Then we can play with our new service:


```
# Create some todo items

$ curl -XPOST http://127.0.0.1:5000/todos -H "Content-Type: application/json" -d '{"complete":false,"description":"Engage eigenthrottle"}'
{
  "complete": false,
  "description": "Engage eigenthrottle",
  "id": 0
}
$ curl -XPOST http://127.0.0.1:5000/todos -H "Content-Type: application/json" -d '{"complete":false,"description":"Soak Ferrous Holospectrum"}'
{
  "complete": false,
  "description": "Soak Ferrous Holospectrum",
  "id": 1
}
$ curl -XPOST http://127.0.0.1:5000/todos -H "Content-Type: application/json" -d '{"complete":false,"description":"Set Newtonian Photomist to maximum"}'
{
  "complete": false,
  "description": "Set Newtonian Photomist to maximum",
  "id": 2
}
$ curl -XPOST http://127.0.0.1:5000/todos -H "Content-Type: application/json" -d '{"complete":false,"description":"Set shiftsanitzer to 1"}'
{
  "complete": false,
  "description": "Set shiftsanitzer to 1",
  "id": 3
}
$ curl -XPOST http://127.0.0.1:5000/todos -H "Content-Type: application/json" -d '{"complete":false,"description":"Set sigmaclapper to 0"}'
{
  "complete": false,
  "description": "Set sigmaclapper to 0",
  "id": 4
}
$ curl -XPOST http://127.0.0.1:5000/todos -H "Content-Type: application/json" -d '{"complete":false,"description":"Set steamsaucer manifold to maximum"}'
{
  "complete": false,
  "description": "Set steamsaucer manifold to maximum",
  "id": 5
}

# Paginate through the todo items

$ curl -XGET 'http://127.0.0.1:5000/todos'
{
  "data": [
    {
      "complete": false,
      "description": "Engage eigenthrottle",
      "id": 0
    },
    {
      "complete": false,
      "description": "Soak Ferrous Holospectrum",
      "id": 1
    },
    {
      "complete": false,
      "description": "Set Newtonian Photomist to maximum",
      "id": 2
    },
    {
      "complete": false,
      "description": "Set shiftsanitzer to 1",
      "id": 3
    },
    {
      "complete": false,
      "description": "Set sigmaclapper to 0",
      "id": 4
    }
  ],
  "next_page_url": "https://io.todo.com/todos?limit=5&skip=5",
  "total_count": 6
}
$ curl -XGET 'http://127.0.0.1:5000/todos?limit=5&skip=5'
{
  "data": [
    {
      "complete": false,
      "description": "Set steamsaucer manifold to maximum",
      "id": 0
    }
  ],
  "next_page_url": null,
  "total_count": 6
}

# Update one of the todo items

$ curl -XPATCH 'http://127.0.0.1:5000/todos/2' -H "Content-Type: application/json" -d '{"complete":true}'
{
  "complete": true,
  "description": "Set Newtonian Photomist to maximum",
  "id": 2
}

# Bad Request!

$ curl -XPATCH 'http://127.0.0.1:5000/todos/3' -H "Content-Type: application/json" -d '{"complete":"not boolean!"}'
{
  "errors": {
    "complete": "Not a valid boolean."
  },
  "message": "JSON body parameters are invalid."
}
```




