"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import java.util.logging.Level as JLevel

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

        for validation_result in self._validation_result_dict.values():
            if validation_result.get_errors_count() > 0 \
                    or validation_result.get_warnings_count() > 0 \
                    or validation_result.get_infos_count():

                indent_level = 0
                validation_area = validation_utils.format_message('WLSDPLY-05200',
                                                                  validation_result.get_validation_area())
                validation_utils.print_blank_lines()
                validation_utils.print_indent(validation_utils.divider_string, indent_level)
                validation_utils.print_indent(validation_area, indent_level)
                validation_utils.print_indent(validation_utils.divider_string, indent_level)

                if validation_result.get_infos_count() > 0:
                    _print_results_category_details(validation_utils.format_message('WLSDPLY-05201'),
                                                    validation_result.get_infos_count(),
                                                    validation_result.get_infos_messages(), indent_level)

                if validation_result.get_warnings_count() > 0:
                    _print_results_category_details(validation_utils.format_message('WLSDPLY-05202'),
                                                    validation_result.get_warnings_count(),
                                                    validation_result.get_warnings_messages(), indent_level)

                if validation_result.get_errors_count() > 0:
                    _print_results_category_details(validation_utils.format_message('WLSDPLY-05203'),
                                                    validation_result.get_errors_count(),
                                                    validation_result.get_errors_messages(), indent_level)

    def log_results(self, logger):
        """

        :return:
        """
        _method_name = 'log_results'

        if logger is not None:
            # Get counts for all the ValidationResult objects
            # in this ValidationResult object
            results_summary = self.__get_summary()

            logger.set_level(JLevel.INFO)

            # Determine what the severity level is going to be for the
            # summary log message. Needs to be set in accordance with
            # what the severest validation message was.
            if results_summary['infos_count'] > 0:
                logger.set_level(JLevel.INFO)
            if results_summary['warnings_count'] > 0:
                logger.set_level(JLevel.WARNING)
            if results_summary['errors_count'] > 0:
                logger.set_level(JLevel.SEVERE)

            total_messages_count = \
                int(results_summary['errors_count']) + int(results_summary['warnings_count']) + \
                int(results_summary['infos_count'])

            logger.log(logger.get_level(),
                       'WLSDPLY-05204',
                       results_summary['errors_count'],
                       results_summary['warnings_count'],
                       results_summary['infos_count'],
                       total_messages_count,
                       class_name=self._class_name, method_name=_method_name)

            for validation_result in self._validation_result_dict.values():
                if validation_result.get_infos_count() > 0:
                    logger.set_level(JLevel.INFO)
                    self.__log_results_category_details(validation_result.get_infos_messages(),
                                                        _method_name, logger)

            for validation_result in self._validation_result_dict.values():
                if validation_result.get_warnings_count() > 0:
                    logger.set_level(JLevel.WARNING)
                    self.__log_results_category_details(validation_result.get_warnings_messages(),
                                                        _method_name, logger)

            for validation_result in self._validation_result_dict.values():
                if validation_result.get_errors_count() > 0:
                    logger.set_level(JLevel.SEVERE)
                    self.__log_results_category_details(validation_result.get_errors_messages(),
                                                        _method_name, logger)

            logger.set_level(JLevel.INFO)

        return

    def __log_results_category_details(self, category_messages, method_name, logger):
        """

        :param category_messages:
        :param method_name:
        :param logger:
        :return:
        """

        for i in range(len(category_messages)):
            messages = category_messages[i]
            if 'message' in messages:
                logger.log(logger.get_level(), message=messages['message'],
                           class_name=self._class_name, method_name=method_name)
            elif 'valid_items' in messages:
                logger.log(logger.get_level(), message=messages['valid_items'],
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


def _print_results_category_details(result_category, category_count, category_messages, indent_level):
    """

    :param result_category:
    :param category_count:
    :param category_messages:
    :param indent_level:
    :return:
    """
    validation_utils.print_blank_lines()
    validation_utils.print_indent('%s: %d' % (result_category, category_count), indent_level + 1)

    for i in range(len(category_messages)):
        messages = category_messages[i]
        if 'message' in messages:
            validation_utils.print_indent(
                validation_utils.format_message('WLSDPLY-05205', messages['message']), indent_level + 2
            )
        elif 'valid_items' in messages:
            validation_utils.print_indent(
                validation_utils.format_message('WLSDPLY-05206', messages['valid_items']), indent_level + 2
            )
            # if i == len(messages):
            #     validation_utils.print_blank_lines()


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

    def add_error(self, error_item_message, valid_items_message=None):
        """

        :param error_item_message:
        :param valid_items_message:
        :return:
        """
        self._result['errors']['count'] += 1
        message = {'message': error_item_message}
        if valid_items_message is not None:
            message['valid_items'] = valid_items_message
        self._result['errors']['messages'].append(message)

    def add_warning(self, warning_item_message, valid_items_message=None):
        """

        :param warning_item_message:
        :param valid_items_message:
        :return:
        """
        self._result['warnings']['count'] += 1
        message = {'message': warning_item_message}
        if valid_items_message is not None:
            message['valid_items'] = valid_items_message
        self._result['warnings']['messages'].append(message)

    def add_info(self, info_item_message):
        """

        :param info_item_message:
        :return:
        """
        self._result['infos']['count'] += 1
        message = {'message': info_item_message}
        self._result['infos']['messages'].append(message)

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

    def print_details(self):
        pass

    def __to_string(self, category_name):
        tmp = ' "%s": {' % category_name
        tmp += '"count": %d, ' % self._result[category_name]['count']
        tmp += '"messages": ['
        for message in self._result[category_name]['messages']:
            tmp += "{"
            message_list = message.keys()
            message_list.sort()
            for name in message_list:
                value = message[name]
                tmp += '"%s": "%s",' % (name, value)
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
