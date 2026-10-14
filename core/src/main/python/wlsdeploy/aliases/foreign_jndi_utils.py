"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.model_constants import FOREIGN_JNDI_PROVIDER
from wlsdeploy.aliases.model_constants import FOREIGN_SERVER
from wlsdeploy.aliases.model_constants import JNDI_PROPERTY
from wlsdeploy.aliases.model_constants import PROPERTIES
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper


def is_provider_properties(location, attribute, wls_version):
    return attribute == PROPERTIES and location.get_current_model_folder() == FOREIGN_JNDI_PROVIDER and \
        string_utils.is_weblogic_version_or_above(wls_version, '26.1')


def is_jms_property_value(location, attribute, wls_version):
    folders = location.get_model_folders()
    return attribute == 'Value' and len(folders) > 1 and folders[-2:] == [FOREIGN_SERVER, JNDI_PROPERTY] and \
        string_utils.is_weblogic_version_or_above(wls_version, '26.1')


def is_encrypted_property(property_name, wls_version):
    return property_name is not None and str_helper.to_string(property_name).endswith('.encrypted') and \
        string_utils.is_weblogic_version_or_above(wls_version, '26.1')
