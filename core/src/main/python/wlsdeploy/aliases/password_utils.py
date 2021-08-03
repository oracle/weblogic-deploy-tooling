"""
Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Contains methods for special processing of dual-password attributes.
Dual-password attributes follow a common pattern in WLST, with the following rules.
These examples will use a prefix of Password*, but there are others throughout WLST.

Offline:
1. There is a single attribute name that includes the suffix, such as "PasswordEncrypted".
2. The attribute can be set to an encrypted ("{AES}...") or unencrypted value.
3. When the value is read, it is always encrypted.

Online:
1. There are two attributes, with and without the prefix, such as "Password" and "PasswordEncrypted". Both
   represent the same underlying value.
2. The encrypted attribute can only be set to an encrypted value.
3. The unencrypted attribute can only be set to an unencrypted value.
4. Only the unencrypted value can be read, and that value is encrypted.

In the alias file, these fields are flagged with the "password" WLST type, and the WLST name ends with "Encrypted".

The discovery code makes special provisions to skip the unencrypted online attribute.

The create and deploy code makes special provisions to set either the encrypted unencrypted online attribute,
depending on whether the model value is encrypted.
"""

from oracle.weblogic.deploy.encrypt import EncryptionUtils

from wlsdeploy.aliases.alias_constants import WLST_NAME
from wlsdeploy.aliases.alias_constants import WLST_TYPE
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils

_class_name = 'password_utils'
_logger = PlatformLogger('wlsdeploy.aliases')
_dual_password_suffix = 'Encrypted'


def get_wlst_skip_name(attribute_info, wlst_mode):
    """
    Returns a WLST attribute name, derived from the the specified attribute information, that should be ignored.
    For example, the model attribute PasswordEncrypted may indicate that the WLST attribute Password should be ignored.
    :param attribute_info: the attribute information to be checked
    :param wlst_mode: the offline or online type to be checked
    :return: a single name to be skipped, or None
    """
    if _is_dual_password(attribute_info) and (wlst_mode == WlstModes.ONLINE):
        return _get_non_encrypted_wlst_name(attribute_info)
    return None


def get_wlst_attribute_name(attribute_info, attribute_value, wlst_mode):
    """
    Returns the corrected WLST attribute name for the specified parameters.
    The "Encrypted" suffix is removed from online dual-password attributes for use with unencrypted values.
    :param attribute_info: the attribute information to be checked
    :param attribute_value: the value to be checked for encryption
    :param wlst_mode: the offline or online type to be checked
    :return: the corrected value, or None if no correction was required
    """
    if _is_dual_password(attribute_info) and (wlst_mode == WlstModes.ONLINE) \
            and not EncryptionUtils.isEncryptedString(attribute_value):
        return _get_non_encrypted_wlst_name(attribute_info)
    return None


def _is_dual_password(attribute_info):
    """
    Returns true if the specified attribute information indicates a dual-password field.
    This means the WLST type is password, and the WLST name ends with "Encrypted".
    :param attribute_info: the attribute information to be checked
    :return: True if this is a dual-password field, False otherwise
    """
    wlst_name = dictionary_utils.get_element(attribute_info, WLST_NAME)  # type: str
    wlst_type = dictionary_utils.get_element(attribute_info, WLST_TYPE)
    return (wlst_type == 'password') and wlst_name.endswith(_dual_password_suffix)


def _get_non_encrypted_wlst_name(attribute_info):
    """
    Returns the prefix portion of the WLST name from the specified attribute information.
    It is assumed that the attribute information is confirmed to be dual-password.
    :param attribute_info: the attribute information to be checked
    :return: the prefix portion of the WLST name
    """
    wlst_name = dictionary_utils.get_element(attribute_info, WLST_NAME)  # type: str
    return wlst_name[0:-len(_dual_password_suffix)]
