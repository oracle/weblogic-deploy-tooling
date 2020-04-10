"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import unittest

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict


class CollectionsTestCase(unittest.TestCase):

    def setUp(self):
        self.name = 'CollectionsTestCase'

    def testIsInstance(self):
        my_ordered_dict = OrderedDict()

        # A type(myOrderedDict) needs to <return True
        self.assertEqual(isinstance(my_ordered_dict, dict), True)
        self.assertEqual(type(my_ordered_dict) is OrderedDict, True)

    def testKeys(self):
        my_ordered_dict = OrderedDict()
        my_ordered_dict['nba_player'] = 'Steph Curry'
        my_ordered_dict['nba_mvp_count'] = 1
        my_ordered_dict['is_retired'] = False
        my_ordered_dict['nba_finals_years'] = ['2015', '2016', '2017']

        expected = ['nba_player', 'nba_mvp_count', 'is_retired', 'nba_finals_years']
        keys = my_ordered_dict.keys()
        self.assertEqual(len(expected), len(keys),
                         'expected the ordered dict keys to be the same length as the expected keys')
        for i, key in enumerate(keys):
            self.assertEqual(key, expected[i], 'expected key at position %s to be %s' % (str(i), expected[i]))

    def testValues(self):
        my_ordered_dict = OrderedDict()
        my_ordered_dict['nba_player'] = 'Steph Curry'
        my_ordered_dict['nba_mvp_count'] = 1
        my_ordered_dict['is_retired'] = False
        my_ordered_dict['nba_finals_years'] = ['2015', '2016', '2017']

        expected_values = ['Steph Curry', 1, False, ['2015', '2016', '2017']]
        values = my_ordered_dict.getValues()
        self.assertEqual(len(expected_values), len(values),
                         'expected the ordered dict values to be the same length as the expected values')
        for i, value in enumerate(values):
            self.assertEqual(value, expected_values[i],
                             'expected value at position %s to be %s' % (str(i), str(expected_values[i])))

    def testIteritems(self):
        my_ordered_dict = OrderedDict()
        my_ordered_dict['nba_player'] = 'Steph Curry'
        my_ordered_dict['nba_mvp_count'] = 1
        my_ordered_dict['is_retired'] = False
        my_ordered_dict['nba_finals_years'] = ['2015', '2016', '2017']

        result = isinstance(my_ordered_dict, dict)
        self.assertEqual(result, True, 'expected ordered dict to be an instance of dict')

        # A myOrderedDict.iteritems() needs to work like
        # a built-in Python dict

        expected_keys = ['nba_player', 'nba_mvp_count', 'is_retired', 'nba_finals_years']
        expected_values = ['Steph Curry', 1, False, ['2015', '2016', '2017']]

        index = 0
        for key, value in my_ordered_dict.iteritems():
            self.assertEqual(key, expected_keys[index],
                             'expected key at position %s to be %s' % (str(index), expected_keys[index]))
            self.assertEqual(value, expected_values[index])
            index += 1

    def testCopyConstructorKeyOrdering(self):
        my_ordered_dict = OrderedDict()
        my_ordered_dict['one'] = 1
        my_ordered_dict['two'] = 2
        my_ordered_dict['five'] = 5
        my_ordered_dict['three'] = 3
        my_ordered_dict['four'] = 4

        copy_ordered_dict = OrderedDict(my_ordered_dict)

        # A myOrderedDict.keys() needs to return the keys, in the
        # exact order that they were inserted
        expected = ['one', 'two', 'five', 'three', 'four']
        copy_ordered_dict_keys = copy_ordered_dict.keys()
        for i in range(len(expected)):
            self.assertEqual(copy_ordered_dict_keys[i], expected[i])

    def testCopyDeepcopyKeyOrdering(self):
        my_ordered_dict = OrderedDict()
        my_ordered_dict['one'] = 1
        my_ordered_dict['two'] = 2
        my_ordered_dict['five'] = [5, 5, 5]
        my_dict = { 'three': 3 }
        my_ordered_dict['three'] = my_dict
        my_ordered_dict['four'] = 4

        # Doing a copy.deepcopy() on a PyOrderedDict object needs to
        # return a new PyOrderedDict, which is a deep copy. Deep copy
        # means a deep copy of the values in the PyOrderedDict's
        # underlying java.util.LinkedHashMap, as well, recursively.
        #
        copy_ordered_dict = copy.deepcopy(my_ordered_dict)

        index = 0
        expected_keys = ['one', 'two', 'five', 'three', 'four']
        for key, value in copy_ordered_dict.iteritems():
            self.assertEqual(key, expected_keys.__getitem__(index))
            index += 1

        # Change the value of the entries in the copy and verify the
        # original has not changed.

        new_dict = copy_ordered_dict['three']
        new_dict['three'] = 333
        new_dict['new_key'] = 'my new value'
        self.assertEqual(my_dict['three'], 3, 'expected original three attribute to have the original value 3')
        self.assertEqual('new_key' in my_dict, False, 'expected the original dict not to have the key new_key')

        # The value of the entry in the original PyOrderedDict
        # (my_ordered_dict) with 'two' as the key, should still
        # the value it was before the value of copy_ordered_dict['two']
        # was changed to something else.

        key = 'two'
        copy_ordered_dict[key] = 8
        self.assertEqual(my_ordered_dict[key], 2)

        expected = 2
        self.assertEqual(my_ordered_dict[key], expected)

        my_list = [1, 2, 3, 4, 5]
        first_ordered_dict = OrderedDict()
        first_ordered_dict['my_list'] = my_list
        second_ordered_dict = OrderedDict()
        second_ordered_dict['first'] = first_ordered_dict
        second_ordered_dict['second'] = None
        second_ordered_dict['third'] = int(1)
        second_ordered_dict['fourth'] = long(123456)
        second_ordered_dict['fifth'] = float(12.34567)
        second_ordered_dict['sixth'] = float(1200000000.34567)
        second_ordered_dict['seventh'] = 'abcdefg'
        second_ordered_dict['eighth'] = { 'a': 'abc', 'b': 'def', 'c': 12345, 'd': 12345.6789}
        second_ordered_dict['ninth'] = ['a', 'b', 'c', 'd']

        my_copy = copy.deepcopy(second_ordered_dict)
        new_list = my_copy['first']['my_list']
        new_list.extend([6, 7, 8, 9, 10])
        self.assertEqual(len(my_list), 5, 'expected deepcopy to make a copy of my_list but it did not')

    def testDictDictUpdate(self):
        dict1 = dict()
        dict1['entry1'] = 'you'
        dict2 = dict()
        dict2['entry2'] = 'me'
        dict1.update(dict2)
        self.assertEqual('entry1' in dict1 and 'entry2' in dict1, True,
                         "expected dict1 to contain 'entry1' and 'entry2' keys")

    def testOrderedDictOrderedDictUpdate(self):
        dict1 = OrderedDict()
        dict1['entry1'] = 'you'
        dict2 = OrderedDict()
        dict2['entry2'] = 'me'
        dict1.update(dict2)
        self.assertEqual('entry1' in dict1 and 'entry2' in dict1, True,
                         "expected ordereddict1 to contain 'entry1' and 'entry2' keys")

    def testOrderedDictDictUpdate(self):
        dict1 = OrderedDict()
        dict1['entry1'] = 'you'
        dict2 = dict()
        dict2['entry2'] = 'me'
        dict1.update(dict2)
        self.assertEqual('entry1' in dict1 and 'entry2' in dict1, True,
                         "expected ordereddict1 to contain 'entry1' and 'entry2' keys")

    def testDictOrderedDictUpdate(self):
        dict1 = dict()
        dict1['entry1'] = 'you'
        dict2 = OrderedDict()
        dict2['entry2'] = 'me'
        dict1.update(dict2)
        self.assertEqual('entry1' in dict1 and 'entry2' in dict1, True,
                         "expected ordereddict1 to contain 'entry1' and 'entry2' keys")

    def testOrderedDictSort(self):
        dict1 = OrderedDict()
        dict1['SecurityConfig.myrealm.IoT-IDCS-Authenticator.ClientSecretEncrypted'] = ''
        dict1['AdminUserName'] = ''
        dict1['ServerTemp.ms-template.SSL.ListenPort'] = '8100'
        dict1['AdminPassword'] = ''
        dict1['JDBC.IoTServerDS.user.Value'] = 'admin'
        dict1['SecurityConfig.CredentialEncrypted'] = ''
        dict1['JDBC.IoTServerDS.PasswordEncrypted'] = ''
        dict1['SecurityConfig.NodeManagerUsername'] = 'iot'

        sorted_dict = OrderedDict()
        sorted_keys = dict1.keys()
        sorted_keys.sort()
        for key in sorted_keys:
            sorted_dict[key] = dict1[key]

        self.assertEqual(sorted_dict.getValues()[-1], '8100',
                         'expected dictionary to be sorted by name')


if __name__ == '__main__':
    unittest.main()
