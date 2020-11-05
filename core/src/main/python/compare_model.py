# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
#
#   This code compares python dictionaries.  It is used to compare the new vs the old version.
#   If the flag -output_dir <directory> is provided, the differences is written as yaml and json
#   diffed_model.json diffed_model.yaml in the directory; the tool output is written as diffed_output_rc.
#
#   If the flag is not provided then all output is written to the standard out.
#
import os
import sets
import sys
import traceback

import java.io.File as JFile
import java.io.FileOutputStream as JFileOutputStream
import java.io.IOException as JIOException
import java.io.PrintWriter as JPrintWriter
from java.lang import System
from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.compare import CompareException
from oracle.weblogic.deploy.exception import ExceptionHelper
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyOrderedDict
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.validate import ValidateException

import oracle.weblogic.deploy.util.TranslateException as TranslateException
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import ALIAS_LIST_TYPES
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.json.json_translator import COMMENT_MATCH
from wlsdeploy.json.json_translator import PythonToJson
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.yaml.yaml_translator import PythonToYaml

VALIDATION_FAIL = 2
PATH_TOKEN = '|'
BLANK_LINE = ""

_program_name = 'compareModel'
_class_name = 'compare_model'
_logger = PlatformLogger('wlsdeploy.compare_model')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH
]

all_changes = []
all_added = []
all_removed = []
compare_msgs = sets.Set()


def __process_args(args):
    """
    Process the command-line arguments.
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    _method_name = '__process_args'

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    argument_map = cla_util.process_args(args, trailing_arg_count=2)

    model_context = ModelContext(_program_name, argument_map)
    model_context.set_ignore_missing_archive_entries(True)
    return model_context


class ModelDiffer:

    def __init__(self, current_dict, past_dict, aliases):
        self.aliases = aliases
        self.final_changed_model = PyOrderedDict()
        self.current_dict = current_dict
        self.past_dict = past_dict
        self.set_current = sets.Set()
        self.set_past = sets.Set()
        if self.current_dict and len(self.current_dict.keys()) > 0:
            for item in self.current_dict.keys():
                self.set_current.add(item)
        if self.past_dict and len(self.past_dict.keys()) > 0:
            for item in self.past_dict.keys():
                self.set_past.add(item)
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        result = sets.Set()
        for o in self.intersect:
            if self.past_dict[o] != self.current_dict[o]:
                result.add(o)
        return result

    def unchanged(self):
        result = sets.Set()
        for o in self.intersect:
            if self.past_dict[o] == self.current_dict[o]:
                result.add(o)
        return result

    # def print_diff(self,s, category):
    #     print category
    #     if len(s) > 0:
    #         print s

    def recursive_changed_detail(self, key, token, root):
        """
        Recursively handle the changed items
        :param key: current key to locate the current dictionary for comparison
        :param token: token is a '|' separated string of the changed item representing the path of the model as it
            traverses down the path (this will be changed in recursive calls)
        :param root: root folder of the changes in the model (never change)
        """
        debug("DEBUG: Entering recursive_changed_detail key=%s token=%s root=%s", key, token, root)

        a = ModelDiffer(self.current_dict[key], self.past_dict[key], self.aliases)
        diff = a.changed()
        added = a.added()
        removed = a.removed()
        saved_token = token

        debug('DEBUG: In recursive changed detail %s', diff)
        debug('DEBUG: In recursive added detail %s', added)
        if len(diff) > 0:
            for o in diff:
                token = saved_token
                # The token is a | separated string that is used to parse and rebuilt the structure later
                debug('DEBUG: in recursive changed detail walking down 1 %s', o)
                token = token + PATH_TOKEN + o
                if a.is_dict(o):
                    debug('DEBUG: in recursive changed detail walking down 2 %s', token)
                    a.recursive_changed_detail(o, token, root)
                    last = token.rfind(PATH_TOKEN)
                    token = root
                else:
                    all_changes.append(token)
                    last = token.rfind(PATH_TOKEN)
                    token = root

        # already out of recursive calls, add all entries from current dictionary
        # resources.JDBCSubsystemResources.* (note it may not have the lower level nodes
        added_token = token
        debug('DEBUG: current added token %s', added_token)
        if len(added) > 0:
            for item in added:
                token = saved_token
                debug('DEBUG: recursive added token %s item %s ', token, item)
                all_added.append(token + PATH_TOKEN + item)

        # We don't really care about this, just put something here is enough
        if len(removed) > 0:
            for item in removed:
                token = saved_token
                debug('DEBUG: removed %s', item)
                all_removed.append(token + PATH_TOKEN + item)
        debug('DEBUG: Exiting recursive_changed_detail')

    def is_dict(self, key):
        """
        Check to see if the ke in the current dictionary is a dictionary.
        :param key: key of the dictionary
        :return: true if it is a dictionary otherwise false
        """
        if self.current_dict.has_key(key) and isinstance(self.current_dict[key], PyOrderedDict):
            return 1
        else:
            return 0

    def calculate_changed_model(self):
        """
        Calculate the changed model.
        """
        _method_name = 'calculate_changed_model'

        # This is the top level of changes only
        #  e.g. from no appDeployments to have appDeployments
        #       from no resources to have resources
        #
        #  changed, added, removed are keys in the dictionary
        #   i.e. resources, domainInfo, appDeployments, topology
        #
        try:
            changed = self.changed()
            added = self.added()
            removed = self.removed()

            #
            #  Call recursive for each key (i.e. appDeployments, topology, resources etc..)
            #
            for s in changed:
                self.recursive_changed_detail(s, s, s)
                self._add_results(all_changes)
                self._add_results(all_added)
                self._add_results(all_removed, True)

            for s in added:
                self.recursive_changed_detail(s, s, s)
                self._add_results(all_changes)
                self._add_results(all_added)

            # Clean up previous delete first
            for x in all_removed:
                all_removed.remove(x)

            # Top level:  e.g. delete all resources, all appDeployments

            for s in removed:
                self.recursive_changed_detail(s, s, s)
                self._add_results(all_removed, True)

        except (KeyError, IndexError), ke:
            _logger.severe('WLSDPLY-05709', str(ke)),
            ex = exception_helper.create_pywlst_exception('WLSDPLY-05709', str(ke))
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        except AliasException, ae:
            _logger.severe('WLSDPLY-05709', ae.getLocalizedMessage(),
                           error=ae, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception(ae.getLocalizedMessage(), error=ae)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    def _parse_change_path(self, path):
        """
        Determine the location and attribute name (if specified) for the specified change path
        :param path: delimited change path, such as "resources|JDBCSystemResource|Generic2|JdbcResource"
        :return: tuple - location for path, attribute name from path or None
        """
        _method_name = '_parse_change_path'

        location = LocationContext()
        attribute_name = None
        name_token_next = False

        path_tokens = path.split(PATH_TOKEN)
        folder_names = self.aliases.get_model_section_top_level_folder_names(path_tokens[0])

        attribute_names = []
        attributes_location = self.aliases.get_model_section_attribute_location(path_tokens[0])
        if attributes_location:
            attribute_names = self.aliases.get_model_attribute_names(attributes_location)

        if path_tokens[0] == KUBERNETES:
            return None, None

        for path_token in path_tokens[1:]:
            if name_token_next:
                token_name = self.aliases.get_name_token(location)
                location.add_name_token(token_name, path_token)
                name_token_next = False
            elif path_token in folder_names:
                location.append_location(path_token)
                folder_names = self.aliases.get_model_subfolder_names(location)
                attribute_names = self.aliases.get_model_attribute_names(location)
                regular_type = not self.aliases.is_artificial_type_folder(location)
                security_type = regular_type and self.aliases.is_security_provider_type(location)
                multiple_type = regular_type and self.aliases.supports_multiple_mbean_instances(location)
                if multiple_type or security_type:
                    name_token_next = True
                else:
                    token_name = self.aliases.get_name_token(location)
                    if not location.get_name_for_token(token_name):
                        location.add_name_token(token_name, "TOKEN")
            elif path_token in attribute_names:
                attribute_name = path_token
                name_token_next = False
            else:
                ex = exception_helper.create_compare_exception('WLSDPLY-05712', path_token, path)
                _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

        return location, attribute_name

    def _add_results(self, change_paths, is_delete=False):
        """
        Update the differences in the final model dictionary with the changes
        :param change_paths: Array of changes in delimited format
        :param is_delete: flag indicating to delete paths
        """
        parent_index = -2
        for change_path in change_paths:
            # change_path is the keys of changes in the piped format, such as:
            # resources|JDBCSystemResource|Generic2|JdbcResource|JDBCConnectionPoolParams|TestConnectionsOnReserve
            location, attribute_name = self._parse_change_path(change_path)
            is_folder_path = attribute_name is None

            if is_delete and not is_folder_path:
                # Skip adding if it is a delete of an attribute
                compare_msgs.add(('WLSDPLY-05701', change_path))
                continue

            # splitted is a tuple containing the next token, and a delimited string of remaining tokens
            splitted = change_path.split(PATH_TOKEN, 1)

            # change_tree will be a nested dictionary containing the change path parent elements.
            # change_tokens is a list of parent tokens in change_tree.
            change_tree = PyOrderedDict()
            change_tokens = []

            while len(splitted) > 1:
                tmp_folder = PyOrderedDict()
                tmp_folder[splitted[0]] = PyOrderedDict()
                if len(change_tree) > 0:
                    # traverse to the leaf folder
                    change_folder = change_tree
                    for token in change_tokens:
                        change_folder = change_folder[token]
                    change_folder[splitted[0]] = PyOrderedDict()
                    change_tokens.append(splitted[0])
                else:
                    change_tree = tmp_folder
                    change_tokens.append(splitted[0])
                splitted = splitted[1].split(PATH_TOKEN, 1)

            # key is the last name in the change path
            key = splitted[0]

            # find the specified folder in the change tree and in the current and previous models
            change_folder = change_tree
            current_folder = self.current_dict
            previous_folder = self.past_dict
            for token in change_tokens:
                change_folder = change_folder[token]
                current_folder = current_folder[token]
                previous_folder = dictionary_utils.get_dictionary_element(previous_folder, token)

            # set the value in the change folder if present.
            # merge new and previous values if relevant.
            # add a comment if the previous value was found.
            if current_folder:
                current_value = current_folder[key]
                previous_value = dictionary_utils.get_element(previous_folder, key)
                change_value, comment = self._get_change_info(current_value, previous_value, location, attribute_name)

                if comment:
                    change_folder[COMMENT_MATCH] = comment
                change_folder[key] = change_value
            else:
                change_folder[key] = None

            # merge the change tree into the final model
            self.merge_dictionaries(self.final_changed_model, change_tree)

            # if it is a deletion then go back and update with '!'

            if is_delete:
                split_delete = change_path.split(PATH_TOKEN)
                # allowable_delete_length = len(allowable_delete.split(PATH_TOKEN))
                split_delete_length = len(split_delete)
                if is_folder_path:
                    app_key = split_delete[split_delete_length - 1]
                    parent_key = split_delete[parent_index]
                    debug("DEBUG: deleting folder %s from the model: key %s ", change_path, app_key)
                    pointer_dict = self.final_changed_model
                    for k_item in split_delete:
                        if k_item == parent_key:
                            break
                        pointer_dict = pointer_dict[k_item]
                    del pointer_dict[parent_key][app_key]
                    # Special handling for deleting all resources in high level
                    if split_delete_length == 2 and app_key != 'WebAppContainer':
                        pointer_dict[parent_key][app_key] = PyOrderedDict()
                        old_keys = self.past_dict[parent_key][app_key].keys()
                        for old_key in old_keys:
                            pointer_dict[parent_key][app_key]['!' + old_key] = PyOrderedDict()
                    else:
                        pointer_dict[parent_key]['!' + app_key] = PyOrderedDict()

    def _get_change_info(self, current_value, previous_value, location, attribute_name):
        """
        Determine the value and comment to put in the change model based on the supplied arguments.
        :param current_value: the current value from the new model
        :param previous_value: the previous value from the old model
        :param location: the location of the value in the model
        :param attribute_name: the name of the attribute, or None if this is a folder path
        :return: a tuple with the change value and comment, either can be None
        """
        change_value = current_value
        comment = None

        if attribute_name and (previous_value is not None):
            attribute_type = self.aliases.get_model_attribute_type(location, attribute_name)
            if attribute_type in ALIAS_LIST_TYPES:
                current_list = alias_utils.create_list(current_value, 'WLSDPLY-08001')
                previous_list = alias_utils.create_list(previous_value, 'WLSDPLY-08000')

                change_list = list(previous_list)
                for item in current_list:
                    if item in previous_list:
                        change_list.remove(item)
                    else:
                        change_list.append(item)
                for item in previous_list:
                    if item not in current_list:
                        change_list.remove(item)
                        change_list.append(model_helper.get_delete_name(item))
                change_value = ','.join(change_list)

                current_text = ','.join(current_list)
                previous_text = ','.join(previous_list)
                comment = attribute_name + ": '" + previous_text + "' -> '" + current_text + "'"
            elif not isinstance(previous_value, dict):
                comment = attribute_name + ": '" + str(previous_value) + "'"

        return change_value, comment

    def merge_dictionaries(self, dictionary, new_dictionary):
        """
         Merge the values from the new dictionary to the existing one.
        :param dictionary: the existing dictionary
        :param new_dictionary: the new dictionary to be merged
        """
        for key in new_dictionary:
            new_value = new_dictionary[key]
            if key not in dictionary:
                dictionary[key] = new_value
            else:
                value = dictionary[key]
                if isinstance(value, PyOrderedDict) and isinstance(new_value, PyOrderedDict):
                    self.merge_dictionaries(value, new_value)
                else:
                    dictionary[key] = new_value

    def get_final_changed_model(self):
        """
        Return the changed model.
        """
        return self.final_changed_model


class ModelFileDiffer:
    """
      This is the main driver for the caller.  It compares two model files whether they are json or yaml format.
    """
    def __init__(self, current_dict, past_dict, model_context, output_dir=None):
        self.current_dict_file = current_dict
        self.past_dict_file = past_dict
        self.output_dir = output_dir
        self.model_context = model_context

    def get_dictionary(self, file):
        """
        Retrieve the python dictionary from file
        :param file:  disk file containing the python dictionary
        :return:  python dictionary
        """
        true = True
        false = False
        fh = open(file, 'r')
        content = fh.read()
        return eval(content)

    def compare(self):
        """
        Do the actual compare of the models.
        :return:  whether the difference is safe for online dynamic update
        """

        _method_name = "compare"
        # arguments have been verified and same extensions

        model_file_name = None

        # validate models first

        try:
            if FileUtils.isYamlFile(JFile(os.path.splitext(self.current_dict_file)[1].lower())):
                model_file_name = self.current_dict_file
                FileToPython(model_file_name, True).parse()
                model_file_name = self.past_dict_file
                FileToPython(model_file_name, True).parse()

            self.model_context.set_validation_method('lax')

            aliases = Aliases(model_context=self.model_context, wlst_mode=WlstModes.OFFLINE,
                              exception_type=ExceptionType.COMPARE)

            validator = Validator(self.model_context, aliases, wlst_mode=WlstModes.OFFLINE)

            variable_map = validator.load_variables(self.model_context.get_variable_file())
            model_file_name = self.current_dict_file

            model_dictionary = cla_helper.merge_model_files(model_file_name, variable_map)

            variables.substitute(model_dictionary, variable_map, self.model_context)

            arg_map = dict()
            arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file_name
            model_context_copy = self.model_context.copy(arg_map)
            val_copy = Validator(model_context_copy, aliases, wlst_mode=WlstModes.OFFLINE)

            # any variables should have been substituted at this point
            return_code = val_copy.validate_in_tool_mode(model_dictionary, variables_file_name=None,
                                                         archive_file_name=None)

            if return_code == Validator.ReturnCode.STOP:
                _logger.severe('WLSDPLY-05705', model_file_name)
                return VALIDATION_FAIL

            current_dict = model_dictionary
            model_file_name = self.past_dict_file

            model_dictionary = cla_helper.merge_model_files(model_file_name, variable_map)
            variables.substitute(model_dictionary, variable_map, self.model_context)

            arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file_name
            model_context_copy = self.model_context.copy(arg_map)
            val_copy = Validator(model_context_copy, aliases, wlst_mode=WlstModes.OFFLINE)
            return_code = val_copy.validate_in_tool_mode(model_dictionary, variables_file_name=None,
                                                         archive_file_name=None)

            if return_code == Validator.ReturnCode.STOP:
                _logger.severe('WLSDPLY-05705', model_file_name)
                return VALIDATION_FAIL
            past_dict = model_dictionary
        except ValidateException, te:
            _logger.severe('WLSDPLY-20009', _program_name, model_file_name, te.getLocalizedMessage(),
                           error=te, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception(te.getLocalizedMessage(), error=te)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            return VALIDATION_FAIL
        except VariableException, ve:
            _logger.severe('WLSDPLY-20009', _program_name, model_file_name, ve.getLocalizedMessage(),
                           error=ve, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception(ve.getLocalizedMessage(), error=ve)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            return VALIDATION_FAIL
        except TranslateException, pe:
            _logger.severe('WLSDPLY-20009', _program_name, model_file_name, pe.getLocalizedMessage(),
                           error=pe, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception(pe.getLocalizedMessage(), error=pe)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            return VALIDATION_FAIL

        obj = ModelDiffer(current_dict, past_dict, aliases)
        obj.calculate_changed_model()
        net_diff = obj.get_final_changed_model()

        print BLANK_LINE
        print format_message('WLSDPLY-05706', self.current_dict_file, self.past_dict_file)
        print BLANK_LINE
        if len(net_diff.keys()) == 0:
            print format_message('WLSDPLY-05710')
            print BLANK_LINE
            return 0

        if self.output_dir:
            fos = None
            writer = None
            file_name = None
            try:
                print format_message('WLSDPLY-05711', self.output_dir)
                print BLANK_LINE
                file_name = self.output_dir + '/diffed_model.json'
                fos = JFileOutputStream(file_name, False)
                writer = JPrintWriter(fos, True)
                json_object = PythonToJson(net_diff)
                json_object._write_dictionary_to_json_file(net_diff, writer)
                writer.close()
                file_name = self.output_dir + '/diffed_model.yaml'
                fos = JFileOutputStream(file_name, False)
                writer = JPrintWriter(fos, True)
                pty = PythonToYaml(net_diff)
                pty._write_dictionary_to_yaml_file(net_diff, writer)
                writer.close()
            except JIOException, ioe:
                if fos:
                    fos.close()
                if writer:
                    writer.close()
                _logger.severe('WLSDPLY-05708', file_name, ioe.getLocalizedMessage(),
                               error=ioe, class_name=_class_name, method_name=_method_name)
                return 2
        else:
            print format_message('WLSDPLY-05707')
            print BLANK_LINE
            pty = PythonToYaml(net_diff)
            pty._write_dictionary_to_yaml_file(net_diff, System.out)

        return 0

    def get_compare_msgs(self):
        """
        Return any warning or info messages.
        :return: Set of warning or info messages
        """
        return compare_msgs


def debug(format_string, *arguments):
    """
    Generic debug code.
    :param format_string:  python formatted string
    :param arguments: arguments for the formatted string
    """
    if os.environ.has_key('DEBUG_COMPARE_MODEL_TOOL'):
        print format_string % (arguments)
    else:
        _logger.finest(format_string, arguments)


def main():
    """
    The main entry point for the discoverDomain tool.
    :param args: the command-line arguments
    """
    _method_name = 'main'

    _logger.entering(class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(sys.argv):
        _logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    _outputdir = None

    try:
        model_context = __process_args(sys.argv)
        _outputdir = model_context.get_output_dir()
        model1 = model_context.get_trailing_argument(0)
        model2 = model_context.get_trailing_argument(1)

        for f in [model1, model2]:
            if not os.path.exists(f):
                raise CLAException("Model %s does not exists" % f)
            if os.path.isdir(f):
                raise CLAException("Model %s is a directory" % f)

        model1_file = JFile(model1)
        model2_file = JFile(model2)

        if not (FileUtils.isYamlFile(model1_file) or FileUtils.isJsonFile(model1_file)):
            raise CLAException("Model extension must be either yaml or json")

        if not (FileUtils.isYamlFile(model1_file) and FileUtils.isYamlFile(model2_file)
                or FileUtils.isJsonFile(model1_file) and FileUtils.isJsonFile(model2_file)):
            ext = os.path.splitext(model1)[1]
            raise CLAException("Model %s is not a %s file " % (model2, ext))

        obj = ModelFileDiffer(model1, model2, model_context, _outputdir)
        rc = obj.compare()
        if rc == VALIDATION_FAIL:
            System.exit(2)

        if _outputdir:
            fos = None
            writer = None
            file_name = None
            if len(compare_msgs) > 0:
                try:
                    file_name = _outputdir + '/compare_model_stdout'
                    fos = JFileOutputStream(file_name, False)
                    writer = JPrintWriter(fos, True)
                    writer.println(BLANK_LINE)
                    writer.println(BLANK_LINE)
                    index = 1
                    for line in compare_msgs:
                        msg_key = line[0]
                        msg_value = line[1]
                        writer.println("%s. %s" % (index, format_message(msg_key,msg_value.replace(PATH_TOKEN, "-->"))))
                        index = index + 1
                        writer.println(BLANK_LINE)
                    fos.close()
                    writer.close()
                except JIOException, ioe:
                    if fos:
                        fos.close()
                    if writer:
                        writer.close()
                    _logger.severe('WLSDPLY-05708', file_name, ioe.getLocalizedMessage(),
                                   error=ioe, class_name=_class_name, method_name=_method_name)
        else:
            if len(compare_msgs) > 0:
                print BLANK_LINE
                print BLANK_LINE
                index = 1
                for line in compare_msgs:
                    msg_key = line[0]
                    msg_value = line[1]
                    print "%s. %s" % (index, format_message(msg_key,msg_value.replace(PATH_TOKEN, "-->")))
                    index = index + 1
                    print BLANK_LINE

        System.exit(0)

    except CLAException, ex:
        exit_code = 2
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            _logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                           class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        sys.exit(exit_code)
    except CompareException, ce:
        cla_helper.clean_up_temp_files()
        _logger.severe('WLSDPLY-05704', ce.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
        System.exit(2)
    except PyWLSTException, pe:
        cla_helper.clean_up_temp_files()
        _logger.severe('WLSDPLY-05704', pe.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
        System.exit(2)
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        eeString = traceback.format_exception(exc_type, exc_obj, exc_tb)
        cla_helper.clean_up_temp_files()
        _logger.severe('WLSDPLY-05704', eeString)
        System.exit(2)


def format_message(key, *args):
    """
    Get message using the bundle.
    :param key: bundle key
    :param args: bundle arguments
    :return:
    """
    return ExceptionHelper.getMessage(key, list(args))


if __name__ == "__main__":
    main()
