# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.


class ConfigError(ValueError):
    pass


class MethodNotImplement(NotImplementedError):
    pass


class FormError(ValueError):
    def __init__(self, form, error_msg, errors):
        """
        :param form:
        :param error_msg: summary error msg
        :param errors: a dict like {field: [error_detail, ]}
        """
        self.form = form
        self.error_msg = error_msg
        self.errors = errors