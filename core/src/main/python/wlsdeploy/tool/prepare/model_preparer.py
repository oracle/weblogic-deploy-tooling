# Copyright (c) 2020, 2021, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

import os
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.validate import ValidateException

import oracle.weblogic.deploy.util.TranslateException as TranslateException
import wlsdeploy.util.variables as variables
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.tool.util.variable_injector import VARIABLE_FILE_UPDATE
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import model
from wlsdeploy.util import target_configuration_helper
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.yaml.yaml_translator import PythonToYaml

_program_name = 'prepareModel'
_class_name = 'ModelPreparer'


class ModelPreparer:
    """
    This class prepares model files for deployment to a target environment.
    """
    def __init__(self, model_files, model_context, logger, output_dir=None):
        self.model_files = model_files
        self.output_dir = output_dir
        self.model_context = model_context
        self._aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE,
                                exception_type=ExceptionType.PREPARE)
        self._logger = logger
        self._name_tokens_location = LocationContext()
        self._name_tokens_location.add_name_token('DOMAIN', "testdomain")
        self.current_dict = None
        self.credential_injector = CredentialInjector(_program_name, None, model_context)

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

        variable_injector = VariableInjector(_program_name, model_dict, model_context,
                                             WebLogicHelper(self._logger).get_actual_weblogic_version(),
                                             credential_properties)

        # update the variable file with any new values
        unused_variable_keys_to_remove = self.credential_injector.get_variable_keys_for_removal()
        inserted, variable_model, variable_file_name = \
            variable_injector.inject_variables_keyword_file(append_option=VARIABLE_FILE_UPDATE,
                                                            variable_keys_to_remove=unused_variable_keys_to_remove)

        # return variable_model - if writing the variables file failed, this will be the original model.
        # a warning is issued in inject_variables_keyword_file() if that was the case.
        return variable_model

    def __walk_model_section(self, model_section_key, model_dict, valid_section_folders):
        _method_name = '__walk_model_section'

        if model_section_key not in model_dict.keys():
            return

        # only specific top-level sections have attributes
        attribute_location = self._aliases.get_model_section_attribute_location(model_section_key)

        valid_attr_infos = []

        if attribute_location is not None:
            valid_attr_infos = self._aliases.get_model_attribute_names_and_types(attribute_location)

        model_section_dict = model_dict[model_section_key]
        for section_dict_key, section_dict_value in model_section_dict.iteritems():
            # section_dict_key is either the name of a folder in the
            # section, or the name of an attribute in the section.
            model_location = LocationContext()

            if section_dict_key in valid_attr_infos:
                # section_dict_key is the name of an attribute in the section
                self.__walk_attribute(model_section_dict, section_dict_key, attribute_location)

            elif section_dict_key in valid_section_folders:
                # section_dict_key is a folder under the model section

                # Append section_dict_key to location context
                model_location.append_location(section_dict_key)

                # Call self.__walk_model_folder() passing in section_dict_value as the model_node to process
                self.__walk_model_folder(section_dict_value, model_location)

    def __walk_model_folder(self, model_node, validation_location):
        _method_name = '__walk_model_folder'

        if self._aliases.supports_multiple_mbean_instances(validation_location):

            for name in model_node:
                expanded_name = name

                new_location = LocationContext(validation_location)

                name_token = self._aliases.get_name_token(new_location)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                value_dict = model_node[name]

                self.__walk_model_node(value_dict, new_location)

        elif self._aliases.requires_artificial_type_subfolder_handling(validation_location):

            for name in model_node:
                expanded_name = name

                new_location = LocationContext(validation_location)

                name_token = self._aliases.get_name_token(new_location)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                value_dict = model_node[name]

                self.__walk_model_node(value_dict, new_location)

        else:
            name_token = self._aliases.get_name_token(validation_location)

            if name_token is not None:
                name = self._name_tokens_location.get_name_for_token(name_token)

                if name is None:
                    name = '%s-0' % name_token

                validation_location.add_name_token(name_token, name)

            self.__walk_model_node(model_node, validation_location)

    def __walk_model_node(self, model_node, validation_location):
        _method_name = '__walk_model_node'

        valid_folder_keys = self._aliases.get_model_subfolder_names(validation_location)
        valid_attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)

        for key, value in model_node.iteritems():

            if key in valid_folder_keys:
                new_location = LocationContext(validation_location).append_location(key)

                if self._aliases.is_artificial_type_folder(new_location):
                    # key is an ARTIFICIAL_TYPE folder
                    valid_attr_infos = self._aliases.get_model_attribute_names_and_types(new_location)

                    self.__walk_attributes(value, valid_attr_infos, new_location)
                else:
                    self.__walk_model_folder(value, new_location)

            elif key in valid_attr_infos:
                # aliases.get_model_attribute_names_and_types(location) filters out
                # attributes that ARE NOT valid in the wlst_version being used, so if
                # we're in this section of code we know key is a bonafide "valid" attribute
                self.__walk_attribute(model_node, key, validation_location)

    def __walk_attributes(self, attributes_dict, valid_attr_infos, validation_location):
        _method_name = '__walk_attributes'

        for attribute_name, attribute_value in attributes_dict.iteritems():
            if attribute_name in valid_attr_infos:
                self.__walk_attribute(attributes_dict, attribute_name, validation_location)

    def __walk_attribute(self, model_dict, attribute_name, attribute_location):
        _method_name = '__walk_attribute'

        self.credential_injector.check_and_tokenize(model_dict, attribute_name, attribute_location)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

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

                return_code = validator.validate_in_tool_mode(model_dictionary,
                                                              variables_file_name=variable_file,
                                                              archive_file_name=None)

                if return_code == Validator.ReturnCode.STOP:
                    ex = exception_helper.create_prepare_exception('WLSDPLY-05804', model_file_name)
                    self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                    raise ex

                self.current_dict = model_dictionary

                self.__walk_model_section(model.get_model_domain_info_key(), self.current_dict,
                                          aliases.get_model_section_top_level_folder_names(DOMAIN_INFO))

                self.__walk_model_section(model.get_model_topology_key(), self.current_dict,
                                          aliases.get_model_topology_top_level_folder_names())

                self.__walk_model_section(model.get_model_resources_key(), self.current_dict,
                                          aliases.get_model_resources_top_level_folder_names())

                self.current_dict = self._apply_filter_and_inject_variable(self.current_dict, self.model_context)

                file_name = os.path.join(self.output_dir, os.path.basename(model_file_name))
                pty = PythonToYaml(self.current_dict)
                pty.write_to_yaml_file(file_name)

                cla_helper.merge_model_dictionaries(merged_model_dictionary, self.current_dict, None)

            # filter variables or secrets that are no longer in the merged, filtered model
            filter_helper.apply_filters(merged_model_dictionary, "discover", self.model_context)
            self.credential_injector.filter_unused_credentials(merged_model_dictionary)

            # use a merged, substituted, filtered model to get domain name and create additional target output.
            full_model_dictionary = cla_helper.load_model(_program_name, self.model_context, self._aliases,
                                                          "discover", WlstModes.OFFLINE)

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
                    credential_caches[key] = variables._substitute(credential_caches[key],
                                                                   original_variables, self.model_context)

            target_config = self.model_context.get_target_configuration()
            if target_config.generate_script_for_secrets():
                target_configuration_helper.generate_k8s_script(self.model_context,
                                                                self.credential_injector.get_variable_cache(),
                                                                full_model_dictionary, ExceptionType.VALIDATE)

            if target_config.generate_json_for_secrets():
                target_configuration_helper.generate_k8s_json(self.model_context,
                                                              self.credential_injector.get_variable_cache(),
                                                              full_model_dictionary)

            # create any additional outputs from full model dictionary
            target_configuration_helper.create_additional_output(Model(full_model_dictionary), self.model_context,
                                                                 self._aliases, self.credential_injector,
                                                                 ExceptionType.VALIDATE)

        except (ValidateException, VariableException, TranslateException), e:
            self._logger.severe('WLSDPLY-20009', _program_name, model_file_name, e.getLocalizedMessage(),
                                error=e, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_prepare_exception(e.getLocalizedMessage(), error=e)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
