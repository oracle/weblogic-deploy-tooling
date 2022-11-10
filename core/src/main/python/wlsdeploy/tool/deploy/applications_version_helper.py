"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from java.io import File
from java.io import FileInputStream
from java.io import FileNotFoundException
from java.io import IOException
from java.lang import IllegalStateException
from java.util.jar import JarFile
from java.util.jar import Manifest
from java.util.jar.Attributes.Name import EXTENSION_NAME
from java.util.jar.Attributes.Name import IMPLEMENTATION_VERSION
from java.util.jar.Attributes.Name import SPECIFICATION_VERSION
from java.util.jar.JarFile import MANIFEST_NAME
from java.util.zip import ZipException

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper


class ApplicationsVersionHelper(object):
    _EXTENSION_INDEX = 0
    _SPEC_INDEX = 1
    _IMPL_INDEX = 2

    _APP_VERSION_MANIFEST_KEY = 'Weblogic-Application-Version'

    def __init__(self, model_context, archive_helper):
        self._class_name = 'ApplicationsVersionHelper'
        self.model_context = model_context
        self.archive_helper = archive_helper
        self.logger = PlatformLogger('wlsdeploy.deploy')

    def get_library_versioned_name(self, source_path, model_name, from_archive=False):
        """
        Get the proper name of the deployable library that WLST requires in the target domain.  This method is
        primarily needed for shared libraries in the Oracle Home where the implementation version may have
        changed.  Rather than requiring the modeller to have to know/adjust the shared library name, we extract
        the information from the target domain's archive file (e.g., war file) and compute the correct name.
        :param source_path: the SourcePath value of the shared library
        :param model_name: the model name of the library
        :param from_archive: if True, use the manifest from the archive, otherwise from the file system
        :return: the updated shared library name for the target environment
        :raises: DeployException: if an error occurs
        """
        _method_name = 'get_library_versioned_name'

        self.logger.entering(source_path, model_name, class_name=self._class_name, method_name=_method_name)

        old_name_tuple = deployer_utils.get_library_name_components(model_name)
        try:
            versioned_name = old_name_tuple[self._EXTENSION_INDEX]
            manifest = self.__get_manifest(source_path, from_archive)
            if manifest is not None:
                attributes = manifest.getMainAttributes()

                extension_name = attributes.getValue(EXTENSION_NAME)
                if not string_utils.is_empty(extension_name):
                    versioned_name = extension_name

                specification_version = attributes.getValue(SPECIFICATION_VERSION)
                if not string_utils.is_empty(specification_version):
                    versioned_name += '#' + specification_version

                    # Cannot specify an impl version without a spec version
                    implementation_version = attributes.getValue(IMPLEMENTATION_VERSION)
                    if not string_utils.is_empty(implementation_version):
                        versioned_name += '@' + implementation_version

                self.logger.info('WLSDPLY-09324', model_name, versioned_name,
                                 class_name=self._class_name, method_name=_method_name)

        except (IOException, FileNotFoundException, ZipException, IllegalStateException), e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09325', model_name, source_path,
                                                          str_helper.to_string(e), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=versioned_name)
        return versioned_name

    def get_application_versioned_name(self, source_path, model_name, from_archive=False, module_type=None):
        """
        Get the proper name of the deployable application that WLST requires in the target domain.
        This method is needed for the case where the application is explicitly versioned in its ear/war manifest.
        Rather than requiring the modeller to have to know/adjust the application name, we extract
        the information from the application's archive file (e.g., war file) and compute the correct name.
        :param source_path: the SourcePath value of the application
        :param model_name: the model name of the application
        :param from_archive: if True, use the manifest from the archive, otherwise from the file system
        :return: the updated application name for the target environment
        :raises: DeployException: if an error occurs
        """
        _method_name = 'get_application_versioned_name'

        self.logger.entering(source_path, model_name, class_name=self._class_name, method_name=_method_name)

        # if no manifest version is found, leave the original name unchanged
        versioned_name = model_name
        if self.is_module_type_app_module(module_type):
            return model_name

        try:
            manifest = self.__get_manifest(source_path, from_archive)

            if manifest is not None:
                attributes = manifest.getMainAttributes()
                application_version = attributes.getValue(self._APP_VERSION_MANIFEST_KEY)
                if application_version is not None:
                    # replace any version information in the model name
                    model_name_tuple = deployer_utils.get_library_name_components(model_name)
                    versioned_name = model_name_tuple[self._EXTENSION_INDEX]
                    versioned_name = versioned_name + '#' + application_version
                    self.logger.info('WLSDPLY-09328', model_name, versioned_name, class_name=self._class_name,
                                     method_name=_method_name)

        except (IOException, FileNotFoundException, ZipException, IllegalStateException), e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09329', model_name, source_path,
                                                          str_helper.to_string(e), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=versioned_name)
        return versioned_name

    def is_module_type_app_module(self, module_type):
        if module_type in [ 'jms', 'jdbc', 'wldf']:
            return True
        else:
            return False

    def __get_manifest(self, source_path, from_archive):
        """
        Returns the manifest object for the specified path.
        The source path may be a jar, or an exploded path.
        :param source_path: the source path to be checked
        :param from_archive: if True, use the manifest from the archive, otherwise from the file system
        :return: the manifest, or None if it is not present
        :raises: IOException: if there are problems reading an existing manifest
        """
        manifest = None
        if string_utils.is_empty(source_path):
            return manifest

        source_path = self.model_context.replace_token_string(source_path)

        if from_archive and deployer_utils.is_path_into_archive(source_path):
            return self.archive_helper.get_manifest(source_path)

        else:
            if not os.path.isabs(source_path):
                # if this was in archive, it has been expanded under domain home.
                # or it may be a relative file intentionally placed under domain home.
                source_file = File(File(self.model_context.get_domain_home()), source_path)
            else:
                source_file = File(source_path)

            if source_file.isDirectory():
                # read the manifest directly from the file system
                manifest_file = File(source_file, MANIFEST_NAME)
                if manifest_file.exists():
                    stream = None
                    try:
                        stream = FileInputStream(manifest_file)
                        manifest = Manifest(stream)
                    finally:
                        if stream is not None:
                            try:
                                stream.close()
                            except IOException:
                                # nothing to report
                                pass
            else:
                # read the manifest from the deployable ear/jar/war on the file system
                archive = JarFile(source_file.getAbsolutePath())
                manifest = archive.getManifest()

        return manifest
