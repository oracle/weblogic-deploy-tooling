"""
Copyright (c) 2023, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that handles OS-specifics for SSH.
"""
import re

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper

__logger = PlatformLogger('wlsdeploy.util')

class SSHCommandLineHelper(object):
    __class_name = 'SSHCommandLineHelper'

    def __init__(self, is_windows):
        self._is_windows = is_windows

    def _filter_directory_contents(self, dir_name, contents_dict, files_only, file_pattern_to_match):
        results = list()
        path_separator = '/'
        if self._is_windows:
            path_separator = '\\'
        for key, value in contents_dict.iteritems():
            if value is None or (isinstance(value, dict) and not files_only):
                if isinstance(file_pattern_to_match, (str, unicode)) and len(file_pattern_to_match) > 0:
                    regex = re.compile(file_pattern_to_match, re.IGNORECASE)
                    if regex.match(key) is None:
                        continue
                entry = '%s%s' % (dir_name, key)
                if isinstance(value, dict) and not entry.endswith(path_separator):
                    entry += path_separator
                results.append(entry)
        return results


class SSHWindowsCommandLineHelper(SSHCommandLineHelper):
    __class_name = 'SSHWindowsCommandLineHelper'
    __directory_line_regex = re.compile(r'^\s*Directory of (.+)$')
    __directory_entry_regex = re.compile(r'^[0-9\-\/]{6,10}\s+[0-9:]{3,5}(?:\sAM|PM)?\s+([0-9,.]+|<DIR>)\s+(.+)\s*$')
    __dir_marker = '<DIR>'

    def __init__(self):
        """
        Constructor for Windows command-line helper
        """
        SSHCommandLineHelper.__init__(self, True)

    def get_remove_dir_command(self, file_or_dir_path):
        path = file_or_dir_path.replace('/', '\\')
        # Use the rd abbreviation to avoid picking up the rmdir Unix utility that might be installed.
        command = 'rd /S /Q %s' % file_or_dir_path
        return command

    def get_remove_file_command(self, file_or_dir_path):
        path = file_or_dir_path.replace('/', '\\')
        # Use the rd abbreviation to avoid picking up the rmdir Unix utility that might be installed.
        command = 'del /F /Q %s' % file_or_dir_path
        return command

    def get_remove_command(self, path):
        return None

    def get_mkdirs_command(self, directory_path):
        path = self._get_directory_path(directory_path)
        command = 'if not exist "%s" md "%s"' % (path, path)
        return command

    def get_does_directory_exist_command(self, directory_path):
        return self.get_directory_contents_command(directory_path)

    def get_directory_contents_command(self, directory_path):
        path = self._get_directory_path(directory_path)
        command = 'dir %s' % path
        return command

    def get_directory_contents(self, output_lines, files_only, pattern_to_match=None):
        dir_name, contents_dict = self._parse_directory_listing_output(output_lines)
        result_list = self._filter_directory_contents(dir_name, contents_dict, files_only, pattern_to_match)
        return result_list

    def _get_directory_path(self, directory_path):
        path = directory_path.replace('/', '\\')
        if not path.endswith('\\'):
            path = '%s\\' % path
        return path

    def _parse_directory_listing_output(self, output_lines):
        contents_dict = dict()
        current_directory_name = None
        found_directory_line = False
        expecting_empty_line = False
        for output_line in output_lines:
            if expecting_empty_line:
                expecting_empty_line = False
                continue

            if found_directory_line:
                matcher = self.__directory_entry_regex.match(output_line)
                if matcher is not None:
                    size_or_dir = matcher.group(1)
                    name = matcher.group(2)

                    if size_or_dir == self.__dir_marker:
                        # Always skip over . and .. directory entries
                        if name != '.' and name != '..':
                            contents_dict[name] = dict()
                    else:
                        contents_dict[name] = None
                else:
                    # Once we start processing directory entries, all the lines should
                    # match finish processing the entries.  As such, bail out once the
                    # output_line doesn't match an entry.
                    break
            else:
                matcher = self.__directory_line_regex.match(output_line)
                if matcher is not None:
                    dir_name = matcher.group(1)
                    current_directory_name = self._get_directory_path(dir_name)
                    found_directory_line = True
                    # Next line should be empty
                    expecting_empty_line = True
        return current_directory_name, contents_dict

    def get_environment_variable_command(self, env_var_name):
        return str_helper.to_string('echo %s' % self._format_environment_variable_deference(env_var_name))

    def get_environment_variable_value(self, output_lines, env_var_name):
        env_var_value_when_not_set = self._format_environment_variable_deference(env_var_name)
        result = None
        for output_line in output_lines:
            line = output_line.strip()
            if line == env_var_value_when_not_set:
                result = None
                break
            elif not string_utils.is_empty(line):
                result = line
                break
        return result

    def _format_environment_variable_deference(self, env_var_name):
        return str_helper.to_string('%') + str_helper.to_string(env_var_name) + str_helper.to_string('%')


class SSHUnixCommandLineHelper(SSHCommandLineHelper):
    __class_name = 'SSHUnixCommandLineHelper'

    def __init__(self):
        """
        Constructor for non-Windows command-line helper
        """
        SSHCommandLineHelper.__init__(self, False)

    def get_remove_command(self, file_or_dir_path):
        command = 'rm -rf %s' % file_or_dir_path
        return command

    def get_remove_dir_command(self, file_or_dir_path):
        return self.get_remove_command(file_or_dir_path)

    def get_remove_file_command(self, file_or_dir_path):
        return self.get_remove_command(file_or_dir_path)

    def get_mkdirs_command(self, directory_path):
        path = self._get_directory_path(directory_path)
        command = 'mkdir -p %s' % path
        return command

    def get_does_directory_exist_command(self, directory_path):
        path = directory_path
        if not path.endswith('/'):
            path = '%s/' % path
        command = 'ls %s' % path
        return command

    def get_directory_contents_command(self, directory_path):
        path = self._get_directory_path(directory_path)
        # We need the first line of the output to be the path since ls doesn't return the directory path
        command = 'echo "%s"; ls -p %s | cat' % (path, path)
        return command

    def get_directory_contents(self, output_lines, files_only, pattern_to_match=None):
        dir_name, contents_dict = self._parse_directory_listing_output(output_lines)
        result_list = self._filter_directory_contents(dir_name, contents_dict, files_only, pattern_to_match)
        return result_list

    def _get_directory_path(self, directory_path):
        path = directory_path
        if not path.endswith('/'):
            path = '%s/' % path
        return path

    def _parse_directory_listing_output(self, output_lines):
        contents_dict = dict()
        current_directory_name = None
        found_directory_line = False
        for output_line in output_lines:
            if found_directory_line:
                name = output_line.strip()
                if len(name) > 0:
                    if name.endswith('/'):
                        contents_dict[name] = dict()
                    else:
                        contents_dict[name] = None
            else:
                current_directory_name = output_line.strip()
                found_directory_line = True

        return current_directory_name, contents_dict

    def get_environment_variable_command(self, env_var_name):
        return str_helper.to_string('echo ${%s}' % env_var_name)

    def get_environment_variable_value(self, output_lines, _):
        result = None
        for output_line in output_lines:
            line = output_line.strip()
            if not string_utils.is_empty(line):
                result = line
                break
        return result
