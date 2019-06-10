"""
    Swagger UI Blueprint
    ~~~~~~~~~~~~~~~~~~~~

    Flask Blueprint for adding Swagger UI to an API.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from flask import Blueprint, render_template, current_app


def create_swagger_ui_blueprint(
    ui_url, swagger_url, name="swagger_ui", page_title="Swagger UI"
):
    """
    Create a blueprint for adding Swagger UI to a service.

    :param str ui_url:
        The path where the Swagger UI will be served from.
        All static files will be served from here as well.
    :param str swagger_url:
        The path (or full URL) where the Swagger UI can retrieve
        the Swagger specification.
    :param str name:
        A name for the blueprint. This is useful if the API is
        hosting multiple instances of the Swagger UI.
    :param str page_title:
        Name to use as the title for the HTML page.
    :rtype: flask.Blueprint
    """
    blueprint = Blueprint(
        name=name,
        import_name=__name__,
        static_folder="static",
        template_folder="templates",
        url_prefix=ui_url,
    )

    template_context = {
        "blueprint_name": name,
        "swagger_url": swagger_url,
        "page_title": page_title,
    }

    @blueprint.route("/")
    @blueprint.route("")
    def show():
        return render_template("index.html.jinja2", **template_context)

    return blueprint
