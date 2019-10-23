"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest
import os

import java.util.logging.Level as JLevel

from wlsdeploy.util import cla_helper


class MergeModelTest(unittest.TestCase):
    """
    This test verifies merge model functionality provided in cla_helper.py.
    """
    _resources_dir = '../../test-classes/'

    # def testSingleModel(self):
    #     model_name = 'derek1'
    #     model_file_path = os.path.join(self._resources_dir, '%s.yaml' % model_name)
    #
    #     merged_model = cla_helper.merge_model_files(model_file_path)
    #     target = open('single.json', 'a')
    #     target.write(str(merged_model))
    #     print 'SINGLE MODEL'
    #     print merged_model

    def testJndiReplacement(self):
        model_name1 = 'derek1'
        model_name2 = 'derek2'
        model_list = self.__get_model_path(model_name1) + "," + self.__get_model_path(model_name2)

        merged_model = cla_helper.merge_model_files(model_list)
        target = open('merged.json', 'a')
        target.write(str(merged_model))
        print 'MERGED MODEL'
        print str(merged_model)

    def __get_model_path(self, name):
        return os.path.join(self._resources_dir, '%s.yaml' % name)

if __name__ == '__main__':
    unittest.main()