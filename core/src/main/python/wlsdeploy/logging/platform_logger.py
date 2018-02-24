"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import java.lang.System as JSystem
import java.lang.Thread as JThread
import java.lang.Throwable as Throwable
import java.util.ArrayList as JArrayList
import java.util.logging.Level as JLevel
import java.util.logging.Logger as JLogger
import java.util.logging.LogRecord as JLogRecord

import wlsdeploy.exception.exception_helper as exception_helper


class PlatformLogger(object):
    """
    A Python implementation of the platform logger wrapper around java.util.logging.Logger.
    """
    def __init__(self, logger_name, resource_bundle_name='oracle.weblogic.deploy.messages.wlsdeploy_rb'):
        self.name = logger_name
        self.resource_bundle_name = resource_bundle_name

        if resource_bundle_name is not None:
            self.logger = JLogger.getLogger(logger_name, resource_bundle_name)
        else:
            self.logger = JLogger.getLogger(logger_name)
        return

    def get_name(self):
        """
        Get the logger name.
        :return: the logger name
        """
        return self.logger.getName()

    def get_level(self):
        """
        Get the logging level.
        :return: the logging level
        """
        return self.logger.getLevel()

    def set_level(self, new_level):
        """
        Set the logging level.
        :param new_level: the new logging level
        """
        self.logger.setLevel(new_level)
        return

    def is_config_enabled(self):
        """
        Is config-level logging enabled?
        :return: True if config-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.CONFIG)

    def is_severe_enabled(self):
        """
        Is severe-level logging enabled?
        :return: True if severe-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.SEVERE)

    def is_warning_enabled(self):
        """
        Is warning-level logging enabled?
        :return: True if warning-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.WARNING)

    def is_info_enabled(self):
        """
        Is info-level logging enabled?
        :return: True if info-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.INFO)

    def is_fine_enabled(self):
        """
        Is fine-level logging enabled?
        :return: True if fine-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.FINE)

    def is_finer_enabled(self):
        """
        Is finer-level logging enabled?
        :return: True if finer-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.FINER)

    def is_finest_enabled(self):
        """
        Is finest-level logging enabled?
        :return: True if finest-level logging is enabled, False otherwise
        """
        return self.logger.isLoggable(JLevel.FINEST)

    def is_loggable(self, level):
        """
        Is the specified level logging enabled?
        :param level: the logging level to check
        :return: True if the specified logging level is enabled, False otherwise
        """
        return self.logger.isLoggable(level)

    def config(self, message, *args, **kwargs):
        """
        Log a config-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.CONFIG, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def log(self, level, message, *args, **kwargs):
        """
        Log a message at the specified level.
        :param level: the logging level
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(level, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def entering(self, *args, **kwargs):
        """
        Log an entering method message at the finer level.
        :param args: the method args
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        self.logger.entering(clazz, method, args)
        return

    def exiting(self, class_name, method_name, result=None):
        """
        Log an exiting method message at the finer level.
        :param class_name: the name of the python class of module
        :param method_name: the name of the method
        :param result: the method result, if any
        """
        if result is not None:
            self.logger.exiting(class_name, method_name, result)
        else:
            self.logger.exiting(class_name, method_name)
        return

    def fine(self, message, *args, **kwargs):
        """
        Log a fine-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.FINE, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def finer(self, message, *args, **kwargs):
        """
        Log a finer-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.FINER, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def finest(self, message, *args, **kwargs):
        """
        Log a finest-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.FINEST, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def info(self, message, *args, **kwargs):
        """
        Log an info-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.INFO, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def warning(self, message, *args, **kwargs):
        """
        Log a warning-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.WARNING, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def severe(self, message, *args, **kwargs):
        """
        Log a severe-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        record = self.__get_log_record(JLevel.SEVERE, clazz, method, message, error, *args)
        self.logger.log(record)
        return

    def throwing(self, error, method_name=None, class_name=None):
        """
        Log a throwing exception message at the finer level.
        :param error: the exception being thrown
        :param method_name: the method name where the exception is being created and thrown
        :param class_name: the Python class name or module name
        """
        if method_name is not None:
            self.logger.throwing(class_name, method_name, error)
        else:
            self.logger.throwing(error)
        return

    def __get_log_record(self, level, clazz, method, message, error, *args):
        record = JLogRecord(level, message)
        record.setLoggerName(self.name)
        record.setMillis(JSystem.currentTimeMillis())
        record.setParameters(_get_args_as_java_array(*args))
        if self.resource_bundle_name is not None:
            record.setResourceBundle(self.logger.getResourceBundle())
        if clazz is not None:
            record.setSourceClassName(clazz)
        if method is not None:
            record.setSourceMethodName(method)
        record.setThreadID(int(JThread.currentThread().getId()))
        if error is not None:
            if isinstance(error, Throwable):
                record.setThrown(error)
            else:
                ex = exception_helper.convert_error_to_exception()
                record.setThrown(ex)

        return record

def _get_args_as_java_array(*args):
    """
    Convert the Python args list into a Java array of strings.
    :param args: the args list
    :return: the Java array of strings
    """
    result = JArrayList()
    if args is not None and len(args) > 0:
        for arg in args:
            result.add(str(arg))
    return result.toArray()

