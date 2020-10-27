"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.json.json_translator import JsonStreamToPython
from wlsdeploy.logging import platform_logger

DOMAIN_RESOURCE_SCHEMA_ROOT = "openAPIV3Schema"
DOMAIN_RESOURCE_SCHEMA_FILE = 'domain-crd-schemav7-260.json'
DOMAIN_RESOURCE_SCHEMA_PATH = 'oracle/weblogic/deploy/wko/' + DOMAIN_RESOURCE_SCHEMA_FILE

_logger = platform_logger.PlatformLogger('wlsdeploy.deploy')
_class_name = 'wko_schema_helper'


def get_domain_resource_schema(exception_type=ExceptionType.DEPLOY):
    """
    Read the WKO domain resource schema from its resource path.
    """
    _method_name = 'get_domain_resource_schema'

    template_stream = None
    try:
        template_stream = FileUtils.getResourceAsStream(DOMAIN_RESOURCE_SCHEMA_PATH)
        if template_stream is None:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-10010', DOMAIN_RESOURCE_SCHEMA_PATH)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        full_schema = JsonStreamToPython(DOMAIN_RESOURCE_SCHEMA_FILE, template_stream, True).parse()

        # remove the root element, since it has a version-specific name
        schema = full_schema[DOMAIN_RESOURCE_SCHEMA_ROOT]

    finally:
        if template_stream:
            template_stream.close()

    return schema
