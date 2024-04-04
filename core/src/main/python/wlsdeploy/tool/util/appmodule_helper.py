"""
Copyright (c) 2022, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import re

from wlsdeploy.logging import platform_logger

_logger = platform_logger.PlatformLogger('wlsdeploy.appmodule_helper')


def process_jdbc_appmodule_xml(xml_file, model_context):

    for beg_tag in [ "<password-encrypted>", "<ons-wallet-password-encrypted>"]:
        end_tag = beg_tag.replace("<", "</")
        expr = r'%s(.*)%s' % (beg_tag, end_tag)
        pattern = re.compile(expr, re.DOTALL)
        matched_groups = re.search(pattern, xml_file)
        if matched_groups:
            value = matched_groups.groups()[0]
            wls_helper = model_context.get_weblogic_helper()
            xml_file = xml_file.replace(beg_tag + value + end_tag,
                                        beg_tag + wls_helper.encrypt(value, model_context.get_domain_home()) + end_tag)

    return xml_file


def process_jms_appmodule_xml(xml_file, model_context):

    for beg_tag in [ "<password-encrypted>", "<jndi-properties-credential-encrypted>"]:
        end_tag = beg_tag.replace("<", "</")
        expr = r'%s(.*)%s' % (beg_tag, end_tag)
        pattern = re.compile(expr, re.DOTALL)
        matched_groups = re.search(pattern, xml_file)
        if matched_groups:
            wls_helper = model_context.get_weblogic_helper()
            for g in matched_groups.groups():
                value = g
                xml_file = xml_file.replace(beg_tag + value + end_tag,
                                            beg_tag + wls_helper.encrypt(value, model_context.get_domain_home()) + end_tag)

    return xml_file

