"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.aliases import alias_utils


class ListTestCase(unittest.TestCase):
    def testListDisjointMerging(self):
        existing = ['a', 'b', 'c']
        model = ['d', 'e', 'f']
        expected = ['a', 'b', 'c', 'd', 'e', 'f']
        result = alias_utils.merge_model_and_existing_lists(model, existing)
        lists_equal, message = self.__lists_are_equal(result, expected)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(None, existing)
        lists_equal, message = self.__lists_are_equal(result, existing)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(list(), existing)
        lists_equal, message = self.__lists_are_equal(result, existing)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(model, None)
        lists_equal, message = self.__lists_are_equal(result, model)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(model, list())
        lists_equal, message = self.__lists_are_equal(result, model)
        self.assertEqual(lists_equal, True, message)
        return

    def testListOverlappingMerging(self):
        existing = ['a', 'b', 'c']
        model = ['d', 'b', 'a']
        expected = ['a', 'b', 'c', 'd',]
        result = alias_utils.merge_model_and_existing_lists(model, existing)
        lists_equal, message = self.__lists_are_equal(result, expected)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(None, existing)
        lists_equal, message = self.__lists_are_equal(result, existing)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(list(), existing)
        lists_equal, message = self.__lists_are_equal(result, existing)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(model, None)
        lists_equal, message = self.__lists_are_equal(result, model)
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(model, list())
        lists_equal, message = self.__lists_are_equal(result, model)
        self.assertEqual(lists_equal, True, message)
        return

    def testStringListDisjointMerging(self):
        existing = 'a,b,c'
        model = 'd,e,f'
        expected = 'a,b,c,d,e,f'

        result = alias_utils.merge_model_and_existing_lists(model, existing)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        lists_equal, message = self.__lists_are_equal(self.__string_to_list(result), self.__string_to_list(expected))
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(model, None)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        lists_equal, message = self.__lists_are_equal(self.__string_to_list(result), self.__string_to_list(model))
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(None, existing)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        lists_equal, message = self.__lists_are_equal(self.__string_to_list(result), self.__string_to_list(existing))
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists(None, existing.split(','))
        self.assertEqual(type(result), list, 'expected resulting list to come back as a list')
        lists_equal, message = self.__lists_are_equal(result, self.__string_to_list(existing))
        self.assertEqual(lists_equal, True, message)

        result = alias_utils.merge_model_and_existing_lists('', existing)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        lists_equal, message = self.__lists_are_equal(self.__string_to_list(result), self.__string_to_list(existing))
        self.assertEqual(lists_equal, True, message)

        return

    def testStringListWithWhitespaceDisjointMerging(self):
        existing = '  a ,    b,c     '
        model = ' d ,  e  ,   f    '
        expected = 'a,b,c,d,e,f'

        result = alias_utils.merge_model_and_existing_lists(model, existing)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        lists_equal, message = self.__lists_are_equal(self.__string_to_list(result), self.__string_to_list(expected))
        self.assertEqual(lists_equal, True, message)
        return

    def testMergeWithDelete(self):
        existing = 'a,b,c'
        model = '!b,c,d'
        expected = 'a,c,d'

        result = alias_utils.merge_model_and_existing_lists(model, existing)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        self.assertEqual(self.__string_to_list(result), self.__string_to_list(expected))
        return

    def testMergeWithDeleteNotPresent(self):
        existing = 'a,b,c'
        model = '!q,c,d'
        expected = 'a,b,c,d'

        result = alias_utils.merge_model_and_existing_lists(model, existing)
        self.assertEqual(type(result), str, 'expected resulting list to come back as a string')
        self.assertEqual(self.__string_to_list(result), self.__string_to_list(expected))
        return

    def testWindowsPathSeparators(self):
        value = r'c:\foo\bar'
        actual = alias_utils._get_path_separator(value)
        expected = ';'
        self.assertEqual(actual, expected)
        return

    def testDelimitedListToList(self):
        value = 'one;two;three'
        actual = alias_utils.convert_to_model_type("list", value, delimiter=';')
        expected = ['one', 'two', 'three']
        lists_equal, message = self.__lists_are_equal(actual, expected)
        self.assertEqual(lists_equal, True, message)
        return

    def __lists_are_equal(self, actual, expected):
        if actual is None and expected is None:
            return True, 'ok'
        elif actual is None:
            return False, 'actual list was None but expected was not'
        elif expected is None:
            return False, 'expected list was None but actual was not'

        self.assertEqual(len(actual), len(expected),
                         'actual list %s length %s did not match expected list %s length %s' %
                         (str(actual), str(len(actual)), str(expected), str(len(expected))))

        for element in actual:
            if element not in expected:
                return False, 'actual element %s not in expected list %s' % (str(element), str(expected))
        return True, 'ok'

    def __string_to_list(self, string, separator=','):
        return string.split(separator)
