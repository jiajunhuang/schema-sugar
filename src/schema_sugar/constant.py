#!/usr/bin/env python
# coding: utf-8

CREATE_OP = "create"
SHOW_OP = "show"
UPDATE_OP = "update"
DELETE_OP = "delete"

OPERATIONS = (
    CREATE_OP, SHOW_OP, UPDATE_OP, DELETE_OP
)

CLI_MAP = {
    "create": CREATE_OP,
    "show": SHOW_OP,
    "update": UPDATE_OP,
    "delete": DELETE_OP,
}
HTTP_MAP = {
    "post": CREATE_OP,
    "get": SHOW_OP,
    "put": UPDATE_OP,
    "delete": DELETE_OP,
}

