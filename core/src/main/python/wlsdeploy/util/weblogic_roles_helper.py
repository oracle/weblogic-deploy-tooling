"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import os
from java.io import File
from java.lang import String
from wlsdeploy.exception import exception_helper

import com.bea.common.security.utils.encoders.BASE64Encoder as BASE64Encoder
import com.bea.common.security.xacml.DocumentParseException as DocumentParseException
import com.bea.common.security.xacml.URISyntaxException as URISyntaxException
import com.bea.security.providers.xacml.entitlement.EntitlementConverter as EntitlementConverter
import com.bea.security.xacml.cache.resource.ResourcePolicyIdUtil as ResourcePolicyIdUtil

WLS_XACML_ROLE_MAPPER_LDIFT_FILENAME = 'XACMLRoleMapperInit.ldift' 

class WebLogicRolesHelper(object):
    """
    Helper functions for handling WebLogic Roles
    """
    __class_name = 'WebLogicRolesHelper'

    def __init__(self, logger, exception_type, domain_security_folder):
        self.logger = logger
        self._exception_type = exception_type
        self._domain_security_folder = domain_security_folder
        self._b64encoder = BASE64Encoder()
        self._escaper = ResourcePolicyIdUtil.getEscaper()
        self._converter = EntitlementConverter(None)

    def update_xacml_role_mapper(self, role_expressions_map):
        _method_name = 'update_xacml_role_mapper'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            # Determine the current ldift file name
            ldift_filename = File(self._domain_security_folder, WLS_XACML_ROLE_MAPPER_LDIFT_FILENAME).getPath()
            self.logger.finer('XACML role mapper file: {0}', ldift_filename, class_name=self.__class_name, method_name=_method_name)

            # Compile expression (needs more work)
            role_name = 'Admin'
            role_expression = role_expressions_map['Admin']
            policy = self._converter.convertRoleExpression(None, role_name, role_expression, None)
            role = self._escaper.escapeString(role_name)
            cn = self._escaper.escapeString(policy.getId().toString())
            xacml = self._b64encoder.encodeBuffer(String(policy.toString()).getBytes("UTF-8"))
            update_lines = ['\n']
            update_lines.append('dn: cn=' + cn + '+xacmlVersion=1.0,ou=Policies,ou=XACMLRole,ou=@realm@,dc=@domain@\n')
            update_lines.append('objectclass: top\n')
            update_lines.append('objectclass: xacmlEntry\n')
            update_lines.append('objectclass: xacmlRoleAssignmentPolicy\n')
            update_lines.append('cn: ' + cn + '\n')
            update_lines.append('xacmlVersion: 1.0\n')
            update_lines.append('xacmlStatus: 3\n')
            update_lines.append('xacmlDocument:: ' + xacml + '\n')
            update_lines.append('xacmlRole: ' + role + '\n')
            update_lines.append('\n')

            # Update the ldift file (needs more work)
            ldift_file = None
            update_file = None
            update_filename = ldift_filename + '.new'
            try:
                update_file = open(update_filename, 'w')
                ldift_file = open(ldift_filename)
                lines = ldift_file.readlines()
                update_file.writelines(lines)
                update_file.writelines(update_lines)
            finally:
                if ldift_file is not None:
                    ldift_file.close()
                if update_file is not None:
                    update_file.close()

            # Backup or remove the existing ldift file
            backup_filename = ldift_filename + '.bak'
            if not os.path.exists(backup_filename):
                self.logger.finer('Creating backup file: {0}', backup_filename, class_name=self.__class_name, method_name=_method_name)
                os.rename(ldift_filename, backup_filename)
            else:
                os.remove(ldift_filename)

            # Rename updated ldift file to the regular ldift file
            os.rename(update_filename, ldift_filename)

        except IOError, ioe:
            ex = exception_helper.create_exception(self._exception_type, 'IOError: {0}', str(ioe), error=ioe)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except OSError, ose:
            ex = exception_helper.create_exception(self._exception_type, 'OSError: {0}', str(ose), error=ose)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except DocumentParseException, dpe:
            ex = exception_helper.create_exception(self._exception_type, 'Failed to convert role expression {0} because {1}', role_expression, dpe.getLocalizedMessage(), error=dpe)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except URISyntaxException, use:
            ex = exception_helper.create_exception(self._exception_type, 'Failed to convert role expression {0} because {1}', role_expression, use.getLocalizedMessage(), error=use)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
