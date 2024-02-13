"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.util import path_helper

class PosixPathHelperTestCase(unittest.TestCase):
    """
    Local Posix file system path only test class.
    """

    def setUp(self):
        self.name = 'PosixPathHelperTestCase'
        path_helper.initialize_path_helper(ExceptionType.SSH, unit_test_force=True, unit_test_is_windows=False)
        self.path_helper = path_helper.get_path_helper()
        self.root_directory = '/'

    ###########################################################################################
    #                                  join() Tests                                           #
    ###########################################################################################

    def testJoin(self):
        base_dir = self.root_directory
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = '/foo/bar/baz.yaml'

        actual = self.path_helper.join(base_dir, arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testJoin_WithRelativeDirectory(self):
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = 'foo/bar/baz.yaml'

        actual = self.path_helper.join(arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testJoin_WithSingleArg(self):
        arg1 = '/u01'
        expected = arg1

        actual = self.path_helper.join(arg1)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               local_join() Tests                                        #
    ###########################################################################################

    def testLocalJoin(self):
        base_dir = self.root_directory
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = '/foo/bar/baz.yaml'

        actual = self.path_helper.local_join(base_dir, arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testLocalJoin_WithRelativeDirectory(self):
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = 'foo/bar/baz.yaml'

        actual = self.path_helper.local_join(arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testLocalJoin_WithSingleArg(self):
        arg1 = '/u01'
        expected = arg1

        actual = self.path_helper.local_join(arg1)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               fixup_path() Tests                                        #
    ###########################################################################################

    def testFixupPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupPath_WithAbsolutePathAndRelativeTo(self):
        source_path = '/foo/bar/baz.yaml'
        relative_to = '/u01/domains/mydomain'
        expected = source_path

        actual = self.path_helper.fixup_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar/baz.yaml'
        relative_to = '/u01/domains/mydomain'
        expected = relative_to + '/' + source_path

        actual = self.path_helper.fixup_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                              fixup_local_path() Tests                                   #
    ###########################################################################################

    def testFixupLocalPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_local_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupLocalPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_local_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupLocalPath_WithAbsolutePathAndRelativeTo(self):
        source_path = '/foo/bar/baz.yaml'
        relative_to = '/u01/domains/mydomain'
        expected = source_path

        actual = self.path_helper.fixup_local_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupLocalPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar/baz.yaml'
        relative_to = '/u01/domains/mydomain'
        expected = relative_to + '/' + source_path

        actual = self.path_helper.fixup_local_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                              get_canonical_path() Tests                                 #
    ###########################################################################################

    def testGetCanonicalPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.get_canonical_path(source_path)
        self.assertEquals(actual, expected)

    #
    # Cannot reliably test get_canonical_path() with a relative path and
    # no relative_to value without making assumptions about the underlying
    # file system.
    #

    def testGetCanonicalPath_WithAbsolutePathAndRelativeTo(self):
        source_path = '/foo/bar/baz.yaml'
        relative_to = '/u01'
        expected = source_path

        actual = self.path_helper.get_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar/baz.yaml'
        relative_to = '/foo'
        expected = relative_to + '/' + source_path

        actual = self.path_helper.get_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithPathWithDots(self):
        source_path = '/foo/./bar/../bar/baz.yaml'
        expected = '/foo/bar/baz.yaml'

        actual = self.path_helper.get_canonical_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                           get_local_canonical_path() Tests                              #
    ###########################################################################################

    def testGetLocalCanonicalPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.get_local_canonical_path(source_path)
        self.assertEquals(actual, expected)

    #
    # Cannot reliably test get_local_canonical_path() with a relative path and
    # no relative_to value without making assumptions about the underlying
    # file system.
    #

    def testGetLocalCanonicalPath_WithAbsolutePathAndRelativeTo(self):
        source_path = '/foo/bar/baz.yaml'
        relative_to = '/u01'
        expected = source_path

        actual = self.path_helper.get_local_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetLocalCanonicalPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar/baz.yaml'
        relative_to = '/foo'
        expected = relative_to + '/' + source_path

        actual = self.path_helper.get_local_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetLocalCanonicalPath_WithPathWithDots(self):
        source_path = '/foo/./bar/../bar/baz.yaml'
        expected = '/foo/bar/baz.yaml'

        actual = self.path_helper.get_local_canonical_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                             get_parent_directory() Tests                                #
    ###########################################################################################

    def testGetParentDirectory_WithAbsoluteFilePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = '/foo/bar'

        actual = self.path_helper.get_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetParentDirectory_WithRelativeFilePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'bar'

        actual = self.path_helper.get_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetParentDirectory_WithEmptyPath(self):
        source_path = ''
        expected = source_path

        actual = self.path_helper.get_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetParentDirectory_WithNullPath(self):
        source_path = None
        expected = source_path

        actual = self.path_helper.get_parent_directory(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                          get_local_parent_directory() Tests                             #
    ###########################################################################################

    def testGetLocalParentDirectory_WithAbsoluteFilePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = '/foo/bar'

        actual = self.path_helper.get_local_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalParentDirectory_WithRelativeFilePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'bar'

        actual = self.path_helper.get_local_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalParentDirectory_WithEmptyPath(self):
        source_path = ''
        expected = source_path

        actual = self.path_helper.get_local_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalParentDirectory_WithNullPath(self):
        source_path = None
        expected = source_path

        actual = self.path_helper.get_local_parent_directory(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               is_absolute_path() Tests                                  #
    ###########################################################################################

    def testIsAbsolutePath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsolutePath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsolutePath_WithEmptyPath(self):
        source_path = ''
        expected = False

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsolutePath_WithNullPath(self):
        source_path = None
        expected = False

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                            is_absolute_local_path() Tests                               #
    ###########################################################################################

    def testIsAbsoluteLocalPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_absolute_local_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteLocalPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_absolute_local_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteLocalPath_WithEmptyPath(self):
        source_path = ''
        expected = False

        actual = self.path_helper.is_absolute_local_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteLocalPath_WithNullPath(self):
        source_path = None
        expected = False

        actual = self.path_helper.is_absolute_local_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               is_relative_path() Tests                                  #
    ###########################################################################################

    def testIsRelativePath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativePath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativePath_WithEmptyPath(self):
        source_path = ''
        expected = True

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativePath_WithNullPath(self):
        source_path = None
        expected = True

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                            is_relative_local_path() Tests                               #
    ###########################################################################################

    def testIsRelativeLocalPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_relative_local_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeLocalPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_relative_local_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeLocalPath_WithEmptyPath(self):
        source_path = ''
        expected = True

        actual = self.path_helper.is_relative_local_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeLocalPath_WithNullPath(self):
        source_path = None
        expected = True

        actual = self.path_helper.is_relative_local_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                            get_filename_from_path() Tests                               #
    ###########################################################################################

    def testGetFilenameFromPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithFileWithNoExt(self):
        source_path = '/foo/bar/baz'
        expected = 'baz'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                         get_local_filename_from_path() Tests                            #
    ###########################################################################################

    def testGetLocalFilenameFromPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_local_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameFromPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_local_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_local_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameFromPath_WithFileWithNoExt(self):
        source_path = '/foo/bar/baz'
        expected = 'baz'

        actual = self.path_helper.get_local_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_local_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_local_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                         get_local_pathname_from_path() Tests                            #
    ###########################################################################################

    def testGetLocalPathnameFromPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = '/foo/bar'

        actual = self.path_helper.get_local_pathname_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalPathnameFromPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'bar'

        actual = self.path_helper.get_local_pathname_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalPathnameFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = None

        actual = self.path_helper.get_local_pathname_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalPathnameFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_local_pathname_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalPathnameFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_local_pathname_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                         get_filename_no_ext_from_path() Tests                           #
    ###########################################################################################

    def testGetFilenameNoExtFromPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithFileWithNoExt(self):
        source_path = '/foo/bar/baz'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                      get_local_filename_no_ext_from_path() Tests                        #
    ###########################################################################################

    def testGetLocalFilenameNoExtFromPath_WithAbsolutePath(self):
        source_path = '/foo/bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_local_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameNoExtFromPath_WithRelativePath(self):
        source_path = 'bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_local_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameNoExtFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_local_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameNoExtFromPath_WithFileWithNoExt(self):
        source_path = '/foo/bar/baz'
        expected = 'baz'

        actual = self.path_helper.get_local_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameNoExtFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_local_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetLocalFilenameNoExtFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_local_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                                   is_jar_file() Tests                                   #
    ###########################################################################################

    def testIsJarFile_WithAbsolutePathToJarFile(self):
        source_path = '/foo/bar/baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithRelativePathToJarFile(self):
        source_path = 'bar/baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithJarFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithAbsolutePathToYamlFile(self):
        source_path = '/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithRelativePathToYamlFile(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithYamlFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithEmptyPath(self):
        source_path = ''
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithNullPath(self):
        source_path = None
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                                is_local_jar_file() Tests                                #
    ###########################################################################################

    def testIsLocalJarFile_WithAbsolutePathToJarFile(self):
        source_path = '/foo/bar/baz.jar'
        expected = True

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithRelativePathToJarFile(self):
        source_path = 'bar/baz.jar'
        expected = True

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithJarFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithAbsolutePathToYamlFile(self):
        source_path = '/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithRelativePathToYamlFile(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithYamlFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithEmptyPath(self):
        source_path = ''
        expected = False

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsLocalJarFile_WithNullPath(self):
        source_path = None
        expected = False

        actual = self.path_helper.is_local_jar_file(source_path)
        self.assertEquals(actual, expected)
