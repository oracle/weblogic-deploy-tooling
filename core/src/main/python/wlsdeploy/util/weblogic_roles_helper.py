"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from java.io import File
from java.lang import String
from wlsdeploy.exception import exception_helper
import wlsdeploy.util.unicode_helper as str_helper

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
        role_entries_map = self._create_xacml_role_mapper_entries(role_expressions_map)
        self._update_xacml_role_mapper_ldift(role_entries_map)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _create_xacml_role_mapper_entries(self, role_expressions_map):
        _method_name = '_create_xacml_role_mapper_entries'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        entries = {}
        if role_expressions_map is not None:
            try:
                for role_name in role_expressions_map.keys():
                    # Get the role expression
                    role_expression = role_expressions_map[role_name]
                    # Convert the role expression
                    policy = self._converter.convertRoleExpression(None, role_name, role_expression, None)
                    role = self._escaper.escapeString(role_name)
                    cn = self._escaper.escapeString(policy.getId().toString())
                    xacml = self._b64encoder.encodeBuffer(String(policy.toString()).getBytes("UTF-8"))
                    # Setup the lines that make up the role entry
                    entry = []
                    entry.append('dn: cn=' + cn + '+xacmlVersion=1.0,ou=Policies,ou=XACMLRole,ou=@realm@,dc=@domain@\n')
                    entry.append('objectclass: top\n')
                    entry.append('objectclass: xacmlEntry\n')
                    entry.append('objectclass: xacmlRoleAssignmentPolicy\n')
                    entry.append('cn: ' + cn + '\n')
                    entry.append('xacmlVersion: 1.0\n')
                    entry.append('xacmlStatus: 3\n')
                    entry.append('xacmlDocument:: ' + xacml + '\n')
                    entry.append('xacmlRole: ' + role + '\n')
                    entry.append('\n')
                    # Add to the map of role entries
                    entries[role] = entry

            except DocumentParseException, dpe:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-01804', role_name, role_expression, dpe.getLocalizedMessage(), error=dpe)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
            except URISyntaxException, use:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-01804', role_name, role_expression, use.getLocalizedMessage(), error=use)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return entries

    def _update_xacml_role_mapper_ldift(self, role_entries_map):
        _method_name = '_update_xacml_role_mapper_ldift'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            # Determine the current XACML ldift file name
            ldift_filename = File(self._domain_security_folder, WLS_XACML_ROLE_MAPPER_LDIFT_FILENAME).getPath()
            self.logger.finer('WLSDPLY-01800', ldift_filename, class_name=self.__class_name, method_name=_method_name)

            # Update the XACML ldift file
            ldift_file = None
            update_file = None
            update_filename = ldift_filename + '.new'
            try:
                update_file = open(update_filename, 'w')
                ldift_file = open(ldift_filename)
                # Look for existing entries to be replaced
                for line in ldift_file:
                    if line.startswith('dn: cn='):
                        role_entry_lines = self.__read_xacml_role_entry(line, ldift_file)
                        role_name = self.__get_xacml_role_entry_name(role_entry_lines)
                        if role_name in role_entries_map:
                            self.logger.finer('WLSDPLY-01802', role_name, class_name=self.__class_name, method_name=_method_name)
                            update_file.writelines(role_entries_map[role_name])
                            del role_entries_map[role_name]
                        else:
                            update_file.writelines(role_entry_lines)
                    else:
                        update_file.write(line)
                # Append any remaining entries
                role_names = role_entries_map.keys()
                self.logger.finer('WLSDPLY-01803', role_names, class_name=self.__class_name, method_name=_method_name)
                for role_name in role_names:
                    update_file.write('\n')
                    update_file.writelines(role_entries_map[role_name])
            finally:
                if ldift_file is not None:
                    ldift_file.close()
                if update_file is not None:
                    update_file.close()

            # Backup or remove the existing ldift file
            backup_filename = ldift_filename + '.bak'
            if not os.path.exists(backup_filename):
                self.logger.finer('WLSDPLY-01801', backup_filename, class_name=self.__class_name, method_name=_method_name)
                os.rename(ldift_filename, backup_filename)
            else:
                os.remove(ldift_filename)

            # Rename updated ldift file to the regular ldift file
            os.rename(update_filename, ldift_filename)

        except ValueError, ve:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-01805', 'ValueError',
                                                   str_helper.to_string(ve), error=ve)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except IOError, ioe:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-01805', 'IOError',
                                                   str_helper.to_string(ioe), error=ioe)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except OSError, ose:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-01805', 'OSError',
                                                   str_helper.to_string(ose), error=ose)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __read_xacml_role_entry(self, start_line, ldift_file):
        count = 1
        lines = [start_line]
        for line in ldift_file:
            count += 1
            lines.append(line)
            if count == 10:
                break

        if len(lines) != 10:
            raise ValueError('Error reading XACML role entry!')

        if not lines[-2].startswith('xacmlRole: '):
            raise ValueError('Unable to find XACML role entry!')

        return lines

    def __get_xacml_role_entry_name(self, role_entry_lines):
        role_name_entry = role_entry_lines[-2]
        role_name = role_name_entry[10:]
        return role_name.strip()
