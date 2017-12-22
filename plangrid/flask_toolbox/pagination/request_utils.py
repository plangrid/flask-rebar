try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from flask import request, g

from plangrid.flask_toolbox import response


def _make_url(resource_path, query_params):
    """
    Constructs a full URL for the application.

    :param str resource_path: e.g. /path/to/resource
    :param dict query_params: e.g. {'skip': 0, 'limit': 100}
    :return: e.g. https://io.plangrid.com/path/to/resource?skip=0&limit=100
    :rtype: str
    """
    url_params = urlencode(
        [
            (param, value)
            # sorted so testing is more reliable
            for param, value in sorted(query_params.items())
            if value is not None
        ]
    )

    return '{}://{}{}?{}'.format(request.scheme, request.host, resource_path, url_params)


def paginated_response(data, total_count, additional_data=None, status_code=200):
    """
    Constructs a flask.Response for paginated endpoint.

    :param list data: The current page of data to return to the client
    :param int total_count: The total amount of resources matching the query
    :param dict additional_data: Any additional data to attach to the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    if not hasattr(g, 'pagination_limit_max'):
        raise Exception(
            'paginated_response only works with the Pagination extension!'
        )
    resp = {
        'data': data,
        'total_count': total_count,
        'next_page_url': None
    }

    query_params = request.args.to_dict()

    skip = int(query_params.get('skip', 0))
    limit = int(query_params.get('limit', g.pagination_limit_max))

    if skip + limit < total_count:
        query_params['skip'] = skip + limit
        query_params['limit'] = limit
        resp['next_page_url'] = _make_url(
            resource_path=request.path,
            query_params=query_params
        )

    if additional_data:
        resp.update(additional_data)

    return response(data=resp, status_code=status_code)
