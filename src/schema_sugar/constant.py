# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

SHOW_OP = "show"
UPDATE_OP = "update"
DELETE_OP = "delete"
INDEX_OP = "index"
CREATE_OP = "create"

OPERATIONS = (
    CREATE_OP, SHOW_OP, UPDATE_OP, DELETE_OP, INDEX_OP,
)

CLI2OP_MAP = {
    "create": CREATE_OP,
    "show": SHOW_OP,
    "update": UPDATE_OP,
    "delete": DELETE_OP,
    "list": INDEX_OP,
}

OP2CLI_MAP = dict((v, k) for k, v in CLI2OP_MAP.iteritems())

HTTP_GET = 'get'
HTTP_POST = 'post'
HTTP_PUT = 'put'
HTTP_DELETE = 'delete'

CLI2HTTP_MAP = {
    "create": HTTP_POST,
    "show": HTTP_GET,
    "update": HTTP_PUT,
    "delete": DELETE_OP,
    "list": HTTP_GET,
}

RESOURCE_HTTP2OP_MAP = {
    HTTP_GET: SHOW_OP,
    HTTP_PUT: UPDATE_OP,
    HTTP_POST: CREATE_OP,
    HTTP_DELETE: DELETE_OP,
}

RESOURCES_HTTP2OP_MAP = {
    HTTP_POST: CREATE_OP,
    HTTP_GET: INDEX_OP,
}


def method2op(method_string):
    """
    Convert http method name or cli operation name to crud name string.
    :param method_string:
    :return: converted method string in
    :rtype : basestring
    """
    method_string = method_string.lower()
    if method_string in OPERATIONS:
        return method_string
    elif method_string in CLI2OP_MAP:
        return CLI2OP_MAP[method_string]
    elif method_string in RESOURCE_HTTP2OP_MAP:
        return RESOURCE_HTTP2OP_MAP[method_string]
    else:
        raise ValueError("method `%s` not in convention map" % method_string)


def resources_method2op(method_string):
    """
    Convert http method to operation for a `resources`.
    :type method_string: str or unicode
    :rtype : str or unicode
    """
    method_string = method_string.lower()
    if method_string in RESOURCES_HTTP2OP_MAP:
        return RESOURCES_HTTP2OP_MAP[method_string]
    else:
        return method_string
