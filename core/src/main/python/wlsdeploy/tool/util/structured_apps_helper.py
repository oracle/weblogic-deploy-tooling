"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging import platform_logger

_class_name = 'structured_app_helper'
_logger = platform_logger.PlatformLogger('wlsdeploy.util')

def get_structured_app_install_root(app_name, abs_source_path, abs_combined_plan_path, exception_type):
    """
    Using the absolute paths for an application's SourcePath and combined PlanDir and PlanPath,
    determine the structured application's install root directory.  The caller MUST ensure that
    the paths are not empty and are absolute paths!

    :param app_name: the name of the application
    :param abs_source_path: the absolute path for the SourcePath
    :param abs_combined_plan_path: the absolute path for the effective PlanPath
    :param exception_type: the type of exception to raise if an error occurs
    :return: the structured application's install root, or None if this is not a structured application
    """
    _method_name = 'get_structured_app_install_root'
    _logger.entering(app_name, abs_source_path, abs_combined_plan_path, exception_type,
                     class_name=_class_name, method_name=_method_name)

    install_root = None
    mutated_source_path = abs_source_path.replace('\\', '/')
    mutated_plan_path = abs_combined_plan_path.replace('\\', '/')

    #
    # This is tricky because the format is:
    #   - <path-to-install-root>/[optional-version-dir]/app/<archive-file | exploded directory>
    #   - <path-to-install-root>/[optional-version-dir]/<plan-dir>/<deploy-plan-file>
    #
    # Find the first element in both paths that do not match.  If the first non-matching element in
    # the source_path is 'app' and the first non-matching element in plan_path is a directory and
    # there is only one additional element after that (i.e., plan.xml), we have a structured application.
    #
    # If it is a structured application, then we only need to try to guess if the optional version directory
    # is present or not.  There is no definitive way to determine this so do the best that we can...
    #
    source_path_elements = mutated_source_path.split('/')
    plan_path_elements = mutated_plan_path.split('/')

    if len(source_path_elements) <= len(plan_path_elements):
        max_len = len(source_path_elements)
    else:
        max_len = len(plan_path_elements)

    index = 0
    while index < max_len:
        if source_path_elements[index] != plan_path_elements[index]:
            break
        index += 1

    # If this is a structured app, the index should point to the app and plan subdirectories
    # in their respective lists.  If the source path element is 'app' and the plan path
    # only has the plan dir and plan file elements remaining, then this looks like a
    # structured application so determine the path to the install root.

    if source_path_elements[index] == 'app' and len(plan_path_elements) == index + 2:
        source_path_elements = source_path_elements[0:index]
        mutated_install_root = \
            _choose_install_root(app_name, abs_source_path, abs_combined_plan_path, source_path_elements, exception_type)
        install_root = abs_source_path[0:len(mutated_install_root)]

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=install_root)
    return install_root


def _choose_install_root(app_name, source_path, plan_path, remaining_source_path_elements, exception_type):
    _method_name = '_choose_install_root'
    _logger.entering(app_name, source_path, plan_path, remaining_source_path_elements, exception_type,
                     class_name=_class_name, method_name=_method_name)

    # For posix-style paths, the first element is an empty string.
    # For windows-style paths, the first element is typically the drive letter followed by a colon.
    #
    number_of_elements = len(remaining_source_path_elements)
    if  number_of_elements > 2:
        # strip off any version qualifier from the app_name
        bare_app_name = app_name.split('#')[0].lower()
        optional_version_dir_name = remaining_source_path_elements[number_of_elements - 1]
        possible_install_root_name = remaining_source_path_elements[number_of_elements - 2]

        if bare_app_name in optional_version_dir_name.lower():
            mutated_install_root = '/'.join(remaining_source_path_elements)
        elif bare_app_name in possible_install_root_name.lower():
            mutated_install_root = '/'.join(remaining_source_path_elements[0:-1])
        else:
            # At this point, the best that we can do it guess...
            #
            # 1. Check for special characters like -, #, @, and .
            # 2. Check for digits
            #
            optional_version_dir_chars = _get_string_character_counts(optional_version_dir_name)
            possible_install_root_chars = _get_string_character_counts(possible_install_root_name)

            optional_specials = optional_version_dir_chars['#'] + optional_version_dir_chars['@'] + \
                                optional_version_dir_chars['-'] + optional_version_dir_chars['.']
            possible_specials = possible_install_root_chars['#'] + possible_install_root_chars['@'] + \
                                possible_install_root_chars['-'] + possible_install_root_chars['.']

            if optional_version_dir_chars['digits'] > possible_install_root_chars['digits'] or \
                    optional_specials > possible_specials:
                # Optional version directory has either more digits or special characters
                # so treat the optional version directory as the version directory and
                # choose the possible install root directory.
                mutated_install_root = '/'.join(remaining_source_path_elements[0:-1])
            else:
                # Otherwise, treat the optional version directory as the install root directory
                mutated_install_root = '/'.join(remaining_source_path_elements)
    elif number_of_elements > 1:
        mutated_install_root = '/'.join(remaining_source_path_elements)
    else:
        ex = exception_helper.create_exception(exception_type,'WLSDPLY-02200',
                                               app_name, source_path, plan_path, number_of_elements)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=mutated_install_root)
    return mutated_install_root

def _get_string_character_counts(value):
    _method_name = '_get_string_character_counts'
    _logger.entering(value, class_name=_class_name, method_name=_method_name)

    result = {'digits': 0, 'letters': 0, '#': 0, '@': 0, '-': 0, '.': 0}
    for c in value:
        if c.isalpha():
            result['letters'] += 1
        elif c.isdigit():
            result['digits'] += 1
        elif c == '#':
            result['#'] += 1
        elif c == '@':
            result['@'] += 1
        elif c == '-':
            result['-'] += 1
        elif c == '.':
            result['.'] += 1


    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result
