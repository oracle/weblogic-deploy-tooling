/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.aliases;

import java.io.File;
import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Properties;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.PyOrderedDict;
import oracle.weblogic.deploy.util.StringUtils;

import org.python.core.Py;
import org.python.core.PyDictionary;
import org.python.core.PyException;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyTuple;

/**
 * Helper methods for converting between types.
 */
public final class TypeUtils {
    private static final String CLASS = TypeUtils.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    public static final String DEFAULT_STRING_LIST_DELIMITER = ",";

    private TypeUtils() {
        // hide the constructor for this utility class
    }

    /**
     * Determine if the object is an instance of the specified class.
     *
     * @param clazz the class
     * @param object the object to check
     * @return true if the object is an instance of the class, false otherwise
     */
    public static boolean isInstanceOfClass(Class<?> clazz, Object object) {
        return clazz.isAssignableFrom(object.getClass());
    }

    /**
     * Convert the value provided to the requested data type, if possible.
     *
     * @param targetTypeName  the Class that value will be converted to.
     * @param value           the data to be converted.
     * @return                the requested data type, null is returned if the conversion is not possible
     *                        or the requested data type is not supported.
     * @throws AliasException if the targetTypeName is not a known/supported type or a multi-value type with
     *                        no delimiter is detected where a delimiter is required to handle the conversion
     */
    public static Object convertToType(String targetTypeName, Object value) throws AliasException {
        String delimiter;
        switch (targetTypeName) {
            case "delimited_string":
            case "delimited_string[comma]":
                delimiter = ",";
                break;
            case "delimited_string[semicolon]":
                delimiter = ";";
                break;
            case "delimited_string[space]":
                delimiter = " ";
                break;
            case "delimited_string[path_separator]":
                delimiter = File.pathSeparator;
                break;
            default:
                delimiter = DEFAULT_STRING_LIST_DELIMITER;
        }
        return convertToType(targetTypeName, value, delimiter);
    }

    /**
     * Convert the value provided to the requested data type, if possible.
     *
     * @param targetTypeName  the Class that value will be converted to.
     * @param value           the data to be converted.
     * @param delimiter       the delimiter to use for processing multi-value types with strings
     * @return                the requested data type, null is returned if the conversion is not possible
     *                        or the requested data type is not supported.
     * @throws AliasException if the targetTypeName is not a known/supported type or a multi-value type with
     *                        no delimiter is detected where a delimiter is required to handle the conversion
     */
    public static Object convertToType(String targetTypeName, Object value, String delimiter) throws AliasException {
        final String METHOD = "convertToType";

        Class<?> targetType;
        switch( targetTypeName ) {
            case "password":
            case "credential":
            case "string":
                targetType = String.class;
                break;
            case "integer":
                targetType = Integer.class;
                break;
            case "long":
                targetType = Long.class;
                break;
            case "double":
                targetType = Double.class;
                break;
            case "boolean":
            case "java.lang.Boolean":
                targetType = Boolean.class;
                break;
            case "delimited_string":
            case "delimited_string[comma]":
            case "delimited_string[semicolon]":
            case "delimited_string[space]":
            case "delimited_string[path_separator]":
            case "list":
                targetType = List.class;
                break;
            case "jarray":
                targetType = Object[].class;
                break;
            case "properties":
                targetType = Properties.class;
                break;
            case "OrderedDict":
            case "PyOrderedDict":
            case "dict":
                targetType = PyOrderedDict.class;
                break;
            default:
                AliasException ae = new AliasException("WLSDPLY-08500", targetTypeName);
                LOGGER.throwing(CLASS, METHOD, ae);
                throw ae;
        }
        return convertToType(targetType, value, delimiter);
    }

    /**
     * Convert the value provided to the requested data type, if possible.
     *
     * @param targetType      the Class that value will be converted to.
     * @param value           the data to be converted.
     * @return                the requested data type, null is returned if the conversion is not possible
     *                        or the requested data type is not supported.
     * @throws AliasException if classType is a primitive class type such as int, short, etc. or if a multi-valued
     *                        type is detected where the delimiter is null and a delimiter is required to handle
     *                        the conversion.
     */
    public static Object convertToType(Class<?> targetType, Object value) throws AliasException {
        return convertToType(targetType, value, DEFAULT_STRING_LIST_DELIMITER);
    }

    /**
     * Convert the value provided to the requested data type, if possible.
     *
     * @param targetType      the Class that value will be converted to.
     * @param value           the data to be converted.
     * @param delimiter       the delimiter to use for processing multi-value types with strings
     * @return                the requested data type, null is returned if the conversion is not possible
     *                        or the requested data type is not supported.
     * @throws AliasException if classType is a primitive class type such as int, short, etc. or if a multi-valued
     *                        type is detected where the delimiter is null and a delimiter is required to handle
     *                        the conversion. Or if the numeric value cannot be converted to the numeric format.
     */
    public static Object convertToType(Class<?> targetType, Object value, String delimiter) throws AliasException {
        final String METHOD = "convertToType";

        if (targetType.isPrimitive()) {
            AliasException ae = new AliasException("WLSDPLY-08501", targetType.getSimpleName());
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }

        if (value == null) {
            return null;
        }

        String strValue;
        if (value instanceof char[]) {
            strValue = String.valueOf((char[]) value);
        } else {
            strValue = value.toString().trim();
            if (strValue.length() == 0) {
                return null;
            }
        }

        Object result;
        try {
            if (targetType == String.class) {
                result = strValue;
            } else if (targetType == Boolean.class) {
                result = convertToBoolean(strValue);
            } else if (targetType == Integer.class) {
                result = Integer.valueOf(strValue);
            } else if (targetType == Short.class) {
                result = Short.valueOf(strValue);
            } else if (targetType == Long.class) {
                result = Long.valueOf(strValue);
            } else if (targetType == Float.class) {
                result = Float.valueOf(strValue);
            } else if (targetType == Double.class) {
                result = Double.valueOf(strValue);
            } else if (targetType == Character.class) {
                result = convertToCharacter(strValue);
            } else if (targetType == char[].class) {
                result = convertToCharArray(strValue);
            } else if (Object[].class.isAssignableFrom(targetType)) {
                result = convertToObjectArray(value, strValue, delimiter);
            } else if (List.class.isAssignableFrom(targetType)) {
                result = convertToList(value, strValue, delimiter);
            } else if (Properties.class.isAssignableFrom(targetType)) {
                result = convertToProperties(value, delimiter);
            } else if (PyOrderedDict.class.isAssignableFrom(targetType)) {
                result = convertToDictionary(value, delimiter, true);
            } else if (PyDictionary.class.isAssignableFrom(targetType)) {
                result = convertToDictionary(value, delimiter, false);
            } else if (Map.class.isAssignableFrom(targetType)) {
                result = convertToMap(value, strValue, delimiter);
            } else {
                AliasException ae = new AliasException("WLSDPLY-08502", strValue, targetType.getName());
                LOGGER.throwing(CLASS, METHOD, ae);
                throw ae;
            }
        } catch (NumberFormatException nfe) {
            AliasException ae = new AliasException("WLSDPLY-08508", strValue, targetType.getSimpleName(), nfe);
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }
        return result;
    }

    public static String convertToBoolean(String strValue) {
        String result;
        switch (strValue.toLowerCase(Locale.ENGLISH)) {
            case "1":
            case "y":
            case "yes":
            case "true":
                result = "true";
                break;
            default:
                result = "false";
        }
        return result;
    }

    public static Character convertToCharacter(String strValue) {
        Character result = null;
        if (strValue.length() > 0) {
            result = strValue.charAt(0);
        }
        return result;
    }

    private static char[] convertToCharArray(String strValue) {
        char[] c = new char[strValue.length()];
        strValue.getChars(0, c.length, c, 0);
        return c;
    }

    public static Object[] convertToObjectArray(Object value, String strValue, String delimiter)
        throws AliasException {
        Object[] result;
        if (Object[].class.isAssignableFrom(value.getClass())) {
            result = Object[].class.cast(value);
        } else if (value instanceof List) {
            List<?> list = (List<?>) value;
            if (!list.isEmpty()) {
                //thanks to Java Generics type erasure in List, need to get element type from list element
                Class<?> elementClass = list.get(0).getClass();
                Object[] array = (Object[]) Array.newInstance(elementClass, list.size());
                @SuppressWarnings( "unchecked" )
                Object[] rtn = list.toArray(array);
                result = rtn;
            } else {
                result = null;
            }
        } else {
            result = convertStringToList(strValue, delimiter).toArray(new String[0]);
        }
        LOGGER.fine("before convert {0} and after convert {1}", value, result);
        return result;
    }

    private static List<?> convertToList(Object value, String strValue, String delimiter) throws AliasException {
        List<?> result = null;
        if (value instanceof List) {
            result = (List<?>) value;
        } else if (value instanceof Object[]) {
            Object[] array = (Object[]) value;
            if (array.length > 0) {
                result = new ArrayList<>(Arrays.asList(array));
            }
        } else if (!StringUtils.isEmpty(strValue)) {
            result = convertStringToList(strValue, delimiter);
        }
        return result;
    }

    private static Properties convertToProperties(Object value, String delimiter) throws AliasException {
        final String METHOD = "convertToProperties";

        Properties properties;
        if (value instanceof Properties) {
            properties = (Properties) value;
        } else if (value instanceof String) {
            properties = new Properties();
            if (!((String)value).isEmpty()) {
                Map<String, String> convert = convertStringToMap((String) value, delimiter);
                for (Map.Entry<String, String> entry : convert.entrySet()) {
                    properties.setProperty(entry.getKey(), entry.getValue());
                }
            }
        } else if (Map.class.isAssignableFrom(value.getClass())) {
            @SuppressWarnings("unchecked")
            Map<Object,Object> propMap = (Map<Object,Object>) value;
            properties = new Properties();
            properties.putAll(propMap);
        } else if (PyDictionary.class.isAssignableFrom(value.getClass())) {
            PyDictionary dict = (PyDictionary) value;
            properties = new Properties();
            for (Object obj : dict.items()) {
                PyTuple po = (PyTuple) obj;
                properties.put( po.__finditem__(0).toString(), getPropertyText(po.__finditem__(1)) );
            }
        } else {
            AliasException ae = new AliasException("WLSDPLY-08503", value.getClass().getName());
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }
        return properties.isEmpty() ? null : properties;
    }

    /**
     * Returns text for the specified value, for use with property type.
     * @param value the value to be examined
     * @return text for the value
     */
    private static String getPropertyText(Object value) {
        // toString() for PyLong includes trailing L, such as 25L
        if(value instanceof PyLong) {
            return ((PyLong) value).getValue().toString();
        }
        return value.toString();
    }

    private static PyDictionary convertToDictionary(Object value, String delimiter, boolean useOrderedDict)
        throws AliasException {
        final String METHOD = "convertToDictionary";

        PyDictionary dictionary;
        if (value instanceof PyDictionary) {
            dictionary = (PyDictionary)value;
        } else if (value instanceof Properties) {
            dictionary = convertPropertiesToDictionary((Properties)value, useOrderedDict);
        } else if (value instanceof String || Map.class.isAssignableFrom(value.getClass())){
            dictionary = convertPropertiesToDictionary(convertToProperties(value, delimiter), useOrderedDict);
        }  else {
            AliasException ae = new AliasException("WLSDPLY-08504", value.getClass().getName());
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }
        return dictionary.__len__() == 0 ? null : dictionary;
    }

    private static Map<?,?> convertToMap(Object value, String strValue, String delimiter) throws AliasException {
        Map<?,?> result;
        if (Map.class.isAssignableFrom(value.getClass())) {
            result = (Map<?,?>)value;
        } else {
            result = convertStringToMap(strValue, delimiter);
        }
        return result;
    }

    private static List<String> convertStringToList(String strValue, String delimiter) throws AliasException {
        final String METHOD = "convertStringToList";

        if (StringUtils.isEmpty(delimiter)) {
            AliasException ae = new AliasException("WLSDPLY-08505", strValue);
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }

        String listString = strValue.trim();
        if (listString.startsWith("{")) {
            listString = listString.substring(1);
        }

        if (listString.endsWith("}")) {
            listString = listString.substring(0, listString.length() - 1);
        }

        String[] entries = listString.split(delimiter);
        List<String> trimmed = new ArrayList<>(entries.length);
        for (String entry : entries) {
            trimmed.add(entry.trim());
        }
        return trimmed;
    }

    // package protected so that unit tests can test it directly...
    static Map<String, String> convertStringToMap(String strValue, String delimiter) throws AliasException {
        final String METHOD = "convertStringToMap";
        if (StringUtils.isEmpty(delimiter)) {
            AliasException ae = new AliasException("WLSDPLY-08505", strValue);
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }

        String mapString = strValue.trim();
        Map<String, String> map = new HashMap<>();
        if (mapString.startsWith("{")) {
            mapString = mapString.substring(1);
        }

        if (mapString.endsWith("}")) {
            mapString = mapString.substring(0, mapString.length() - 1);
        }

        String[] attrPairs = mapString.split(delimiter);
        for (String pair : attrPairs) {
            String[] keyValue = pair.split("=");
            if (keyValue.length == 2) {
                map.put(keyValue[0].trim(), keyValue[1].trim());
            }
        }
        return map;
    }

    static PyDictionary convertPropertiesToDictionary(Properties properties, boolean useOrderedDict)
        throws AliasException {
        final String METHOD = "convertPropertiesToDictionary";
        PyDictionary dictionary;
        if (useOrderedDict) {
            dictionary = new PyOrderedDict();
        } else {
            dictionary = new PyDictionary();
        }

        if (properties != null) {
            for (String key : properties.stringPropertyNames()) {
                PyObject pyKey = convertToPyObject(key);
                PyObject pyValue = convertToPyObject(properties.getProperty(key));
                try {
                    dictionary.__setitem__(pyKey, pyValue);
                } catch (PyException pe) {
                    AliasException ae = new AliasException("WLSDPLY-08506", pe, key);
                    LOGGER.throwing(CLASS, METHOD, ae);
                    throw ae;
                }
            }
        }
        return dictionary;
    }

    static PyObject convertToPyObject(Object toConvert) throws AliasException {
        PyObject object;
        final String METHOD = "convertPropertiesToDictionary";
        try {
            object = Py.java2py(toConvert);
        } catch (PyException pe) {
            AliasException ae = new AliasException("WLSDPLY-08507", pe, toConvert.getClass().getName());
            LOGGER.throwing(CLASS, METHOD, ae);
            throw ae;
        }
        return object;
    }
}
