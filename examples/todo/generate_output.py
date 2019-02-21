import os
import subprocess
import json
import contextlib


this_directory = os.path.dirname(os.path.realpath(__file__))
todo_app_filepath = os.path.join(this_directory, "todo.py")
todo_output_filepath = os.path.join(this_directory, "todo_output.md")


@contextlib.contextmanager
def app():
    print("Starting app...")

    app_process = None
    try:
        app_process = subprocess.Popen(
            args=["python", todo_app_filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the app to startup by polling the service
        up = False
        while not up:
            try:
                subprocess.check_output(
                    "curl -s http://127.0.0.1:5000/swagger", shell=True
                )
                up = True
            except subprocess.SubprocessError:
                pass

        yield

    finally:
        if app_process:
            app_process.terminate()


def main():
    output = []

    with app():
        output.extend(
            [
                "# cURL and examples/todo.py",
                "Here's a snippet of playing with the application inside todo.py.",
                "",
            ]
        )

        for title, commands in [
            ("Swagger for free!", ["curl -s -XGET http://127.0.0.1:5000/swagger"]),
            (
                "Request validation!",
                [
                    'curl -s -XPATCH http://127.0.0.1:5000/todos/1 -H "X-MyApp-Key: my-api-key" -H "Content-Type: application/json" -d \'{"complete": "wrong type, for demonstration of validation"}\''
                ],
            ),
            (
                "Authentication!",
                [
                    "curl -s -XGET http://127.0.0.1:5000/todos",
                    'curl -s -XGET http://127.0.0.1:5000/todos -H "X-MyApp-Key: my-api-key"',
                ],
            ),
            (
                "CRUD!",
                [
                    'curl -s -XPOST http://127.0.0.1:5000/todos -H "X-MyApp-Key: my-api-key" -H "Content-Type: application/json" -d \'{"complete": false, "description": "Find product market fit"}\'',
                    'curl -s -XPATCH http://127.0.0.1:5000/todos/1 -H "X-MyApp-Key: my-api-key" -H "Content-Type: application/json" -d \'{"complete": true}\'',
                    'curl -s -XGET http://127.0.0.1:5000/todos -H "X-MyApp-Key: my-api-key"',
                ],
            ),
        ]:
            output.extend([title, "```"])

            for command in commands:
                print(command)

                result = subprocess.check_output(command, shell=True)

                output.extend(
                    ["$ " + command, json.dumps(json.loads(result), indent=2)]
                )

            output.extend(["```", ""])

    print("Writing output to {}".format(todo_output_filepath))

    with open(todo_output_filepath, "w") as f:
        f.write("\n".join(output))

    print("Done!")


if __name__ == "__main__":
    main()
