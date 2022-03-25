"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import re
from sets import Set

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.exception import exception_helper


class JVMArguments(object):
    """
    Class that represents the JVM command-line options.
    """

    _class_name = 'JVMArguments'
    __client_server_regex = re.compile('-client|-server')

    # examples: -Xmx200m -Xms100K
    __x_args_size_regex = re.compile('(-X(ms|mx|ss|mn) ?)([0-9]+[kmgKMG]? ?)')

    # example: -Xrunjdwp:transport=dt_socket,address=8888,server=y,suspend=y
    __x_args_value_regex = re.compile('(-X[a-zS]+(/[ap])? ?):([\S]+ ?)')

    __x_args_other_regex = re.compile('(-X[a-z]+ ?)(=([0-9]+[kmgKMG]? ?))?')
    __xx_args_switch_regex = re.compile('-XX:([+-] ?)([a-zA-Z0-9]+ ?)')
    __xx_args_value_regex = re.compile('-XX:([a-zA-Z0-9]+ ?)=([\S]+ ?)')

    # examples: -Dabc -Dxyz=jkl,fdr,jdk -Drak=xyz
    __sys_props_regex = re.compile('-D([a-zA-Z0-9-_.]+ ?)(=([\S]+ ?))?')

    __size_regex = re.compile('([0-9]+ ?)([kmgKMG]? ?)')
    __k_multiplier = 1024
    __m_multiplier = 1024 * 1024
    __g_multiplier = 1024 * 1024 * 1024

    def __init__(self, logger, args):
        self._logger = logger
        self.__raw_args = args
        self.__x_args = OrderedDict()
        self.__xx_args = OrderedDict()
        self.__sys_props = OrderedDict()
        self.__client_server_args = list()
        self.__unsorted_args = list()
        self.__parse_args()

    def get_arguments_string(self):
        """
        Get the argument string representation of this object
        :return: the argument string
        """
        result = self.__get_client_server_arg_string('')
        result = self.__get_x_args_string(result)
        result = self.__get_xx_args_string(result)
        result = self.__get_system_property_args_string(result)
        result = self.__get_unsorted_args_string(result)
        return result

    def merge_jvm_arguments(self, other_jvm_args_obj):
        """
        Merge the specified JVMArguments object into this one, overwriting overlapping values in this object
        with those from the specified object.
        :param other_jvm_args_obj: the specified JVMArguments object to merge
        :raises: AliasException: if merging the JVM args encounters a problem with the arguments
        """
        self.__add_client_server_args(other_jvm_args_obj.get_client_server_args_list())
        self.__add_x_args(other_jvm_args_obj.get_x_args_dict())
        self.__add_xx_args(other_jvm_args_obj.get_xx_args_dict())
        self.__add_system_property_args(other_jvm_args_obj.get_sys_props_dict())
        self.__add_unsorted_args(other_jvm_args_obj.get_unsorted_args_list())

    ###########################################################################
    #          Private methods that are not part of the public API            #
    ###########################################################################

    def get_client_server_args_list(self):
        """
        Internal method required for merge support.
        WARNING: This method returns the internal data structure so do not modify it.
        :return: client_server list
        """
        return self.__client_server_args

    def get_x_args_dict(self):
        """
        Internal method required for merge support.
        WARNING: This method returns the internal data structure so do not modify it.
        :return: -X args dictionary
        """
        return self.__x_args

    def get_xx_args_dict(self):
        """
        Internal method required for merge support.
        WARNING: This method returns the internal data structure so do not modify it.
        :return: -XX args dictionary
        """
        return self.__xx_args

    def get_sys_props_dict(self):
        """
        Internal method required for merge support.
        WARNING: This method returns the internal data structure so do not modify it.
        :return: -D args dictionary
        """
        return self.__sys_props

    def get_unsorted_args_list(self):
        """
        Internal method required for merge support.
        WARNING: This method returns the internal data structure so do not modify it.
        :return: all other arguments list
        """
        return self.__unsorted_args

    def __get_client_server_arg_string(self, incremental_result):
        """
        Get the  -client or -server argument, if any, from the end of the list (last one specified).
        :return: the combined incremental result and -client or -server, if present
        """
        result = incremental_result
        if len(self.__client_server_args) > 0:
            if len(result) > 0:
                result += ' '
            result += self.__client_server_args[-1]
        return result

    def __get_x_args_string(self, incremental_result):
        """
        Get the argument string for the -X arguments.
        :param incremental_result: the result to which to add the -X argument string
        :return: the combined incremental result and -X argument string
        """
        _method_name = '__get_x_args_string'

        self._logger.entering(incremental_result, class_name=self._class_name, method_name=_method_name)
        result = incremental_result
        result = self.__get_x_size_args(result)
        result = self.__get_x_value_args(result)
        result = self.__get_x_other_args(result)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def __get_xx_args_string(self, incremental_result):
        """
        Get the argument string for the -XX arguments.
        :param incremental_result: the result to which to add the -XX argument string
        :return: the combined incremental result and -XX argument string
        """
        _method_name = '__get_xx_args_string'

        self._logger.entering(incremental_result, class_name=self._class_name, method_name=_method_name)
        result = incremental_result
        result = self.__get_xx_switch_args(result)
        result = self.__get_xx_value_args(result)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def __get_system_property_args_string(self, incremental_result):
        """
        Get the argument string for the -D arguments.
        :param incremental_result: the result to which to add the -D argument string
        :return: the combined incremental result and -D argument string
        """
        _method_name = '__get_system_property_args_string'
        self._logger.entering(incremental_result, class_name=self._class_name, method_name=_method_name)
        result = incremental_result
        for key, value in self.__sys_props.iteritems():
            if len(result) > 0:
                result += ' '
            result += '-D' + key
            if value is not None:
                result += '=' + value
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def __get_unsorted_args_string(self, incremental_result):
        """
        Get the argument string for the all of the other, unsorted arguments.
        :param incremental_result: the result to which to add the -XX argument string
        :return: the combined incremental result and -XX argument string
        """
        _method_name = '__get_system_property_args_string'
        self._logger.entering(incremental_result, class_name=self._class_name, method_name=_method_name)
        result = incremental_result
        if len(result) > 0 and len(self.__unsorted_args) > 0:
            result += ' '
        result += ' '.join(self.__unsorted_args)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def __add_client_server_args(self, other_cs_list):
        """
        Add the specified list to the current one.
        :param other_cs_list: the specified list
        """
        self.__client_server_args.extend(other_cs_list)

    def __add_x_args(self, other_x_args_dict):
        """
        Add the specified dictionary to the current one.
        :param other_x_args_dict: the specified dictionary
        """
        self.__merge_x_size_args(other_x_args_dict)
        self.__merge_x_value_args(other_x_args_dict)
        self.__merge_x_other_args(other_x_args_dict)

    def __add_xx_args(self, other_xx_args_dict):
        """
        Add the specified dictionary to the current one.
        :param other_xx_args_dict: the specified dictionary
        :return:
        """
        self.__merge_xx_switch_args(other_xx_args_dict)
        self.__merge_xx_value_args(other_xx_args_dict)

    def __add_system_property_args(self, other_sys_props_dict):
        """
        Add the specified dictionary to the current one.
        :param other_sys_props_dict: the specified dictionary
        :return:
        """
        for key, value in other_sys_props_dict.iteritems():
            self.__sys_props[key] = value

    def __add_unsorted_args(self, other_unsorted_args_list):
        """
        Add the specified list into the current one, removing duplicates.
        :param other_unsorted_args_list: the specified list
        """
        if len(other_unsorted_args_list) > 0:
            if len(self.__unsorted_args) > 0:
                other_unsorted_set = Set(other_unsorted_args_list)
                my_unsorted_set = Set(self.__unsorted_args)
                self.__unsorted_args = list(my_unsorted_set.union(other_unsorted_set))
            else:
                self.__unsorted_args = list(other_unsorted_args_list)

    def __parse_args(self):
        """
        Parse the arguments string into its components.
        """
        _method_name = '__parse_args'

        if self.__raw_args is not None and len(self.__raw_args) > 0:
            if isinstance(self.__raw_args, list):
                arguments = self.__raw_args
            else:
                arguments = self.__raw_args.split()

            for argument in arguments:
                if self.__client_server_regex.match(argument):
                    self.__client_server_args.append(argument)
                elif self.__x_args_size_regex.match(argument):
                    self.__process_x_size_arg(argument)
                elif self.__x_args_value_regex.match(argument):
                    self.__process_x_value_arg(argument)
                elif self.__x_args_other_regex.match(argument):
                    self.__process_x_other_arg(argument)
                elif self.__xx_args_switch_regex.match(argument):
                    self.__process_xx_switch_arg(argument)
                elif self.__xx_args_value_regex.match(argument):
                    self.__process_xx_value_arg(argument)
                elif self.__sys_props_regex.match(argument):
                    self.__process_sys_prop_arg(argument)
                else:
                    self._logger.finer('WLSDPLY-08300', argument, class_name=self._class_name, method_name=_method_name)
                    self.__unsorted_args.append(argument)

    def __process_x_size_arg(self, argument):
        """
        Process -X arguments where the argument specifies a size that has no delimiter and add it to the internal map.
        :param argument: the argument string
        """
        _method_name = '__process_x_size_arg'

        match = self.__x_args_size_regex.match(argument)
        xarg = match.group(1)
        xvalue = match.group(3)
        if 'size' not in self.__x_args:
            self.__x_args['size'] = OrderedDict()
        self._logger.finer('WLSDPLY-08301', argument, xarg, xvalue,
                           class_name=self._class_name, method_name=_method_name)
        self.__x_args['size'][xarg] = xvalue

    def __process_x_value_arg(self, argument):
        """
        Process -X arguments where the argument specifies a value that has a colon delimiter and
        add it to the internal map.
        :param argument: the argument string
        """
        _method_name = '__process_x_value_arg'

        match = self.__x_args_value_regex.match(argument)
        xarg = match.group(1)
        xvalue = match.group(3)
        if 'value' not in self.__x_args:
            self.__x_args['value'] = OrderedDict()
        self._logger.finer('WLSDPLY-08302', argument, xarg, xvalue,
                           class_name=self._class_name, method_name=_method_name)
        self.__x_args['value'][xarg] = xvalue

    def __process_x_other_arg(self, argument):
        """
        Process -X arguments where the argument a switch or a value with an equals delimiter and
        add it to the internal map.
        :param argument: the argument string
        """
        _method_name = '__process_x_other_arg'

        match = self.__x_args_other_regex.match(argument)
        xarg = match.group(1)
        #
        # match.group(3) will always be None unless the argument is of the form -Xmaxjitcodesize=240m
        #
        xvalue = match.group(3)
        if 'other' not in self.__x_args:
            self.__x_args['other'] = OrderedDict()
        self._logger.finer('WLSDPLY-08303', argument, xarg, xvalue,
                           class_name=self._class_name, method_name=_method_name)
        self.__x_args['other'][xarg] = xvalue

    def __process_xx_switch_arg(self, argument):
        """
        Process -XX arguments where there is a plus or minus sign to turn on/off the option and
        add it to the internal map.
        :param argument: the argument string
        """
        _method_name = '__process_xx_switch_arg'

        match = self.__xx_args_switch_regex.match(argument)
        xarg = match.group(2)
        on_or_off = match.group(1)
        if on_or_off == '+':
            on_or_off_text = 'on'
        else:
            on_or_off_text = 'off'

        if 'switch' not in self.__xx_args:
            self.__xx_args['switch'] = OrderedDict()
        self._logger.finer('WLSDPLY-08304', argument, xarg, on_or_off_text,
                           class_name=self._class_name, method_name=_method_name)
        self.__xx_args['switch'][xarg] = on_or_off

    def __process_xx_value_arg(self, argument):
        """
        Process -XX arguments where there a value delimited by an equal sign and add it to the internal map.
        :param argument: the argument string
        """
        _method_name = '__process_xx_value_arg'

        match = self.__xx_args_value_regex.match(argument)
        xarg = match.group(1)
        xvalue = match.group(2)

        if 'value' not in self.__xx_args:
            self.__xx_args['value'] = OrderedDict()
        self._logger.finer('WLSDPLY-08305', argument, xarg, xvalue,
                           class_name=self._class_name, method_name=_method_name)
        self.__xx_args['value'][xarg] = xvalue

    def __process_sys_prop_arg(self, argument):
        """
        Process Java system property definition (-D) arguments where there the value, if  any, is delimited by
        an equal sign and add it to the internal map.
        :param argument: the argument string
        """
        _method_name = '__process_xx_value_arg'

        match = self.__sys_props_regex.match(argument)
        prop_name = match.group(1)
        #
        # match.group(3) will always be None if the argument is of the form -Dfoo instead of -Dfoo=bar
        #
        prop_value = match.group(3)
        self._logger.finer('WLSDPLY-08306', argument, prop_name, prop_value,
                           class_name=self._class_name, method_name=_method_name)
        self.__sys_props[prop_name] = prop_value

    def __get_x_size_args(self, incremental_result):
        """
        Add the -X size arguments to the end of the specified string.
        :param incremental_result: the specified string
        :return: the resulting string
        """
        result = incremental_result
        if 'size' in self.__x_args:
            x_size_args = self.__x_args['size']
            for key, value in x_size_args.iteritems():
                if len(result) > 0:
                    result += ' '
                result += key + value
        return result

    def __get_x_value_args(self, incremental_result):
        """
        Add the -X value arguments to the end of the specified string.
        :param incremental_result: the specified string
        :return: the resulting string
        """
        result = incremental_result
        if 'value' in self.__x_args:
            x_value_args = self.__x_args['value']
            for key, value in x_value_args.iteritems():
                if len(result) > 0:
                    result += ' '
                result += key + ':' + value
        return result

    def __get_x_other_args(self, incremental_result):
        """
        Add the -X other arguments to the end of the specified string.
        :param incremental_result: the specified string
        :return: the resulting string
        """
        result = incremental_result
        if 'other' in self.__x_args:
            x_other_args = self.__x_args['other']
            for key, value in x_other_args.iteritems():
                if len(result) > 0:
                    result += ' '
                result += key
                if value is not None:
                    result += '=' + value
        return result

    def __get_xx_switch_args(self, incremental_result):
        """
        Add the -XX switch arguments to the end of the specified string.
        :param incremental_result: the specified string
        :return: the resulting string
        """
        result = incremental_result
        if 'switch' in self.__xx_args:
            xx_switch_args = self.__xx_args['switch']
            for key, value in xx_switch_args.iteritems():
                if len(result) > 0:
                    result += ' '
                result += '-XX:' + value + key
        return result

    def __get_xx_value_args(self, incremental_result):
        """
        Add the -XX value arguments to the end of the specified string.
        :param incremental_result: the specified string
        :return: the resulting string
        """
        result = incremental_result
        if 'value' in self.__xx_args:
            xx_value_args = self.__xx_args['value']
            for key, value in xx_value_args.iteritems():
                if len(result) > 0:
                    result += ' '
                result += '-XX:' + key + '=' + value
        return result

    def __merge_x_size_args(self, other_x_args):
        """
        Merge the specified -X size arguments into the current ones.
        :param other_x_args: the specified -X size args to merge
        :raises: AliasException: if the size cannot be parsed as a number
        """
        _method_name = '__merge_x_size_args'

        if 'size' in other_x_args:
            other_size_args = other_x_args['size']
            if 'size' in self.__x_args:
                my_size_args = self.__x_args['size']

                my_min_heap_size = '0'
                if '-Xms' in my_size_args:
                    my_min_heap_size = my_size_args['-Xms']
                if '-Xms' in other_size_args:
                    my_min_heap_size = other_size_args['-Xms']

                my_max_heap_size = '0'
                if '-Xmx' in my_size_args:
                    my_max_heap_size = my_size_args['-Xmx']
                if '-Xmx' in other_size_args:
                    my_max_heap_size = other_size_args['-Xmx']

                if my_max_heap_size != '0' and my_min_heap_size != '0':
                    min_size = self.__get_size_as_number('-Xms', my_min_heap_size)
                    max_size = self.__get_size_as_number('-Xmx', my_max_heap_size)

                    if min_size > max_size:
                        self._logger.warning('WLSDPLY-08307', my_min_heap_size, my_max_heap_size,
                                             class_name=self._class_name, method_name=_method_name)
                        other_size_args['-Xmx'] = my_min_heap_size

                for key, value in other_size_args.iteritems():
                    my_size_args[key] = value
            else:
                self.__x_args['size'] = copy.deepcopy(other_size_args)

    def __merge_x_value_args(self, other_x_args):
        """
        Merge the specified -X value arguments into the current ones.
        :param other_x_args: the specified -X size args to merge
        """
        if 'value' in other_x_args:
            other_value_args = other_x_args['value']
            if 'value' in self.__x_args:
                my_value_args = self.__x_args['value']
                for key, value in other_value_args.iteritems():
                    my_value_args[key] = value
            else:
                self.__x_args['value'] = copy.deepcopy(other_value_args)

    def __merge_x_other_args(self, other_x_args):
        """
        Merge the specified -X other arguments into the current ones.
        :param other_x_args: the specified -X other args to merge
        """
        if 'other' in other_x_args:
            other_other_args = other_x_args['other']
            if 'other' in self.__x_args:
                my_other_args = self.__x_args['other']
                for key, value in other_other_args.iteritems():
                    my_other_args[key] = value
            else:
                self.__x_args['other'] = copy.deepcopy(other_other_args)

    def __merge_xx_switch_args(self, other_xx_args):
        """
        Merge the specified -XX switch arguments into the current ones.
        :param other_xx_args: the specified -XX switch args to merge
        """
        if 'switch' in other_xx_args:
            other_switch_args = other_xx_args['switch']
            if 'switch' in self.__xx_args:
                my_switch_args = self.__xx_args['switch']
                for key, value in other_switch_args.iteritems():
                    my_switch_args[key] = value
            else:
                self.__xx_args['switch'] = copy.deepcopy(other_switch_args)

    def __merge_xx_value_args(self, other_xx_args):
        """
        Merge the specified -XX value arguments into the current ones.
        :param other_xx_args: the specified -XX value args to merge
        """
        if 'value' in other_xx_args:
            other_value_args = other_xx_args['value']
            if 'value' in self.__xx_args:
                my_value_args = self.__xx_args['value']
                for key, value in other_value_args.iteritems():
                    my_value_args[key] = value
            else:
                self.__xx_args['value'] = copy.deepcopy(other_value_args)

    def __get_size_as_number(self, size_arg, size_string):
        """
        Convert the specified size string into a number.
        :param size_arg: the arg name that specified the size string
        :param size_string: the size string
        :return: the size as a number
        """
        _method_name = '__get_size_as_number'

        match = self.__size_regex.match(size_string)
        if not match:
            ex = exception_helper.create_alias_exception('WLSDPLY-08308', size_arg, size_string)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        number = int(match.group(1))
        multiplier = self.__get_size_multiplier(match.group(2))
        return number * multiplier

    def __get_size_multiplier(self, multiplier):
        """
        Get the size multiplier based on the letter suffix (e.g., a value of k would result in a multiplier of 1024).
        :param multiplier: the multiplier
        :return: the multiplier as a number
        """
        if multiplier is None:
            result = 1
        elif multiplier in ['k', 'K']:
            result = self.__k_multiplier
        elif multiplier in ['m', 'M']:
            result = self.__m_multiplier
        elif multiplier in ['g', 'G']:
            result = self.__g_multiplier
        else:
            result = 0
        return result
