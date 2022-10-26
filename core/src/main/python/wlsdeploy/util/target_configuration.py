"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.validate_configuration import VALIDATION_METHODS
from wlsdeploy.tool.util.targets import model_crd_helper

# types for credential method
CREDENTIALS_METHOD = "credentials_method"

# results output method: "default" (script and additional output) or "json" (single results file)
RESULTS_OUTPUT_METHOD = "results_output_method"

# type for validation method
VALIDATION_METHOD = "validation_method"

# Overrides the Kubernetes secret name for the WebLogic admin user credential
WLS_CREDENTIALS_NAME = "wls_credentials_name"

# Determines whether the domainBin contents should be excluded
EXCLUDE_DOMAIN_BIN_CONTENTS = "exclude_domain_bin_contents"

# Determines whether a persistent volume is used
USE_PERSISTENT_VOLUME = "use_persistent_volume"

# Determines the type of domain used
DOMAIN_HOME_SOURCE_TYPE = "domain_home_source_type"

# Determines if replica count is applied at the cluster level
SET_CLUSTER_REPLICAS = "set_cluster_replicas"

# Determines the version of the target product.
PRODUCT_VERSION = 'product_version'
DEFAULT_PRODUCT_VERSION = 'v3'  # default for WKO and WKO in VZ

# put secret tokens in the model, and build a script to create the secrets.
SECRETS_METHOD = 'secrets'

# put password placeholders in the model, and build a script to create the secrets.
CONFIG_OVERRIDES_SECRETS_METHOD = 'config_override_secrets'

CREDENTIALS_METHODS = [
    SECRETS_METHOD,
    CONFIG_OVERRIDES_SECRETS_METHOD
]

# domain home source types and names
DOMAIN_IN_IMAGE_SOURCE_TYPE = 'dii'
MODEL_IN_IMAGE_SOURCE_TYPE = 'mii'
PERSISTENT_VOLUME_SOURCE_TYPE = 'pv'

SOURCE_TYPE_NAMES = {
    DOMAIN_IN_IMAGE_SOURCE_TYPE: 'Image',
    MODEL_IN_IMAGE_SOURCE_TYPE: 'FromModel',
    PERSISTENT_VOLUME_SOURCE_TYPE: 'PersistentVolume'
}

DEFAULT_RESULTS_OUTPUT_METHOD = "default"
JSON_RESULTS_OUTPUT_METHOD = "json"
RESULTS_OUTPUT_METHODS = [
    DEFAULT_RESULTS_OUTPUT_METHOD,
    JSON_RESULTS_OUTPUT_METHOD
]


class TargetConfiguration(object):
    """
    Provide access to fields in the target.json JSON file of a target environment.
    """
    _class_name = 'TargetConfiguration'
    _logger = PlatformLogger('wlsdeploy.util')

    def __init__(self, config_dictionary):
        """
        Initialize the configuration with the target file's dictionary.
        :param config_dictionary: the top-level dictionary from the target.json file
        """
        if config_dictionary is None:
            self.config_dictionary = {}
        else:
            self.config_dictionary = config_dictionary

    def get_credentials_method(self):
        """
        Returns the method for handling credentials in the model.
        :return: the method for handling credentials
        """
        return dictionary_utils.get_element(self.config_dictionary, CREDENTIALS_METHOD)

    def get_results_output_method(self):
        """
        Returns the method for generating results output.
        :return: "default" (script and additional files) or "json" (single results file)
        """
        result = dictionary_utils.get_element(self.config_dictionary, RESULTS_OUTPUT_METHOD)
        if result is None:
            result = DEFAULT_RESULTS_OUTPUT_METHOD
        return result

    def get_wls_credentials_name(self):
        """
        Returns the method for handling credentials in the model.
        :return: the method for handling credentials
        """
        return dictionary_utils.get_element(self.config_dictionary, WLS_CREDENTIALS_NAME)

    def get_additional_output_types(self):
        """
        Return the additional output types for this target environment.
        This is a list of keys that map to output types.
        """
        types = dictionary_utils.get_element(self.config_dictionary, 'additional_output')
        if types is not None:
            return types.split(',')
        return []

    def get_validation_method(self):
        """
        Return the validation method for this target environment.
        :return: the validation method, or None
        """
        return dictionary_utils.get_element(self.config_dictionary, VALIDATION_METHOD)

    def get_model_filters(self):
        """
        Return a dictionary of model filters for this target environment.
        :return: the dictionary of model filters
        """
        return dictionary_utils.get_dictionary_element(self.config_dictionary, 'model_filters')

    def get_variable_injectors(self):
        """
        Return a dictionary of variable injectors for this target environment.
        :return: the dictionary of variable injectors
        """
        return dictionary_utils.get_dictionary_element(self.config_dictionary, 'variable_injectors')

    def get_additional_secrets(self):
        """
        Return a list of secrets to be included in the create secrets script.
        :return: a list of secrets
        """
        secrets = dictionary_utils.get_element(self.config_dictionary, 'additional_secrets')
        if secrets is not None:
            return secrets.split(',')
        return []

    def uses_credential_secrets(self):
        """
        Determine if this configuration uses secrets to manage credentials.
        :return: True if secrets are used, False otherwise
        """
        return self.get_credentials_method() in [SECRETS_METHOD, CONFIG_OVERRIDES_SECRETS_METHOD]

    def generate_results_file(self):
        """
        Determine if a JSON results file should be created.
        :return: True if results file should be created, False otherwise
        """
        return self.get_results_output_method() == JSON_RESULTS_OUTPUT_METHOD

    def generate_output_files(self):
        """
        Determine if scripts and additional output files should be created.
        :return: True files should be created, False otherwise
        """
        return self.get_results_output_method() == DEFAULT_RESULTS_OUTPUT_METHOD

    def manages_credentials(self):
        """
        Determine if this configuration manages credential values in the model.
        If this is True, credentials will not go into the properties file.
        :return: True if credential values are managed, False otherwise
        """
        return self.get_credentials_method() in [SECRETS_METHOD, CONFIG_OVERRIDES_SECRETS_METHOD]

    def exclude_domain_bin_contents(self):
        """
        Determine if the contents of the domain's bin directory should be
        excluded from the model and archive.  If True, these files will be
        excluded and not go into the model or archive file.
        :return: True if the domain bin contents should be excluded, False otherwise
        """
        result = dictionary_utils.get_element(self.config_dictionary, EXCLUDE_DOMAIN_BIN_CONTENTS)
        if result is None:
            result = False
        return result

    def use_persistent_volume(self):
        """
        Determine if this configuration uses a persistent volume for the domain home.
        :return: True if persistent volume is used, False otherwise
        """
        result = dictionary_utils.get_element(self.config_dictionary, USE_PERSISTENT_VOLUME)
        if result is None:
            result = False
        return result

    def uses_wdt_model(self):
        """
        Determine if this configuration will include WDT model content in the output file.
        WKO builds the domain using this model content for the model-in-image source type.
        :return: True if a model is included, False otherwise
        """
        source_type = self._get_domain_home_source_type()
        return source_type == MODEL_IN_IMAGE_SOURCE_TYPE

    def get_domain_home_source_name(self):
        """
        Return the name associated with the domain home source type key.
        :return: the domain home source name
        """
        source_type = self._get_domain_home_source_type()
        return SOURCE_TYPE_NAMES[source_type]

    def sets_cluster_replicas(self):
        """
        Return True if this configuration will calculate and apply replica counts at the cluster level.
        :return: True if a replica counts are applied, False otherwise
        """
        result = dictionary_utils.get_element(self.config_dictionary, SET_CLUSTER_REPLICAS)
        return result or False

    def get_product_version(self):
        """
        Return the version of the product being targeted, such as WKO or VZ.
        :return: the product version
        """
        result = dictionary_utils.get_element(self.config_dictionary, PRODUCT_VERSION)
        if result is not None:
            return result
        return DEFAULT_PRODUCT_VERSION

    def validate_configuration(self, exit_code, target_configuration_file):
        validation_method = self.get_validation_method()
        self._validate_enumerated_field(VALIDATION_METHOD, validation_method, VALIDATION_METHODS, exit_code,
                                        target_configuration_file)

        credentials_method = self.get_credentials_method()
        self._validate_enumerated_field(CREDENTIALS_METHOD, credentials_method, CREDENTIALS_METHODS, exit_code,
                                        target_configuration_file)

        product_version = self.get_product_version()
        valid_product_versions = model_crd_helper.get_valid_versions(model_crd_helper.WKO_PRODUCT_KEY)
        self._validate_enumerated_field(PRODUCT_VERSION, product_version, valid_product_versions, exit_code,
                                        target_configuration_file)

        source_type = self._get_domain_home_source_type()
        self._validate_enumerated_field(DOMAIN_HOME_SOURCE_TYPE, source_type, SOURCE_TYPE_NAMES.keys(), exit_code,
                                        target_configuration_file)

        output_method = self.get_results_output_method()
        self._validate_enumerated_field(RESULTS_OUTPUT_METHOD, output_method, RESULTS_OUTPUT_METHODS, exit_code,
                                        target_configuration_file)

    ###################
    # Private methods #
    ###################

    def _get_domain_home_source_type(self):
        """
        Get the domain home source type (private method).
        :return: the domain home source type key, or the default MODEL_IN_IMAGE_SOURCE_TYPE
        """
        source_type = dictionary_utils.get_element(self.config_dictionary, DOMAIN_HOME_SOURCE_TYPE)
        return source_type or MODEL_IN_IMAGE_SOURCE_TYPE

    def _validate_enumerated_field(self, key, value, valid_values, exit_code, target_configuration_file):
        method_name = '_validate_enumerated_field'
        if (value is not None) and (value not in valid_values):
            ex = exception_helper.create_cla_exception(exit_code, 'WLSDPLY-01648', target_configuration_file,
                                                       value, key, ', '.join(valid_values))
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
