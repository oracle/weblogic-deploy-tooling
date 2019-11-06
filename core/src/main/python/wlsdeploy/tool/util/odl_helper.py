"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File, FileOutputStream
from java.io import FileInputStream

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER, ODL_INFO
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.util import dictionary_utils

from oracle.core.ojdl.weblogic.ODLConfiguration import CONFIG_DIR
from oracle.core.ojdl.weblogic.ODLConfiguration import CONFIG_FILE
from oracle.core.ojdl.logging.config import LoggingConfigurationDocument

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
_USE_PARENT_HANDLERS = "UseParentHandlers"

_VALID_TOP_FIELDS = [
    _ADD_JVM_NUMBER,
    _HANDLER,
    _HANDLER_DEFAULTS,
    _LOGGER
]

_VALID_HANDLER_FIELDS = [
    _CLASS,
    _ENCODING,
    _ERROR_MANAGER,
    _FILTER,
    _FORMATTER,
    _LEVEL,
    _PROPERTIES
]

_VALID_LOGGER_FIELDS = [
    _FILTER,
    _HANDLERS,
    _LEVEL,
    _USE_PARENT_HANDLERS
]


class OdlHelper(object):
    """
    Handle the ODL validation and configuration.
    """
    __class_name = 'OdlHelper'

    def __init__(self, model, model_context, wlst_mode, exception_type, logger):
        self.logger = logger
        self.model = model
        self.model_context = model_context
        self.wlst_mode = wlst_mode
        self.exception_type = exception_type
        self.logger = logger

    def configure_odl(self):
        """
        Apply the ODL configuration section of the model.
        """
        _method_name = 'configure_odl'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        odl_info = self.model.get_model_odl_info()
        if len(odl_info):
            if self.wlst_mode == WlstModes.ONLINE:
                self.logger.info('WLSDPLY-19700', class_name=self.__class_name, method_name=_method_name)
            else:
                for server in odl_info:
                    self.update_server(server, odl_info[server])

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def update_server(self, name, dictionary):
        config_dir = File(self.model_context.get_domain_home(), CONFIG_DIR)
        server_dir = File(config_dir, name)
        config_file = File(server_dir, CONFIG_FILE)

        document = LoggingConfigurationDocument(FileInputStream(config_file))

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

                if handler_name not in existing_handler_names:
                    document.addHandler(handler_name, "my.class.Handler")

                handler_class = dictionary_utils.get_element(handler, _CLASS)
                if handler_class is not None:
                    document.setHandlerClass(handler_name, str(handler_class))

                level = dictionary_utils.get_element(handler, _LEVEL)
                if level is not None:
                    document.setHandlerLevel(handler_name, str(level))

                error_manager = dictionary_utils.get_element(handler, _ERROR_MANAGER)
                if error_manager is not None:
                    document.setHandlerErrorManager(handler_name, str(error_manager))

                handler_filter = dictionary_utils.get_element(handler, _FILTER)
                if handler_filter is not None:
                    document.setHandlerFilter(handler_name, str(handler_filter))

                formatter = dictionary_utils.get_element(handler, _FORMATTER)
                if formatter is not None:
                    document.setHandlerFormatter(handler_name, str(formatter))

                encoding = dictionary_utils.get_element(handler, _ENCODING)
                if encoding is not None:
                    document.setHandlerEncoding(handler_name, str(encoding))

                properties = dictionary_utils.get_dictionary_element(handler, _PROPERTIES)
                for key in properties:
                    value = properties[key]
                    document.setHandlerProperty(handler_name, key, _get_property_text(value))

        # configure Loggers
        existing_logger_names = document.getLoggerNames()

        loggers = dictionary_utils.get_dictionary_element(dictionary, _LOGGER)
        if loggers is not None:
            for logger_name in loggers:
                logger = loggers[logger_name]

                if logger_name not in existing_logger_names:
                    document.addLogger(logger_name)

                level = dictionary_utils.get_element(logger, _LEVEL)
                if level is not None:
                    document.setLoggerLevel(logger_name, str(level))

                logger_filter = dictionary_utils.get_element(logger, _FILTER)
                if logger_filter is not None:
                    document.setLoggerFilter(logger_name, str(logger_filter))

                use_parent_handlers = dictionary_utils.get_element(logger, _USE_PARENT_HANDLERS)
                if use_parent_handlers is not None:
                    document.setLoggerUseParentHandlers(logger_name, alias_utils.convert_boolean(use_parent_handlers))

                assigned_handlers = document.getLoggerHandlers(logger_name)

                logger_handlers = dictionary_utils.get_element(logger, _HANDLERS)
                if logger_handlers is not None:
                    handlers_list = alias_utils.convert_to_type('list', logger_handlers,
                                                                delimiter=MODEL_LIST_DELIMITER)
                    for logger_handler in handlers_list:
                        if logger_handler not in assigned_handlers:
                            document.addHandlerToLogger(logger_name, logger_handler)

        document.writeDocument(FileOutputStream(config_file))

    def validate_odl(self):
        """
        Validate the ODL configuration section of the model.
        Because ODL structure is not alias-based, alias log messages are built manually,
        and model path is constructed to match topology:/Server/m2 format.
        """
        _method_name = 'validate_odl'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        odl_info = self.model.get_model_odl_info()
        if self._check_dict(ODL_INFO, odl_info, "<root>"):
            for server_name in odl_info:
                server = odl_info[server_name]
                server_path = ODL_INFO + ":/" + server_name
                self._check_fields(server, _VALID_TOP_FIELDS, server_path)

                handlers = dictionary_utils.get_dictionary_element(server, _HANDLER)
                if self._check_dict(_HANDLER, handlers, server_path):
                    for handler_name in handlers:
                        handler = handlers[handler_name]
                        handler_path = server_path + "/" + _HANDLER + "/" + handler_name
                        self._check_fields(handler, _VALID_HANDLER_FIELDS, handler_path)

                loggers = dictionary_utils.get_dictionary_element(server, _LOGGER)
                if self._check_dict(_LOGGER, loggers, server_path):
                    for logger_name in loggers:
                        logger = loggers[logger_name]
                        logger_path = server_path + "/" + _LOGGER + "/" + logger_name
                        self._check_fields(logger, _VALID_LOGGER_FIELDS, logger_path)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def _check_dict(self, key, value, model_folder_path):
        """
        Determine if the specified value is a dictionary type.
        If it is not, log an error and return False.
        :param key: the key used for logging
        :param value: the value to be checked
        :param model_folder_path: the model path used for logging
        :return: True if the value is a dictionary, False otherwise
        """
        _method_name = '_check_dict'

        if not isinstance(value, dict):
            self.logger.severe('WLSDPLY-05032', key, model_folder_path, str(type(value)),
                               class_name=self.__class_name, method_name=_method_name)
            return False

        return True

    def _check_fields(self, dictionary, valid_fields, model_folder_path):
        """
        Check that all the keys in the dictionary object are in the valid fields list.
        If an invalid field is found, log errors matching those in alias framework.
        :param dictionary: the dictionary to be checked
        :param valid_fields: a list of valid field names
        :param model_folder_path: a path describing the model location
        """
        _method_name = '_check_fields'

        for field in dictionary:
            if field not in valid_fields:
                value = dictionary[field]
                if isinstance(value, dict):
                    self.logger.severe('WLSDPLY-05026', field, 'folder', model_folder_path,
                                       class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.severe('WLSDPLY-05029', field, model_folder_path,
                                       class_name=self.__class_name, method_name=_method_name)


def validate(model, model_context, wlst_mode, exception_type, logger):
    helper = OdlHelper(model, model_context, wlst_mode, exception_type, logger)
    helper.validate_odl()


def configure(model, model_context, wlst_mode, exception_type, logger):
    helper = OdlHelper(model, model_context, wlst_mode, exception_type, logger)
    helper.configure_odl()


def _get_property_text(item):
    return str(item)
