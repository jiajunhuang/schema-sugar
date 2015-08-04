#!/usr/bin/env python
# coding: utf-8
from abc import abstractmethod

import unittest2 as unittest


class TestMethod2OPCONV(unittest.TestCase):

    def test_method2op_letter_case(self):
        from schema_sugar import method2op
        self.assertEqual(method2op("GET"), "show")
        self.assertEqual(method2op("get"), "show")
        self.assertEqual(method2op("Show"), "show")

    def test_method2op_name_conv(self):
        from schema_sugar import method2op
        input_values = [
            "get", "put", "post", "delete",
            "show", "update", "create", "delete",
        ]
        expect_values = [
            "show", "update", "create", "delete",
            "show", "update", "create", "delete",
        ]
        for input_value, expect_value in zip(input_values, expect_values):
            self.assertEqual(method2op(input_value), expect_value)

    def test_method2op_unexpected(self):
        from schema_sugar import method2op

        e = None
        try:
            method2op("haha")
        except ValueError as e:
            pass

        self.assertIsNotNone(e)

class TestResourcesMethod2OPCONV(unittest.TestCase):

    def test_resources_method2op(self):
        from schema_sugar import resources_method2op
        input_values = [
            "post", "get", "POST", "mymethod"
        ]
        expect_values = [
            "create", "index", "create", "mymethod"
        ]
        for input_value, expect_value in zip(input_values, expect_values):
            self.assertEqual(resources_method2op(input_value), expect_value)


class TestIsAbcMethod(unittest.TestCase):

    def setUp(self):
        from schema_sugar import is_abs_method
        self.is_abs_method = is_abs_method

    def test_normal_func(self):
        def normal():
            pass

        @abstractmethod
        def is_abc():
            pass

        self.assertTrue(self.is_abs_method(is_abc))
        self.assertFalse(self.is_abs_method(normal))

    def test_class_method(self):

        class Test(object):

            @abstractmethod
            def test_method(self):
                pass

            def normal_method(self):
                pass

            @classmethod
            @abstractmethod
            def cls_method(cls):
                pass

        test = Test()

        self.assertTrue(self.is_abs_method(test.test_method))
        self.assertTrue(self.is_abs_method(Test.cls_method))
        self.assertFalse(self.is_abs_method(test.normal_method))


class TestJsonForm(unittest.TestCase):

    def setUp(self):
        from schema_sugar import JsonForm
        self.JsonForm = JsonForm
        self.base_schema = {
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "string"},
            },
            "required": ["field1", ],
        }
        self.base_valid_data = {"field1": "haha"}

    def test_normal_schema(self):

        class MyForm(self.JsonForm):
            schema = self.base_schema
        form = MyForm(self.base_valid_data)
        self.assertEqual(self.base_schema, form.schema)

    def test_live_schema(self):
        form = self.JsonForm(self.base_valid_data, live_schema=self.base_schema)

        self.assertEqual(form.schema, self.base_schema)

    def test_both_schema(self):

        class MyForm(self.JsonForm):
            schema = self.base_schema

        live_schema = {
            "type": "object",
            "properties": {
                "field2": {"type": "number"},
                "field3": {"type": "string"},
            },
            "required": ["field2", ],
        }
        form = MyForm({}, live_schema=live_schema)
        self.assertEqual(
            form.schema,
            {
                "type": "object",
                "properties": {
                    "field1": {"type": "string"},
                    "field2": {"type": "number"},
                    "field3": {"type": "string"},
                },
                "required": ["field2", "field1"],
            }
        )

    def test_validation_success(self):
        class MyForm(self.JsonForm):
            schema = self.base_schema
        form = MyForm(self.base_valid_data)
        self.assertTrue(form.validate())

    def test_validataion_fail(self):
        class MyForm(self.JsonForm):
            schema = self.base_schema
        form = MyForm({})
        self.assertFalse(form.validate())
        self.assertIsNotNone(form.errors)

    def test_data_filter(self):
        class MyForm(self.JsonForm):
            schema = self.base_schema
        form = MyForm({
            "field1": "hello",
            "field2": "hello",
            "field3": "hello",
        })
        self.assertFalse("filed3" in form.data)

    def test_non_strict_mode(self):
        class MyForm(self.JsonForm):
            schema = self.base_schema
        form = MyForm({
            "field1": "hello",
            "field2": 1,
        })
        self.assertEqual(form.data["field2"], "1")

    def test_strict_mode(self):
        class MyForm(self.JsonForm):
            schema = self.base_schema
        form = MyForm(
            {
                "field1": "hello",
                "field2": 1,
            },
            strict=True,
        )
        self.assertEqual(form.data["field2"], 1)


class TestArgGenerator(unittest.TestCase):

    def test_default_type(self):
        from schema_sugar import cli_arg_generator

        class Hello(object):
            pass
        e = None

        try:
            cli_arg_generator(Hello)
        except ValueError as e:
            pass
        self.assertIsNotNone(e)