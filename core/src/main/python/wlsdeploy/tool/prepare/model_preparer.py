"""
Copyright (c) 2021, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import os
from java.io import FileInputStream
from java.io import IOException
from java.util import Properties
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.validate import ValidateException

import oracle.weblogic.deploy.util.TranslateException as TranslateException
import wlsdeploy.util.variables as variables
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DOMAIN_SCRIPTS
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.tool.util.variable_injector import VARIABLE_FILE_UPDATE
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.tool.validate.content_validator import ContentValidator
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import target_configuration_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.yaml.yaml_translator import PythonToYaml

_program_name = 'prepareModel'
_class_name = 'ModelPreparer'


class ModelPreparer:
    """
    This class prepares model files for deployment to a target environment.
    """
    def __init__(self, model_files, model_context, output_dir=None):
        self.model_files = model_files
        self.output_dir = output_dir
        self.model_context = model_context
        self._aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE,
                                exception_type=ExceptionType.PREPARE)
        self._logger = PlatformLogger('wlsdeploy.prepare_model')
        self.current_dict = None
        self.credential_injector = CredentialInjector(_program_name, model_context, self._aliases)

    def fix_property_secrets(self):
        # Just in case the credential cache has @@PROP in the model's attribute value,
        # we use the original variable file to resolve it,
        # so that the generated json/script files have the resolved property value(s) instead of the @@PROP token.
        # it's possible that the variable file is not specified, or does not exist yet.

        original_variables = {}
        variable_file = self.model_context.get_variable_file()
        if variable_file is not None and os.path.exists(variable_file):
            original_variables = variables.load_variables(variable_file)

        credential_caches = self.credential_injector.get_variable_cache()
        for key in credential_caches:
            if variables.is_variable_string(credential_caches[key]):
                credential_caches[key] = variables.substitute_value(credential_caches[key],
                                                                    original_variables, self.model_context)

    def _apply_filter_and_inject_variable(self, model_dict, model_context):
        """
        Applying filter
        Inject variable for tokens
        :param model_dict: updated model
        """
        _method_name = '_apply_filter_and_inject_variable'
        self._logger.entering(class_name=_class_name, method_name=_method_name)

        if filter_helper.apply_filters(model_dict, "discover", model_context):
            self._logger.info('WLSDPLY-06014', _class_name=_class_name, method_name=_method_name)

        # include credential properties in the injector map, unless target uses credential secrets
        target_config = model_context.get_target_configuration()
        if target_config.uses_credential_secrets():
            credential_properties = {}
        else:
            credential_properties = self.credential_injector.get_variable_cache()

        if target_config.exclude_domain_bin_contents() and DOMAIN_INFO in model_dict \
                and DOMAIN_SCRIPTS in model_dict[DOMAIN_INFO]:
            del model_dict[DOMAIN_INFO][DOMAIN_SCRIPTS]

        variable_injector = VariableInjector(_program_name, model_context, self._aliases,
                                             credential_properties)

        # update the variable file with any new values
        inserted, variable_model, variable_file_name = \
            variable_injector.inject_variables_from_configuration(model_dict, append_option=VARIABLE_FILE_UPDATE)

        # return variable_model - if writing the variables file failed, this will be the original model.
        # a warning is issued in inject_variables_keyword_file() if that was the case.
        return variable_model

    def _add_model_variables(self, model_dictionary, all_variables):
        """
        Add any variable values found in the model dictionary to the variables list
        :param model_dictionary: the dictionary to be examined
        :param all_variables: the list to be appended
        """
        for key in model_dictionary:
            value = model_dictionary[key]
            if isinstance(value, dict):
                self._add_model_variables(value, all_variables)
            else:
                matches = variables.get_variable_matches(str_helper.to_string(value))
                for token, variable_key in matches:
                    all_variables.append(variable_key)

    def _clean_variable_files(self, merged_model_dictionary):
        """
        Remove any unused variables that are not in the merged model from the variable file.
        :param merged_model_dictionary: a model with every property.
        """
        _method_name = '_clean_variable_files'

        all_model_variables = []
        self._add_model_variables(merged_model_dictionary, all_model_variables)

        original_file = self.model_context.get_variable_file()
        if original_file:
            output_file = os.path.join(self.output_dir, os.path.basename(original_file))
            if os.path.exists(output_file):
                try:
                    fis = FileInputStream(output_file)
                    properties = Properties()
                    properties.load(fis)
                    fis.close()

                    variable_dict = {}
                    for key in list(properties.keySet()):
                        if key in all_model_variables:
                            variable_dict[key] = properties.get(key)

                    # use this method instead of Properties.store() to maintain order
                    variables.write_sorted_variables(_program_name, variable_dict, output_file)
                except IOException, e:
                    self._logger.warning('WLSDPLY-05803', e.getLocalizedMessage(),
                                         class_name=_class_name, method_name=_method_name)

    def _clean_archive_files(self):
        """
        Remove any content necessary from the archive file.
        """
        archive_file_name = self.model_context.get_archive_file_name()
        if archive_file_name is None:
            return

        # If the archive file(s) exist, always make a copy even if we aren't filtering them
        archive_helper = ArchiveList(archive_file_name, self.model_context,
                                     exception_helper.ExceptionType.PREPARE)
        archive_helper = archive_helper.copy_archives_to_target_directory(self.model_context.get_output_dir())

        if self.model_context.get_target_configuration().exclude_domain_bin_contents():
            archive_helper.remove_domain_scripts()

    def _apply_final_filters(self, model_dictionary):
        """
        Apply final filters to the merged model dictionary,
        and apply any updates to the last model in the command-line list.
        """
        model_file_list = self.model_files.split(',')
        last_file = model_file_list[-1]
        update_file = os.path.join(self.output_dir, os.path.basename(last_file))

        update_model_dict = FileToPython(update_file, True).parse()
        filter_helper.apply_final_filters(model_dictionary, update_model_dict, self.model_context)

        pty = PythonToYaml(update_model_dict)
        pty.write_to_yaml_file(update_file)

    def prepare_models(self):
        """
        Replace password attributes in each model file with secret tokens, and write each model.
        Generate a script to create the required secrets.
        Create any additional output specified for the target environment.
        """
        _method_name = "prepare_models"

        model_file_name = None

        # create a merged model that is not substituted
        merged_model_dictionary = {}
        try:
            model_file_list = self.model_files.split(',')
            target = self.model_context.get_target()

            for model_file in model_file_list:
                if os.path.splitext(model_file)[1].lower() == ".yaml":
                    model_file_name = model_file

                if target is not None and self.model_context.get_target_configuration().get_additional_output_types():
                    additional_output_types = []
                    output_types = self.model_context.get_target_configuration().get_additional_output_types()

                    if isinstance(output_types, list):
                        additional_output_types.extend(output_types)
                    else:
                        additional_output_types.append(output_types)

                    if os.path.basename(model_file_name) in additional_output_types:
                        ex = exception_helper.create_prepare_exception('WLSDPLY-05802',
                                                                       os.path.basename(model_file_name),
                                                                       additional_output_types, target)
                        self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex

                FileToPython(model_file_name, True).parse()

                aliases = Aliases(model_context=self.model_context, wlst_mode=WlstModes.OFFLINE)

                validator = Validator(self.model_context, aliases, wlst_mode=WlstModes.OFFLINE)

                # Just merge and validate but without substitution
                model_dictionary = cla_helper.merge_model_files(model_file_name, None)

                variable_file = self.model_context.get_variable_file()
                if variable_file is not None and not os.path.exists(variable_file):
                    variable_file = None

                archive_file_name = self.model_context.get_archive_file_name()
                return_code = validator.validate_in_tool_mode(model_dictionary,
                                                              variables_file_name=variable_file,
                                                              archive_file_name=archive_file_name)

                if return_code == Validator.ReturnCode.STOP:
                    ex = exception_helper.create_prepare_exception('WLSDPLY-05804', model_file_name)
                    self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                    raise ex

                self.current_dict = model_dictionary

                self.credential_injector.inject_model_variables(self.current_dict)

                self.current_dict = self._apply_filter_and_inject_variable(self.current_dict, self.model_context)

                file_name = os.path.join(self.output_dir, os.path.basename(model_file_name))
                pty = PythonToYaml(self.current_dict)
                pty.write_to_yaml_file(file_name)

                cla_helper.merge_model_dictionaries(merged_model_dictionary, self.current_dict, None)

            # filter variables or secrets that are no longer in the merged, filtered model
            filter_helper.apply_filters(merged_model_dictionary, "discover", self.model_context)
            self.credential_injector.filter_unused_credentials(merged_model_dictionary)
            self._clean_variable_files(merged_model_dictionary)
            self._clean_archive_files()

            # resolve variables in the model AFTER the clean and filter has been done,
            # but before generating output files.

            result_variable_map = {}
            source_variable_file = self.model_context.get_variable_file()
            if source_variable_file:
                result_variable_file = os.path.join(self.output_dir, os.path.basename(source_variable_file))
            else:
                result_variable_file = variables.get_default_variable_file_name(self.model_context)

            if os.path.exists(result_variable_file):
                result_variable_map = variables.load_variables(result_variable_file)

            variables.substitute(merged_model_dictionary, result_variable_map, self.model_context)

            # correct any secret values that point to @@PROP values
            self.fix_property_secrets()

            # apply final filter changes for the merged model to the last source model
            self._apply_final_filters(merged_model_dictionary)

            # check for any content problems in the merged, substituted model
            content_validator = ContentValidator(self.model_context, self._aliases)
            content_validator.validate_model(merged_model_dictionary)

            target_configuration_helper.generate_all_output_files(Model(merged_model_dictionary), self._aliases,
                                                                  self.credential_injector, self.model_context,
                                                                  ExceptionType.PREPARE)

        except (ValidateException, VariableException, TranslateException), e:
            self._logger.severe('WLSDPLY-20009', _program_name, model_file_name, e.getLocalizedMessage(),
                                error=e, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_prepare_exception(e.getLocalizedMessage(), error=e)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
