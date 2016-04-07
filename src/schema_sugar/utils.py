# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
from schema_sugar.constant import CLI2HTTP_MAP, OP2CLI_MAP


def cli2http(cli_operation):
    """
    Convert cli cmd name to http method name
    :type cli_operation: str
    """
    return CLI2HTTP_MAP[cli_operation]


def op2cli(operation_name):
    """
    Convert operation name to human readable cli name.
    :param operation_name: str
    """
    return OP2CLI_MAP[operation_name]