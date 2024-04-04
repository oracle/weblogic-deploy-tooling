"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.util import path_helper

class PosixToWindowsPathHelperTestCase(unittest.TestCase):
    """
    Remote Windows file system path only test class.
    """

    def setUp(self):
        self.name = 'PosixToWindowsPathHelperTestCase'
        path_helper.initialize_path_helper(ExceptionType.SSH, unit_test_force=True, unit_test_is_windows=False)
        path_helper.set_remote_file_system_from_oracle_home('c:\\oracle\\wls12213')
        self.path_helper = path_helper.get_path_helper()
        self.root_directory = 'c:\\'

    ###########################################################################################
    #                                  join() Tests                                           #
    ###########################################################################################

    def testJoin(self):
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = self.root_directory + '\\'.join([arg1, arg2, arg3])

        actual = self.path_helper.join(self.root_directory, arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testJoin_WithRelativeDirectory(self):
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = '\\'.join([arg1, arg2, arg3])

        actual = self.path_helper.join(arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testJoin_WithSingleArg(self):
        arg1 = self.root_directory
        expected = arg1

        actual = self.path_helper.join(arg1)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               remote_join() Tests                                        #
    ###########################################################################################

    def testRemoteJoin(self):
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = self.root_directory + '\\'.join([arg1, arg2, arg3])

        actual = self.path_helper.remote_join(self.root_directory, arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testRemoteJoin_WithRelativeDirectory(self):
        arg1 = 'foo'
        arg2 = 'bar'
        arg3 = 'baz.yaml'
        expected = '\\'.join([arg1, arg2, arg3])

        actual = self.path_helper.remote_join(arg1, arg2, arg3)
        self.assertEquals(actual, expected)

    def testRemoteJoin_WithSingleArg(self):
        arg1 = self.root_directory
        expected = arg1

        actual = self.path_helper.remote_join(arg1)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               fixup_path() Tests                                        #
    ###########################################################################################

    def testFixupPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = source_path.replace('\\', '/')

        actual = self.path_helper.fixup_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupPath_WithAbsolutePathAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = source_path.replace('\\', '/')

        actual = self.path_helper.fixup_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupPath_WithRelativePathAndForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupPath_WithAbsolutePathAndRelativeTo(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        relative_to = 'd:\\domains\\mydomain'
        expected = source_path.replace('\\', '/')

        actual = self.path_helper.fixup_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupPath_WithAbsolutePathAndForwardSlashesAndRelativeTo(self):
        source_path = 'c:/foo/bar/baz.yaml'
        relative_to = 'd:/domains/mydomain'
        expected = source_path

        actual = self.path_helper.fixup_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar\\baz.yaml'
        relative_to = 'd:\\domains\\mydomain'
        expected = ('%s\\%s' % (relative_to, source_path)).replace('\\', '/')

        actual = self.path_helper.fixup_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupPath_WithRelativePathAndForwardSlashesAndRelativeTo(self):
        source_path = 'bar/baz.yaml'
        relative_to = 'd:/domains/mydomain'
        expected = relative_to + '/' + source_path

        actual = self.path_helper.fixup_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                              fixup_remote_path() Tests                                   #
    ###########################################################################################

    def testFixupRemotePath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = source_path.replace('\\', '/')

        actual = self.path_helper.fixup_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithAbsolutePathAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = source_path.replace('\\', '/')

        actual = self.path_helper.fixup_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithRelativePathAndForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = source_path

        actual = self.path_helper.fixup_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithAbsolutePathAndRelativeTo(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        relative_to = 'd:\\domains\\mydomain'
        expected = source_path.replace('\\', '/')

        actual = self.path_helper.fixup_remote_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithAbsolutePathAndForwardSlashesAndRelativeTo(self):
        source_path = 'c:/foo/bar/baz.yaml'
        relative_to = 'd:/domains/mydomain'
        expected = source_path

        actual = self.path_helper.fixup_remote_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar\\baz.yaml'
        relative_to = 'd:\\domains\\mydomain'
        expected = ('%s\\%s' % (relative_to, source_path)).replace('\\', '/')

        actual = self.path_helper.fixup_remote_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testFixupRemotePath_WithRelativePathAndForwardSlashesAndRelativeTo(self):
        source_path = 'bar/baz.yaml'
        relative_to = 'd:/domains/mydomain'
        expected = relative_to + '/' + source_path

        actual = self.path_helper.fixup_remote_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                           get_canonical_path() Tests                                    #
    ###########################################################################################

    def testGetCanonicalPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = source_path

        actual = self.path_helper.get_canonical_path(source_path)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithAbsolutePathAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = source_path.replace('/', '\\')

        actual = self.path_helper.get_canonical_path(source_path)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        # kind of hacky since the OS running the build could be using a posix file system...
        expected = (os.getcwd() + '\\' + source_path).replace('/', '\\')

        actual = self.path_helper.get_canonical_path(source_path).replace('/', '\\')
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithRelativePathWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        # kind of hacky since the OS running the build could be using a posix file system...
        expected = (os.getcwd() + '/' + source_path).replace('/', '\\')

        actual = self.path_helper.get_canonical_path(source_path).replace('/', '\\')
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithAbsolutePathAndRelativeTo(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        relative_to = 'd:\\u01'
        expected = source_path

        actual = self.path_helper.get_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithAbsolutePathAndRelativeToAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        relative_to = 'd:/u01'
        expected = source_path.replace('/', '\\')

        actual = self.path_helper.get_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar\\baz.yaml'
        relative_to = 'c:\\foo'
        expected = relative_to + '\\' + source_path

        actual = self.path_helper.get_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithRelativePathAndRelativeToAndForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        relative_to = 'c:/foo'
        expected = (relative_to + '/' + source_path).replace('/', '\\')

        actual = self.path_helper.get_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithPathWithDots(self):
        source_path = 'c:\\foo\\.\\bar\\..\\bar\\baz.yaml'
        expected = 'c:\\foo\\bar\\baz.yaml'

        actual = self.path_helper.get_canonical_path(source_path)
        self.assertEquals(actual, expected)

    def testGetCanonicalPath_WithPathWithDotsAndForwardSlashes(self):
        source_path = 'c:/foo/./bar/../bar/baz.yaml'
        expected = 'c:\\foo\\bar\\baz.yaml'

        actual = self.path_helper.get_canonical_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                           get_remote_canonical_path() Tests                              #
    ###########################################################################################

    def testGetRemoteCanonicalPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = source_path

        actual = self.path_helper.get_remote_canonical_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithAbsolutePathAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = source_path.replace('/', '\\')

        actual = self.path_helper.get_remote_canonical_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        # kind of hacky since the OS running the build could be using a posix file system...
        expected = (os.getcwd() + '\\' + source_path).replace('/', '\\')

        actual = self.path_helper.get_remote_canonical_path(source_path).replace('/', '\\')
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithRelativePathWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        # kind of hacky since the OS running the build could be using a posix file system...
        expected = (os.getcwd() + '/' + source_path).replace('/', '\\')

        actual = self.path_helper.get_remote_canonical_path(source_path).replace('/', '\\')
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithAbsolutePathAndRelativeTo(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        relative_to = 'd:\\u01'
        expected = source_path

        actual = self.path_helper.get_remote_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithAbsolutePathAndRelativeToAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        relative_to = 'd:/u01'
        expected = source_path.replace('/', '\\')

        actual = self.path_helper.get_remote_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithRelativePathAndRelativeTo(self):
        source_path = 'bar\\baz.yaml'
        relative_to = 'c:\\foo'
        expected = relative_to + '\\' + source_path

        actual = self.path_helper.get_remote_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithRelativePathAndRelativeToAndForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        relative_to = 'c:/foo'
        expected = (relative_to + '/' + source_path).replace('/', '\\')

        actual = self.path_helper.get_remote_canonical_path(source_path, relative_to)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithPathWithDots(self):
        source_path = 'c:\\foo\\.\\bar\\..\\bar\\baz.yaml'
        expected = 'c:\\foo\\bar\\baz.yaml'

        actual = self.path_helper.get_remote_canonical_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteCanonicalPath_WithPathWithDotsAndForwardSlashes(self):
        source_path = 'c:/foo/./bar/../bar/baz.yaml'
        expected = 'c:\\foo\\bar\\baz.yaml'

        actual = self.path_helper.get_remote_canonical_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                             get_parent_directory() Tests                                #
    ###########################################################################################

    def testGetParentDirectory_WithAbsoluteFilePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = 'c:\\foo\\bar'

        actual = self.path_helper.get_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetParentDirectory_WithAbsoluteFilePathAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = 'c:/foo/bar'

        actual = self.path_helper.get_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetParentDirectory_WithRelativeFilePath(self):
        source_path = 'bar\\baz.yaml'
        try:
            __ = self.path_helper.get_parent_directory(source_path)
            self.fail('Expected get_parent_directory() to fail with an active remote path module and a relative path')
        except:
            pass

    def testGetParentDirectory_WithRelativeFilePathAndForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        try:
            __ = self.path_helper.get_parent_directory(source_path)
            self.fail('Expected get_parent_directory() to fail with an active remote path module and a relative path')
        except:
            pass

    def testGetParentDirectory_WithFileOnlyPath(self):
        source_path = 'baz.yaml'
        try:
            __ = self.path_helper.get_parent_directory(source_path)
            self.fail('Expected get_parent_directory() to fail with an active remote path module and only a file name')
        except:
            pass

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
    #                          get_remote_parent_directory() Tests                             #
    ###########################################################################################

    def testGetRemoteParentDirectory_WithAbsoluteFilePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = 'c:\\foo\\bar'

        actual = self.path_helper.get_remote_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteParentDirectory_WithAbsoluteFilePathAndForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = 'c:/foo/bar'

        actual = self.path_helper.get_remote_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteParentDirectory_WithRelativeFilePath(self):
        source_path = 'bar\\baz.yaml'
        try:
            __ = self.path_helper.get_remote_parent_directory(source_path)
            self.fail('Expected get_remote_parent_directory() to fail with an active remote path module and a relative path')
        except:
            pass

    def testGetRemoteParentDirectory_WithRelativeFilePathAndForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        try:
            __ = self.path_helper.get_remote_parent_directory(source_path)
            self.fail('Expected get_remote_parent_directory() to fail with an active remote path module and a relative path')
        except:
            pass

    def testGetRemoteParentDirectory_WithFileOnlyPath(self):
        source_path = 'baz.yaml'
        try:
            __ = self.path_helper.get_remote_parent_directory(source_path)
            self.fail('Expected get_remote_parent_directory() to fail with an active remote path module and only a file name')
        except:
            pass

    def testGetRemoteParentDirectory_WithEmptyPath(self):
        source_path = ''
        expected = source_path

        actual = self.path_helper.get_remote_parent_directory(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteParentDirectory_WithNullPath(self):
        source_path = None
        expected = source_path

        actual = self.path_helper.get_remote_parent_directory(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               is_absolute_path() Tests                                  #
    ###########################################################################################

    def testIsAbsolutePath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = True

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsolutePath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsolutePath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_absolute_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsolutePath_WithRelativePathWithForwardSlashes(self):
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
    #                            is_absolute_remote_path() Tests                               #
    ###########################################################################################

    def testIsAbsoluteRemotePath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = True

        actual = self.path_helper.is_absolute_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteRemotePath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_absolute_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteRemotePath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_absolute_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteRemotePath_WithRelativePathWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_absolute_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteRemotePath_WithEmptyPath(self):
        source_path = ''
        expected = False

        actual = self.path_helper.is_absolute_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsAbsoluteRemotePath_WithNullPath(self):
        source_path = None
        expected = False

        actual = self.path_helper.is_absolute_remote_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                               is_relative_path() Tests                                  #
    ###########################################################################################

    def testIsRelativePath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativePath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativePath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = True

        actual = self.path_helper.is_relative_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativePath_WithRelativePathWithForwardSlashes(self):
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
    #                            is_relative_remote_path() Tests                               #
    ###########################################################################################

    def testIsRelativeRemotePath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_relative_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeRemotePath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_relative_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeRemotePath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = True

        actual = self.path_helper.is_relative_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeRemotePath_WithRelativePathWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = True

        actual = self.path_helper.is_relative_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeRemotePath_WithEmptyPath(self):
        source_path = ''
        expected = True

        actual = self.path_helper.is_relative_remote_path(source_path)
        self.assertEquals(actual, expected)

    def testIsRelativeRemotePath_WithNullPath(self):
        source_path = None
        expected = True

        actual = self.path_helper.is_relative_remote_path(source_path)
        self.assertEquals(actual, expected)


    ###########################################################################################
    #                            get_filename_from_path() Tests                               #
    ###########################################################################################

    def testGetFilenameFromPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithRelativePathWithForwardSlashes(self):
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
        source_path = 'c:\\foo\\bar\\baz'
        expected = 'baz'

        actual = self.path_helper.get_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameFromPath_WithFileWithNoExtWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz'
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
    #                         get_remote_filename_from_path() Tests                            #
    ###########################################################################################

    def testGetRemoteFilenameFromPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithRelativePathWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = 'baz.yaml'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithFileWithNoExt(self):
        source_path = 'c:\\foo\\bar\\baz'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithFileWithNoExtWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_remote_filename_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                         get_filename_no_ext_from_path() Tests                           #
    ###########################################################################################

    def testGetFilenameNoExtFromPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithRelativePathWithForwardSlashes(self):
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
        source_path =  'c:\\foo\\bar\\baz'
        expected = 'baz'

        actual = self.path_helper.get_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetFilenameNoExtFromPath_WithFileWithNoExtWithForwardSlashes(self):
        source_path =  'c:/foo/bar/baz'
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
    #                      get_remote_filename_no_ext_from_path() Tests                        #
    ###########################################################################################

    def testGetRemoteFilenameNoExtFromPath_WithAbsolutePath(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithAbsolutePathWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithRelativePath(self):
        source_path = 'bar\\baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithRelativePathWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithFileOnly(self):
        source_path = 'baz.yaml'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithFileWithNoExt(self):
        source_path =  'c:\\foo\\bar\\baz'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithFileWithNoExtWithForwardSlashes(self):
        source_path =  'c:/foo/bar/baz'
        expected = 'baz'

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithEmptyPath(self):
        source_path = ''
        expected = None

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    def testGetRemoteFilenameNoExtFromPath_WithNullPath(self):
        source_path = None
        expected = None

        actual = self.path_helper.get_remote_filename_no_ext_from_path(source_path)
        self.assertEquals(actual, expected)

    ###########################################################################################
    #                                   is_jar_file() Tests                                   #
    ###########################################################################################

    def testIsJarFile_WithAbsolutePathToJarFile(self):
        source_path = 'c:\\foo\\bar\\baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithAbsolutePathToJarFileWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithRelativePathToJarFile(self):
        source_path = 'bar\\baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithRelativePathToJarFileWithForwardSlashes(self):
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
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithAbsolutePathToYamlFileWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithRelativePathToYamlFile(self):
        source_path = 'bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithRelativePathToYamlFileWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithJarFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsJarFile_WithYamlFileOnly(self):
        source_path = 'baz.yaml'
        expected = False

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
    #                                is_remote_jar_file() Tests                                #
    ###########################################################################################

    def testIsRemoteJarFile_WithAbsolutePathToJarFile(self):
        source_path = 'c:\\foo\\bar\\baz.jar'
        expected = True

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithAbsolutePathToJarFileWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.jar'
        expected = True

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithRelativePathToJarFile(self):
        source_path = 'bar\\baz.jar'
        expected = True

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithRelativePathToJarFileWithForwardSlashes(self):
        source_path = 'bar/baz.jar'
        expected = True

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithJarFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithAbsolutePathToYamlFile(self):
        source_path = 'c:\\foo\\bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithAbsolutePathToYamlFileWithForwardSlashes(self):
        source_path = 'c:/foo/bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithRelativePathToYamlFile(self):
        source_path = 'bar\\baz.yaml'
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithRelativePathToYamlFileWithForwardSlashes(self):
        source_path = 'bar/baz.yaml'
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithJarFileOnly(self):
        source_path = 'baz.jar'
        expected = True

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithYamlFileOnly(self):
        source_path = 'baz.yaml'
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithEmptyPath(self):
        source_path = ''
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)

    def testIsRemoteJarFile_WithNullPath(self):
        source_path = None
        expected = False

        actual = self.path_helper.is_remote_jar_file(source_path)
        self.assertEquals(actual, expected)
