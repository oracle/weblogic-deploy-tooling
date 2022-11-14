"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from java.io import FileInputStream
from java.io import FileOutputStream
from java.io import IOException
from java.lang import IllegalArgumentException
from javax.xml.parsers import ParserConfigurationException

from oracle.weblogic.deploy.util import FileUtils
from org.xml.sax import SAXException

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ODL_CONFIGURATION
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper

_ADD_JVM_NUMBER = "AddJvmNumber"
_CLASS = "Class"
_ENCODING = "Encoding"
_ERROR_MANAGER = "ErrorManager"
_FILTER = "Filter"
_FORMATTER = "Formatter"
_HANDLER = "Handler"
_HANDLER_DEFAULTS = "HandlerDefaults"
_HANDLERS = "Handlers"
_LEVEL = "Level"
_LOGGER = "Logger"
_PROPERTIES = "Properties"
_SERVERS = "Servers"
_USE_PARENT_HANDLERS = "UseParentHandlers"

LOGGING_TEMPLATE_FILE = "logging-template.xml"


class OdlDeployer(object):
    """
    Handle the ODL validation and configuration.
    """
    __class_name = 'OdlHelper'

    def __init__(self, model, model_context, aliases, wlst_mode):
        self.model = model
        self.model_context = model_context
        self.aliases = aliases

        self.logger = PlatformLogger('wlsdeploy.deploy')
        self.wlst_mode = wlst_mode

    def configure_odl(self, parent_dict, parent_location):
        """
        Apply the ODL configuration section of the model, if present.
        :param parent_dict: the model dictionary that may contains ODL configuration
        :param parent_location: the alias location of the parent dictionary (used for logging paths)
        """
        _method_name = 'configure_odl'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        odl_info = dictionary_utils.get_dictionary_element(parent_dict, ODL_CONFIGURATION)
        if len(odl_info):
            typedef = self.model_context.get_domain_typedef()
            if not (typedef.is_jrf_domain_type() or typedef.is_restricted_jrf_domain_type()):
                self.logger.info('WLSDPLY-19709', class_name=self.__class_name, method_name=_method_name)
            elif self.wlst_mode == WlstModes.ONLINE:
                self.logger.info('WLSDPLY-19700', class_name=self.__class_name, method_name=_method_name)
            else:
                for config in odl_info:
                    self._update_config(config, odl_info[config], parent_location)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def _update_config(self, config_name, config_dictionary, parent_location):
        _method_name = '_update_config'

        config_location = LocationContext(parent_location).append_location(ODL_CONFIGURATION)
        token = self.aliases.get_name_token(config_location)
        config_location.add_name_token(token, config_name)

        servers = dictionary_utils.get_element(config_dictionary, _SERVERS)
        if servers is not None:
            servers_list = alias_utils.convert_to_type('list', servers, delimiter=MODEL_LIST_DELIMITER)
            for server in servers_list:
                self.logger.info('WLSDPLY-19708', ODL_CONFIGURATION, config_name, server,
                                 class_name=self.__class_name, method_name=_method_name)
                self._update_server(server, config_dictionary, config_location)

    def _update_server(self, name, dictionary, config_location):
        _method_name = '_update_server'

        # these imports are local, since they are only present in JRF environments.
        # this method is only called after that check has been made.
        from oracle.core.ojdl.weblogic.ODLConfiguration import CONFIG_DIR
        from oracle.core.ojdl.weblogic.ODLConfiguration import CONFIG_FILE
        from oracle.core.ojdl.logging.config import LoggingConfigurationDocument

        config_dir = File(self.model_context.get_domain_home(), CONFIG_DIR)
        server_dir = File(config_dir, name)
        config_file = File(server_dir, CONFIG_FILE)
        log_template_dir = config_dir.getParentFile()

        try:
            if config_file.exists():
                source_file = config_file
                FileUtils.validateWritableFile(config_file.getPath())
            else:
                # for dynamic servers, the logging config does not exist until the server is started.
                # read the from template file, verify that the server directory is present and writable.
                source_file = File(log_template_dir, LOGGING_TEMPLATE_FILE)
                FileUtils.validateExistingFile(source_file)
                if not server_dir.exists() and not server_dir.mkdirs():
                    ex = exception_helper.create_deploy_exception('WLSDPLY-19710', server_dir)
                    self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex
                FileUtils.validateWritableDirectory(server_dir.getPath())

            document = LoggingConfigurationDocument(FileInputStream(source_file))

            # configure AddJvmNumber
            add_jvm_number = dictionary_utils.get_element(dictionary, _ADD_JVM_NUMBER)
            if add_jvm_number is not None:
                document.setAddJvmNumber(alias_utils.convert_boolean(add_jvm_number))

            # configure HandlerDefaults
            handler_defaults = dictionary_utils.get_dictionary_element(dictionary, _HANDLER_DEFAULTS)
            if handler_defaults is not None:
                for key in handler_defaults:
                    value = handler_defaults[key]
                    document.setHandlerDefault(key, _get_property_text(value))

            # configure Handlers
            # do these before loggers, in case new handlers are assigned to loggers
            existing_handler_names = document.getHandlerNames()
            handlers = dictionary_utils.get_dictionary_element(dictionary, _HANDLER)
            if handlers is not None:
                for handler_name in handlers:
                    handler = handlers[handler_name]
                    self._configure_handler(handler_name, handler, document, existing_handler_names, config_location)

            # configure Loggers
            existing_logger_names = document.getLoggerNames()
            loggers = dictionary_utils.get_dictionary_element(dictionary, _LOGGER)
            if loggers is not None:
                for logger_name in loggers:
                    logger = loggers[logger_name]
                    self._configure_logger(logger_name, logger, document, existing_logger_names, config_location)

            document.writeDocument(FileOutputStream(config_file))

        except (ParserConfigurationException, SAXException, IOException, IllegalArgumentException), ex:
            self.logger.severe('WLSDPLY-19707', name, ex.getLocalizedMessage(),
                               class_name=self.__class_name, method_name=_method_name)
        return

    def _configure_handler(self, handler_name, handler, document, existing_names, config_location):
        """
        Configure the specified handler in the document.
        The handler will be added if it is not currently in the document.
        :param handler_name: the name of the handler to be configured
        :param handler: the dictionary of the handler to be configured
        :param document: the document to be updated
        :param existing_names: the names of existing handlers
        :param config_location: the location of ODL configuration in the model
        """
        _method_name = '_configure_handler'

        handler_location = LocationContext(config_location).append_location(_HANDLER)
        token = self.aliases.get_name_token(handler_location)
        handler_location.add_name_token(token, handler_name)
        handler_path = self.aliases.get_model_folder_path(handler_location)

        handler_class = dictionary_utils.get_element(handler, _CLASS)

        if handler_name not in existing_names:
            # new handlers must have a class specified.
            # we can't determine if a handler is new or existing during validation.
            if handler_class is None:
                self.logger.severe('WLSDPLY-19701', handler_name, handler_path,
                                   class_name=self.__class_name, method_name=_method_name)
                return
            try:
                document.addHandler(handler_name, str_helper.to_string(handler_class))
            except IllegalArgumentException, iae:
                self.logger.severe('WLSDPLY-19702', handler_name, handler_path, iae.getLocalizedMessage(),
                                   class_name=self.__class_name, method_name=_method_name)

        elif handler_class is not None:
            try:
                document.setHandlerClass(handler_name, str_helper.to_string(handler_class))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_CLASS, handler_class, iae, _method_name, handler_path)

        level = dictionary_utils.get_element(handler, _LEVEL)
        if level is not None:
            try:
                document.setHandlerLevel(handler_name, str_helper.to_string(level))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_LEVEL, level, iae, _method_name, handler_path)

        error_manager = dictionary_utils.get_element(handler, _ERROR_MANAGER)
        if error_manager is not None:
            try:
                document.setHandlerErrorManager(handler_name, str_helper.to_string(error_manager))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_ERROR_MANAGER, error_manager, iae, _method_name, handler_path)

        handler_filter = dictionary_utils.get_element(handler, _FILTER)
        if handler_filter is not None:
            try:
                document.setHandlerFilter(handler_name, str_helper.to_string(handler_filter))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_FILTER, level, iae, _method_name, handler_path)

        formatter = dictionary_utils.get_element(handler_filter, _FORMATTER)
        if formatter is not None:
            try:
                document.setHandlerFormatter(handler_name, str_helper.to_string(formatter))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_FORMATTER, formatter, iae, _method_name, handler_path)

        encoding = dictionary_utils.get_element(handler, _ENCODING)
        if encoding is not None:
            try:
                document.setHandlerEncoding(handler_name, str_helper.to_string(encoding))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_ENCODING, encoding, iae, _method_name, handler_path)

        properties = dictionary_utils.get_dictionary_element(handler, _PROPERTIES)
        for key in properties:
            value = properties[key]
            property_text = _get_property_text(value)
            try:
                document.setHandlerProperty(handler_name, key, property_text)
            except IllegalArgumentException, iae:
                self.logger.severe('WLSDPLY-19706', key, property_text, handler_path, iae.getLocalizedMessage(),
                                   class_name=self.__class_name, method_name=_method_name)

    def _configure_logger(self, logger_name, logger, document, existing_names, config_location):
        """
        Configure the specified logger in the document.
        The logger will be added if it is not currently in the document.
        :param logger_name: the name of the logger to be configured
        :param logger: the dictionary of the logger to be configured
        :param document: the document to be updated
        :param existing_names: the names of existing loggers
        :param config_location: the location of ODL configuration in the model
        """
        _method_name = '_configure_logger'

        logger_location = LocationContext(config_location).append_location(_LOGGER)
        token = self.aliases.get_name_token(logger_location)
        logger_location.add_name_token(token, logger_name)
        logger_path = self.aliases.get_model_folder_path(logger_location)

        if logger_name not in existing_names:
            try:
                document.addLogger(logger_name)
            except IllegalArgumentException, iae:
                self.logger.severe('WLSDPLY-19704', logger_name, logger_path, iae.getLocalizedMessage(),
                                   class_name=self.__class_name, method_name=_method_name)

        level = dictionary_utils.get_element(logger, _LEVEL)
        if level is not None:
            try:
                document.setLoggerLevel(logger_name, str_helper.to_string(level))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_LEVEL, level, iae, _method_name, logger_path)

        logger_filter = dictionary_utils.get_element(logger, _FILTER)
        if logger_filter is not None:
            try:
                document.setLoggerFilter(logger_name, str_helper.to_string(logger_filter))
            except IllegalArgumentException, iae:
                self._log_invalid_set(_FILTER, logger_filter, iae, _method_name, logger_path)

        use_parent_handlers = dictionary_utils.get_element(logger, _USE_PARENT_HANDLERS)
        if use_parent_handlers is not None:
            value = alias_utils.convert_boolean(use_parent_handlers)
            try:
                document.setLoggerUseParentHandlers(logger_name, value)
            except IllegalArgumentException, iae:
                self._log_invalid_set(_USE_PARENT_HANDLERS, value, iae, _method_name, logger_path)

        assigned_handlers = document.getLoggerHandlers(logger_name)

        logger_handlers = dictionary_utils.get_element(logger, _HANDLERS)
        if logger_handlers is not None:
            handlers_list = alias_utils.convert_to_type('list', logger_handlers, delimiter=MODEL_LIST_DELIMITER)
            for logger_handler in handlers_list:
                if logger_handler not in assigned_handlers:
                    try:
                        document.addHandlerToLogger(logger_name, logger_handler)
                    except IllegalArgumentException, iae:
                        self.logger.severe('WLSDPLY-19705', logger_handler, logger_name, logger_path,
                                           iae.getLocalizedMessage(), class_name=self.__class_name,
                                           method_name=_method_name)

    def _log_invalid_set(self, key, value, exception, method_name, model_path):
        """
        Log a message at the severe level indicating that a value cannot be assigned to the specified key.
        :param key: the key being assigned
        :param value: the value to be set
        :param exception: the exception from the failure
        :param method_name: the name of the calling method
        :param model_path: the path of the key in the model
        """
        self.logger.severe('WLSDPLY-19703', key, value, model_path, exception.getLocalizedMessage(),
                           class_name=self.__class_name, method_name=method_name)


def _get_property_text(value):
    """
    Return the text for the specified property value.
    Some of these may require special processing.
    :param value: the value to be evaluated
    :return: the corresponding text value
    """
    return str_helper.to_string(value)
