# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
from oracle.weblogic.deploy.compare import CompareException
from oracle.weblogic.deploy.exception import ExceptionHelper
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.validate import ValidateException
from oracle.weblogic.deploy.yaml import YamlException

import oracle.weblogic.deploy.util.TranslateException as TranslateException
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.json.json_translator import PythonToJson
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.compare.model_comparer import ModelComparer
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util import validate_configuration
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.yaml.yaml_translator import PythonToYaml

PATH_TOKEN = '|'
BLANK_LINE = ""

_program_name = 'compareModel'
_class_name = 'compare_model'
__logger = PlatformLogger('wlsdeploy.compare_model')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments.
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    argument_map = cla_util.process_args(args, trailing_arg_count=2)

    return ModelContext(_program_name, argument_map)


class ModelFileDiffer:
    """
      This is the main driver for the caller.  It compares two model files whether they are json or yaml format.
    """
    def __init__(self, current_dict, past_dict, model_context, output_dir=None):
        self.current_dict_file = current_dict
        self.past_dict_file = past_dict
        self.output_dir = output_dir
        self.model_context = model_context
        self.compare_msgs = sets.Set()

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

            # allow unresolved tokens and archive entries
            self.model_context.set_validation_method(validate_configuration.LAX_METHOD)

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
                __logger.severe('WLSDPLY-05705', model_file_name)
                ex = exception_helper.create_compare_exception('WLSDPLY-05705', model_file_name)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

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
                __logger.severe('WLSDPLY-05705', model_file_name, class_name=_class_name, method_name=_method_name)
                ex = exception_helper.create_compare_exception('WLSDPLY-05705', model_file_name)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            past_dict = model_dictionary
        except ValidateException, te:
            __logger.severe('WLSDPLY-20009', _program_name, model_file_name, te.getLocalizedMessage(),
                            error=te, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception('WLSDPLY-20009', _program_name, model_file_name,
                                                           te.getLocalizedMessage(), error=te)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        except VariableException, ve:
            __logger.severe('WLSDPLY-20009', _program_name, model_file_name, ve.getLocalizedMessage(),
                            error=ve, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception('WLSDPLY-20009', _program_name, model_file_name,
                                                           ve.getLocalizedMessage(), error=ve)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        except TranslateException, pe:
            __logger.severe('WLSDPLY-20009', _program_name, model_file_name, pe.getLocalizedMessage(),
                            error=pe, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_compare_exception('WLSDPLY-20009', _program_name, model_file_name,
                                                           pe.getLocalizedMessage(), error=pe)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        comparer = ModelComparer(current_dict, past_dict, aliases, self.compare_msgs)
        change_model = comparer.compare_models()

        print(BLANK_LINE)
        print(format_message('WLSDPLY-05706', self.current_dict_file, self.past_dict_file))
        print(BLANK_LINE)
        if len(change_model.keys()) == 0:
            print(format_message('WLSDPLY-05710'))
            print(BLANK_LINE)
            return 0

        if self.output_dir:
            file_name = None
            try:
                print(format_message('WLSDPLY-05711', self.output_dir))
                print(BLANK_LINE)

                # write the change model as a JSON file
                file_name = self.output_dir + '/diffed_model.json'
                json_object = PythonToJson(change_model)
                json_object.write_to_json_file(file_name)

                # write the change model as a YAML file
                file_name = self.output_dir + '/diffed_model.yaml'
                pty = PythonToYaml(change_model)
                pty.write_to_yaml_file(file_name)

            except YamlException, ye:
                __logger.severe('WLSDPLY-05708', file_name, ye.getLocalizedMessage(),
                                error=ye, class_name=_class_name, method_name=_method_name)
                ex = exception_helper.create_compare_exception('WLSDPLY-05708', file_name, ye.getLocalizedMessage(),
                                                               error=ye)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
        else:
            # write the change model to standard output in YAML format
            print(format_message('WLSDPLY-05707'))
            print(BLANK_LINE)
            pty = PythonToYaml(change_model)
            pty.write_to_stream(System.out)

        return 0

    def get_compare_msgs(self):
        """
        Return any warning or info messages.
        :return: Set of warning or info messages
        """
        return self.compare_msgs


def debug(format_string, *arguments):
    """
    Generic debug code.
    :param format_string:  python formatted string
    :param arguments: arguments for the formatted string
    """
    if os.environ.has_key('DEBUG_COMPARE_MODEL_TOOL'):
        print(format_string % arguments)
    else:
        __logger.finest(format_string, arguments)


def _check_model_extension(file):
    model_file = JFile(file)
    if not (FileUtils.isYamlFile(model_file) or FileUtils.isJsonFile(model_file)):
        return False
    else:
        return True


def main(model_context):
    """
    The main entry point for the compareModel tool.

    :param model_context: the model context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _output_dir = None
    _exit_code = ExitCode.OK

    try:
        _output_dir = model_context.get_output_dir()
        model1 = model_context.get_trailing_argument(0)
        model2 = model_context.get_trailing_argument(1)

        for f in [model1, model2]:
            if not os.path.exists(f):
                raise CLAException(ExitCode.ERROR, 'WLSDPLY-85717', [f])
            if os.path.isdir(f):
                raise CLAException(ExitCode.ERROR, 'WLSDPLY-85718', [f])
            if not _check_model_extension(f):
                raise CLAException(ExitCode.ERROR, 'WLSDPLY-85719', [f])

        obj = ModelFileDiffer(model1, model2, model_context, _output_dir)
        obj.compare()
        if _output_dir:
            fos = None
            writer = None
            file_name = None
            if len(obj.get_compare_msgs()) > 0:
                try:
                    file_name = _output_dir + '/compare_model_stdout'
                    print format_message('WLSDPLY-05715', len(obj.get_compare_msgs()), file_name)
                    fos = JFileOutputStream(file_name, False)
                    writer = JPrintWriter(fos, True)
                    writer.println(BLANK_LINE)
                    writer.println(BLANK_LINE)
                    index = 1
                    for line in obj.get_compare_msgs():
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
                    __logger.severe('WLSDPLY-05708', file_name, ioe.getLocalizedMessage(),
                                    error=ioe, class_name=_class_name, method_name=_method_name)
        else:
            if len(obj.get_compare_msgs()) > 0:
                print(BLANK_LINE)
                print(BLANK_LINE)
                index = 1
                for line in obj.get_compare_msgs():
                    msg_key = line[0]
                    msg_value = line[1]
                    print("%s. %s" % (index, format_message(msg_key,msg_value.replace(PATH_TOKEN, "-->"))))
                    index = index + 1
                    print(BLANK_LINE)

    except CLAException, ex:
        _exit_code = ex.getExitCode()
        if _exit_code != ExitCode.HELP:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
    except CompareException, ce:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-05704', ce.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
    except PyWLSTException, pe:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-05704', pe.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        _exit_code = ExitCode.ERROR
        ee_string = traceback.format_exception(exc_type, exc_obj, exc_tb)
        __logger.severe('WLSDPLY-05704', ee_string)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


def format_message(key, *args):
    """
    Get message using the bundle.
    :param key: bundle key
    :param args: bundle arguments
    :return:
    """
    return ExceptionHelper.getMessage(key, list(args))


if __name__ == "__main__":
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
