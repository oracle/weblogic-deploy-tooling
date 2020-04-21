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
#

import sets
import sys, os, traceback
from java.lang import System
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.yaml.yaml_translator import PythonToYaml
from wlsdeploy.json.json_translator import PythonToJson
from oracle.weblogic.deploy.util import CLAException
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.tool.validate.validator import Validator
from oracle.weblogic.deploy.validate import ValidateException
from wlsdeploy.exception.expection_types import ExceptionType
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.exception import ExceptionHelper
import java.io.FileOutputStream as JFileOutputStream
import java.io.IOException as JIOException
import java.io.PrintWriter as JPrintWriter
import oracle.weblogic.deploy.util.TranslateException as TranslateException

VALIDATION_FAIL=-1
PATH_TOKEN='|'
BLANK_LINE=""

_program_name = 'compareModel'
_class_name = 'model_diff'
__logger = PlatformLogger('wlsdeploy.model_diff')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.COMPARE_MODEL_OUTPUT_DIR_SWITCH,
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
    required_arg_map, optional_arg_map = cla_util.process_args(args, trailing_arg_count=2)

    cla_helper.verify_required_args_present(_program_name, __required_arguments, required_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)
    return ModelContext(_program_name, combined_arg_map)

class ModelDiffer:

    def __init__(self, current_dict, past_dict):

        self.final_changed_model=dict()
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

    def print_diff(self,s, category):
        print category
        if len(s) > 0:
            print s

    def recursive_changed_detail(self, key, token, root):
        debug("DEBUG: Entering recursive_changed_detail key=%s token=%s root=%s", key, token, root)

        a=ModelDiffer(self.current_dict[key], self.past_dict[key])
        diff=a.changed()
        added=a.added()
        removed=a.removed()
        saved_token=token

        debug('DEBUG: In recursive changed detail %s', diff)
        debug('DEBUG: In recursive added detail %s', added)
        if len(diff) > 0:
            for o in diff:
                token=saved_token
                # The token is a | separated string that is used to parse and rebuilt the structure later
                debug('DEBUG: in recursive changed detail walking down 1 %s', o)
                token=token+PATH_TOKEN+o
                if a.is_dict(o):
                    debug('DEBUG: in recursive changed detail walking down 2 %s', token)
                    a.recursive_changed_detail(o,token, root)
                    last=token.rfind(PATH_TOKEN)
                    token=root
                else:
                    all_changes.append(token)
                    last=token.rfind(PATH_TOKEN)
                    token=root


        # already out of recursive calls, add all entries from current dictionary
        # resources.JDBCSubsystemResources.* (note it may not have the lower level nodes
        added_token=token
        debug('DEBUG: current added token %s' , added_token)
        if len(added) > 0:
            for item in added:
                token=saved_token
                debug('DEBUG: recursive added token %s item %s ', token, item)
                all_added.append(token + PATH_TOKEN + item)

        # We don't really care about this, just put something here is enough
        if len(removed) > 0:
            for item in removed:
                token=saved_token
                debug('DEBUG: removed %s', item)
                all_removed.append(token + PATH_TOKEN + item)
        debug('DEBUG: Exiting recursive_changed_detail')

    def is_dict(self,key):
        if isinstance(self.current_dict[key],dict):
            return 1
        else:
            return 0

    def calculate_changed_model(self):
        """
        Calculate the changed model.
        """

        # This is the top level of changes only
        #  e.g. from no appDeployments to have appDeployments
        #       from no resources to have resources
        #
        #  changed, added, removed are keys in the dictionary
        #   i.e. resources, domainInfo, appDeployments, topology
        #
        changed = self.changed()
        added = self.added()
        removed = self.removed()

        #
        #  Call recursive for each key
        #
        for s in changed:
            token=s
            self.recursive_changed_detail(s, token, s)
            self._add_results(all_changes)
            self._add_results(all_added)
            self._add_results(all_removed, True)

        for s in added:
            token=s
            self.recursive_changed_detail(s, token, s)
            self._add_results(all_changes)
            self._add_results(all_added)
            # Should not have delete

        # Clean up previous delete first
        for x in all_removed:
            all_removed.remove(x)

        # Top level:  e.g. delete all resources, all appDeployments

        for s in removed:
            token = s
            self.recursive_changed_detail(s,token, s)
            self._add_results(all_removed, True)

    def _is_alias_folder(self, path):
        """
        Check if the delimited path is a folder or attribute
        :param path: '|' delimited path
        :return: true if it is a folder otherwise false
        """
        debug("DEBUG: Entering is_alias_folder %s", path)
        path_tokens = path.split(PATH_TOKEN)
        model_context = ModelContext("test", { })
        aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE)
        location = LocationContext()
        last_token = path_tokens[-1]
        alias_helper = AliasHelper(aliases, __logger, ExceptionType.COMPARE)

        found = True
        name_token_next = False
        for path_token in path_tokens[1:]:
            if name_token_next:
                token_name = aliases.get_name_token(location)
                location.add_name_token(token_name, path_token)
                name_token_next = False
            else:
                location.append_location(path_token)
                if last_token == path_token:
                    break
                name_token_next = alias_helper.supports_multiple_mbean_instances(location)
            attrib_names = alias_helper.get_model_attribute_names(location)
            if last_token in attrib_names:
                found = False

        debug("DEBUG: is_alias_folder %s %s", path, found)

        return found

    def _add_results(self, ar_changes, is_delete=False):
        """
        Update the differences in the final model dictionary with the changes
        :param ar_changes:   Array of changes in delimited format
        """
        # The ar_changes is the keys of changes in the piped format
        #  'resources|JDBCSystemResource|Generic2|JdbcResource|JDBCConnectionPoolParams|TestConnectionsOnReserve
        #

        for item in ar_changes:
            if is_delete:
                # Skipp adding if it is a delete of an attribute
                found_in_allowable_delete = self._is_alias_folder(item)
                if not found_in_allowable_delete:
                    compare_msgs.add(('WLSDPLY-05701',item))
                    continue

            splitted=item.split(PATH_TOKEN,1)
            n=len(splitted)
            result=dict()
            walked=[]

            while n > 1:
                tmp=dict()
                tmp[splitted[0]]=dict()
                if len(result) > 0:
                    # traverse to the leaf
                    leaf=result
                    for k in walked:
                        leaf = leaf[k]
                    leaf[splitted[0]]=dict()
                    walked.append(splitted[0])
                else:
                    result=tmp
                    walked.append(splitted[0])
                splitted=splitted[1].split(PATH_TOKEN,1)
                n=len(splitted)
            #
            # result is the dictionary format
            #
            leaf=result
            value_tree=self.current_dict
            for k in walked:
                leaf = leaf[k]
                value_tree=value_tree[k]
            #
            # walk the current dictionary and set the value
            #
            if value_tree:
                leaf[splitted[0]] = value_tree[splitted[0]]
            else:
                leaf[splitted[0]] = None

            self.merge_dictionaries(self.final_changed_model, result)

            # if it is a deletion then go back and update with '!'

            if is_delete:
                is_folder_path = self._is_alias_folder(item)
                split_delete = item.split(PATH_TOKEN)
                #allowable_delete_length = len(allowable_delete.split(PATH_TOKEN))
                split_delete_length = len(split_delete)
                if is_folder_path:
                    app_key = split_delete[split_delete_length - 1]
                    parent_key = split_delete[-2]
                    debug("DEBUG: deleting folder %s from the model: key %s ", item, app_key)
                    pointer_dict = self.final_changed_model
                    for k_item in split_delete:
                        if k_item == parent_key:
                            break
                        pointer_dict = pointer_dict[k_item]
                    del pointer_dict[parent_key][app_key]
                    # Special handling for deleting all resources in high level
                    if split_delete_length == 2 and app_key != 'WebAppContainer':
                        pointer_dict[parent_key][app_key] = dict()
                        old_keys = self.past_dict[parent_key][app_key].keys()
                        for old_key in old_keys:
                            pointer_dict[parent_key][app_key]['!' + old_key] = dict()
                    else:
                        pointer_dict[parent_key]['!' + app_key] = dict()


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
                if isinstance(value, dict) and isinstance(new_value, dict):
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
            if os.path.splitext(self.current_dict_file)[1].lower() == ".yaml":
                model_file_name = self.current_dict_file
                FileToPython(model_file_name, True).parse()
                model_file_name = self.past_dict_file
                FileToPython(model_file_name, True).parse()


            aliases = Aliases(model_context=self.model_context, wlst_mode=WlstModes.OFFLINE)

            validator = Validator(self.model_context, aliases, wlst_mode=WlstModes.OFFLINE)

            variable_map = validator.load_variables(self.model_context.get_variable_file())
            model_file_name = self.current_dict_file

            model_dictionary = cla_helper.merge_model_files(model_file_name, variable_map)

            variables.substitute(model_dictionary, variable_map, self.model_context)

            return_code = validator.validate_in_tool_mode(model_dictionary,
                                                      variables_file_name=None,
                                                      archive_file_name=None)

            if return_code == Validator.ReturnCode.STOP:
                __logger.severe('WLSDPLY-05705', model_file_name)
                return VALIDATION_FAIL

            current_dict = model_dictionary
            model_file_name = self.past_dict_file

            model_dictionary = cla_helper.merge_model_files(model_file_name, variable_map)
            variables.substitute(model_dictionary, variable_map, self.model_context)

            return_code = validator.validate_in_tool_mode(model_dictionary,
                                            variables_file_name=None,
                                            archive_file_name=None)

            if return_code == Validator.ReturnCode.STOP:
                __logger.severe('WLSDPLY-05705', model_file_name)
                return VALIDATION_FAIL
            past_dict = model_dictionary
        except ValidateException, te:
            __logger.severe('WLSDPLY-20009', _program_name, model_file_name, te.getLocalizedMessage(),
                            error=te, class_name=_class_name, method_name=_method_name)
            return VALIDATION_FAIL
        except VariableException, ve:
            __logger.severe('WLSDPLY-20009', _program_name, model_file_name, ve.getLocalizedMessage(),
                            error=ve, class_name=_class_name, method_name=_method_name)
            return VALIDATION_FAIL
        except TranslateException, pe:
            __logger.severe('WLSDPLY-20009', _program_name, model_file_name, pe.getLocalizedMessage(),
                            error=pe, class_name=_class_name, method_name=_method_name)
            return VALIDATION_FAIL



        obj = ModelDiffer(current_dict, past_dict)
        obj.calculate_changed_model()
        net_diff = obj.get_final_changed_model()
        if self.output_dir:
            fos = None
            writer = None
            file_name = None
            try:
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
                __logger.severe('WLSDPLY-05708', file_name, ioe.getLocalizedMessage(),
                                error=ioe, class_name=_class_name, method_name=_method_name)
                return -1
        else:
            print BLANK_LINE
            print format_message('WLSDPLY-05706', self.current_dict_file, self.past_dict_file)
            print BLANK_LINE
            print format_message('WLSDPLY-05707')
            print BLANK_LINE

            pty = PythonToYaml(net_diff)
            pty._write_dictionary_to_yaml_file(net_diff, System.out)

        return 0

def debug(format_string, *arguments):
    """
      Generic debug code
    :param format_string:  python formatted string
    :param arguments:
    """
    if os.environ.has_key('DEBUG_COMPARE_MODEL_TOOL'):
        print format_string % (arguments)
    else:
        __logger.finest(format_string, arguments)

def main():
    """
    The main entry point for the discoverDomain tool.
    :param args: the command-line arguments
    """
    _method_name = 'main'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(sys.argv):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    _outputdir = None

    try:
        model_context = __process_args(sys.argv)
        _outputdir = model_context.get_compare_model_output_dir()
        model1 = model_context.get_trailing_argument(0)
        model2 = model_context.get_trailing_argument(1)

        for f in [ model1, model2 ]:
            if not os.path.exists(f):
                raise CLAException("Model %s does not exists" % f)
            if os.path.isdir(f):
                raise CLAException("Model %s is a directory" % f)

        model1_ext = os.path.splitext(model1)[1]
        model2_ext = os.path.splitext(model2)[1]

        validated = False
        for ext in [ '.yaml', '.json' ]:
            if model1_ext.lower() == ext:
                if model2_ext.lower() != model1_ext.lower():
                    raise CLAException("Model %s is not a %s file " % model2, ext)
                else:
                    validated = True
                    break

        if not validated:
            raise CLAException("Model extension must be either yaml or json")

        obj = ModelFileDiffer(model1, model2, model_context, _outputdir)
        rc = obj.compare()
        if rc == VALIDATION_FAIL:
            System.exit(-1)

        if _outputdir:
            fos = None
            writer = None
            file_name = None
            if len(compare_msgs) > 0:
                try:
                    file_name = _outputdir + '/model_diff_stdout'
                    fos = JFileOutputStream(file_name, False)
                    writer = JPrintWriter(fos, True)
                    writer.println(BLANK_LINE)
                    writer.println(BLANK_LINE)
                    index = 1
                    for line in compare_msgs:
                        msg_key = line[0]
                        msg_value = line[1]
                        writer.println( "%s. %s" % (index, format_message(msg_key,msg_value.replace(PATH_TOKEN, "-->"))))
                        index = index + 1
                        writer.println(BLANK_LINE)
                    fos.close()
                    writer.close()
                except JIOException, ioe:
                    if fos:
                        fos.close()
                    if writer:
                        writer.close()
                    __logger.severe('WLSDPLY-05708', file_name, ioe.getLocalizedMessage(),
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
        exit_code = -1
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        sys.exit(exit_code)
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        eeString = traceback.format_exception(exc_type, exc_obj, exc_tb)
        cla_helper.clean_up_temp_files()
        __logger.severe('WLSDPLY-05704', eeString)
        System.exit(-1)

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


