"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import java.lang.System as JSystem
import java.lang.Thread as JThread
import java.util.logging.Level as JLevel
import java.util.logging.Logger as JLogger
import java.util.logging.LogRecord as JLogRecord

from oracle.weblogic.deploy.exception import ExceptionHelper

from wlsdeploy.util import model
from wlsdeploy.tool.validate import validation_utils


class ValidationResults(object):
    """
    Class for logging and printing out validation results

    """
    _class_name = 'ValidationResults'

    def __init__(self):
        self._validation_result_dict = {
            '%s Section' % model.get_model_domain_info_key(): None,
            '%s Section' % model.get_model_topology_key(): None,
            '%s Section' % model.get_model_deployments_key(): None,
            '%s Section' % model.get_model_resources_key(): None
        }

    def __str__(self):
        return self.__to_string()

    def set_validation_result(self, validation_result):
        self._validation_result_dict[validation_result.get_validation_area()] = validation_result

    def get_errors_count(self):
        """

        :return:
        """
        results_summary = self.__get_summary()
        return results_summary['errors_count']

    def get_warnings_count(self):
        """

        :return:
        """
        results_summary = self.__get_summary()
        return results_summary['warnings_count']

    def get_infos_count(self):
        """

        :return:
        """
        results_summary = self.__get_summary()
        return results_summary['infos_count']

    def print_details(self):
        """

        :return:
        """

        results_summary = self.__get_summary()

        message_count = results_summary['infos_count']
        if message_count > 0:
            indent_level = 0
            validation_utils.print_blank_lines()
            validation_utils.print_indent('%s: %d' % (validation_utils.format_message('WLSDPLY-05201'),
                                                      message_count), indent_level + 1)
            for validation_result in self._validation_result_dict.values():
                _print_results_category_details(validation_result.get_infos_messages(), indent_level)

        message_count = results_summary['warnings_count']
        if message_count > 0:
            indent_level = 0
            validation_utils.print_blank_lines()
            validation_utils.print_indent('%s: %d' % (validation_utils.format_message('WLSDPLY-05202'),
                                                      message_count), indent_level + 1)
            for validation_result in self._validation_result_dict.values():
                _print_results_category_details(validation_result.get_warnings_messages(), indent_level)

        message_count = results_summary['errors_count']
        if message_count > 0:
            indent_level = 0
            validation_utils.print_blank_lines()
            validation_utils.print_indent('%s: %d' % (validation_utils.format_message('WLSDPLY-05203'),
                                                      message_count), indent_level + 1)
            for validation_result in self._validation_result_dict.values():
                _print_results_category_details(validation_result.get_errors_messages(), indent_level)

    def log_results(self, logger):
        """

        :return:
        """
        _method_name = 'log_results'

        if logger is not None:
            # Get counts for all the ValidationResult objects
            # in this ValidationResults object
            results_summary = self.__get_summary()

            jlogger = JLogger.getLogger(logger.get_name(), logger.resource_bundle_name)

            jlogger.setLevel(JLevel.INFO)

            # Determine what the severity level is going to be for the
            # summary log message. Needs to be set in accordance with
            # what the severest validation message was.
            if results_summary['infos_count'] > 0:
                jlogger.setLevel(JLevel.INFO)
            if results_summary['warnings_count'] > 0:
                jlogger.setLevel(JLevel.WARNING)
            if results_summary['errors_count'] > 0:
                jlogger.setLevel(JLevel.SEVERE)

            total_messages_count = \
                int(results_summary['errors_count']) + int(results_summary['warnings_count']) + \
                int(results_summary['infos_count'])

            logger.log(jlogger.getLevel(),
                       'WLSDPLY-05204',
                       results_summary['errors_count'],
                       results_summary['warnings_count'],
                       results_summary['infos_count'],
                       class_name=self._class_name, method_name=_method_name)

            if total_messages_count > 0:
                logger.log(jlogger.getLevel(), 'WLSDPLY-05207', total_messages_count,
                           class_name=self._class_name, method_name=_method_name)

            for validation_result in self._validation_result_dict.values():
                if validation_result.get_infos_count() > 0:
                    jlogger.setLevel(JLevel.INFO)
                    self.__log_results_category_details(validation_result.get_infos_messages(),
                                                        _method_name, jlogger)

            for validation_result in self._validation_result_dict.values():
                if validation_result.get_warnings_count() > 0:
                    jlogger.setLevel(JLevel.WARNING)
                    self.__log_results_category_details(validation_result.get_warnings_messages(),
                                                        _method_name, jlogger)

            for validation_result in self._validation_result_dict.values():
                if validation_result.get_errors_count() > 0:
                    jlogger.setLevel(JLevel.SEVERE)
                    self.__log_results_category_details(validation_result.get_errors_messages(),
                                                        _method_name, jlogger)

            jlogger.setLevel(JLevel.INFO)

        return

    def __log_results_category_details(self, category_messages, method_name, jlogger):
        """

        :param category_messages:
        :param method_name:
        :param jlogger:
        :return:
        """

        for i in range(len(category_messages)):
            messages = category_messages[i]
            _log_category_message(jlogger, messages['resource_id'], messages['args'],
                                  class_name=self._class_name, method_name=method_name)

    def __get_summary(self):
        """

        :return:
        """

        results_summary = {
            'errors_count': 0,
            'warnings_count': 0,
            'infos_count': 0
        }

        for validation_result in self._validation_result_dict.values():
            if validation_result is not None:
                results_summary['errors_count'] += validation_result.get_errors_count()
                results_summary['warnings_count'] += validation_result.get_warnings_count()
                results_summary['infos_count'] += validation_result.get_infos_count()

        return results_summary

    def __to_string(self):
        """

        :return:
        """

        tmp = ''

        for validation_result in self._validation_result_dict.values():
            if validation_result.get_errors_count() > 0 \
                    or validation_result.get_warnings_count() > 0 \
                    or validation_result.get_infos_count():
                tmp += str(validation_result)
                tmp += ','

        if tmp[-1:] == ',':
            # Strip off trailing ','
            tmp = tmp[:-1]

        return '[%s]' % tmp


def _print_results_category_details(category_messages, indent_level):
    """

    :param category_messages:
    :param indent_level:
    :return:
    """
    for i in range(len(category_messages)):
        messages = category_messages[i]
        validation_utils.print_indent(
            ExceptionHelper.getMessage(messages['resource_id'], list(messages['args'])), indent_level + 2
        )

    return


def _log_category_message(jlogger, message, *args, **kwargs):
    method = kwargs.get('method_name', None)
    clazz = kwargs.get('class_name', None)
    record = JLogRecord(jlogger.getLevel(), message)
    record.setLoggerName(jlogger.getName())
    record.setMillis(JSystem.currentTimeMillis())
    record.setParameters(list(*args))
    record.setResourceBundle(jlogger.getResourceBundle())
    if clazz is not None:
        record.setSourceClassName(clazz)
    if method is not None:
        record.setSourceMethodName(method)
    record.setThreadID(int(JThread.currentThread().getId()))
    jlogger.log(record)
    return


class ValidationResult(object):
    """
    Class for capturing validation results
    """
    def __init__(self, validation_area):
        self._result = {
            "validation_area": validation_area,
            "errors": {
                "count": 0,
                "messages": []
            },
            "warnings": {
                "count": 0,
                "messages": []
            },
            "infos": {
                "count": 0,
                "messages": []
            }
        }

    def __str__(self):
        tmp = '"validation_area": "%s",' % self._result['validation_area']
        if self.get_errors_count() > 0:
            tmp += self.__to_string('errors')
        if self.get_warnings_count() > 0:
            tmp += self.__to_string('warnings')
        if self.get_infos_count() > 0:
            tmp += self.__to_string('infos')

        if tmp[-1:] == ',':
            # Strip off trailing ','
            tmp = tmp[:-1]

        return "{%s}" % tmp

    def add_error(self, resource_id, *args):
        """

        :param resource_id:
        :param args:
        :return:
        """
        self._result['errors']['count'] += 1
        message = {'resource_id': resource_id, 'args': args}
        self._result['errors']['messages'].append(message)
        return

    def add_warning(self, resource_id, *args):
        """

        :param resource_id:
        :param args:
        :return:
        """
        self._result['warnings']['count'] += 1
        message = {'resource_id': resource_id, 'args': args}
        self._result['warnings']['messages'].append(message)
        return

    def add_info(self, resource_id, *args):
        """

        :param resource_id:
        :param args:
        :return:
        """
        self._result['infos']['count'] += 1
        message = {'resource_id': resource_id, 'args': args}
        self._result['infos']['messages'].append(message)
        return

    def get_validation_area(self):
        """

        :return:
        """
        return self._result['validation_area']

    def get_errors_count(self):
        """

        :return:
        """
        return self._result['errors']['count']

    def get_errors_messages(self):
        """

        :return:
        """
        return self._result['errors']['messages']

    def get_warnings_count(self):
        """

        :return:
        """
        return self._result['warnings']['count']

    def get_warnings_messages(self):
        """

        :return:
        """
        return self._result['warnings']['messages']

    def get_infos_count(self):
        """

        :return:
        """
        return self._result['infos']['count']

    def get_infos_messages(self):
        """

        :return:
        """
        return self._result['infos']['messages']

    def __to_string(self, category_name):
        tmp = ' "%s": {' % category_name
        tmp += '"count": %d, ' % self._result[category_name]['count']
        tmp += '"messages": ['
        for message in self._result[category_name]['messages']:
            tmp += "{"
            tmp += '"%s": "%s",' % ('message', ExceptionHelper.getMessage(message['resource_id'],
                                                                          list(message['args'])))
            if tmp[-1:] == ',':
                # Strip off trailing ','
                tmp = tmp[:-1]
            tmp += "},"
        if tmp[-1:] == ',':
            # Strip off trailing ','
            tmp = tmp[:-1]
        # Concatenate closing ']}'
        tmp += "]},"

        return tmp
