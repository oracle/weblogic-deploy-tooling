/*
 * Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import oracle.weblogic.deploy.aliases.TypeUtils;
import oracle.weblogic.deploy.exception.ExceptionHelper;

import java.lang.reflect.Array;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * Utility methods for configuring custom MBeans.
 */
public final class CustomBeanUtils {

    private CustomBeanUtils() {
        // hide the constructor for this utility class
    }

    /**
     * Invoke the specified set method on the MBean with the provided value, converted to the desired type.
     * The conversion and invocation are done together to avoid automatic Jython data conversion.
     *
     * @param mbean the MBean containing the value to be set
     * @param method the method to be called on the specified MBean
     * @param propertyType the class representing the target type
     * @param propertyValue the value to be converted and set
     * @throws IllegalAccessException if method invocation fails
     * @throws IllegalArgumentException if the data conversion or method invocation fails
     * @throws InvocationTargetException if method invocation fails
     */
    public static void callMethod(Object mbean, Method method, Class<?> propertyType, Object propertyValue)
            throws IllegalAccessException, IllegalArgumentException, InvocationTargetException {

        // convert the specified property value to the desired type
        Object setValue = CustomBeanUtils.convertValue(propertyValue, propertyType);

        // call the setter with the target value
        method.invoke(mbean, setValue);
    }

    /**
     * Convert the specified value to the specified type.
     * The conversions and available types are specific to user-defined custom mbeans.
     *
     * @param value the value to be converted
     * @param dataType the class representing the target type
     * @throws IllegalArgumentException if the data conversion fails
     * @return the value converted to the new type, or null if conversion failed
     */
    static Object convertValue(Object value, Class<?> dataType) {
        // package private to allow unit test access

        Object result;

        if (Object[].class.isAssignableFrom(dataType)) {
            result = convertArrayValue(value, dataType);
        } else {
            result = convertSingleValue(value, dataType);
        }

        return result;
    }

    /**
     * Convert the specified array value to the specified type.
     * This may require rebuilding the array with the desired type.
     *
     * @param value the value to be converted
     * @param dataType the class representing the target type
     * @throws IllegalArgumentException if the data conversion fails
     * @return the value converted to the new type, or null if conversion failed
     */
    private static Object convertArrayValue(Object value, Class<?> dataType) {
        Class<?> componentType = dataType.getComponentType();
        Object[] result;

        if (dataType.isAssignableFrom(value.getClass())) {
            // the value may already match the target type
            result = (Object[]) value;

        } else {
            // rebuild the array with the target component type and converted elements
            Object[] source;

            if(Object[].class.isAssignableFrom(value.getClass())) {
                source = (Object[]) value;

            } else if(value instanceof List) {
                // probably a python PyList from model
                source = ((List) value).toArray();

            } else {
                String text = value.toString();
                source = text.split(TypeUtils.DEFAULT_STRING_LIST_DELIMITER);
            }

            Object arrayObject = Array.newInstance(componentType, source.length);

            for (int i = 0; i < source.length; i++) {
                Object elementValue = convertSingleValue(source[i], componentType);
                Array.set(arrayObject, i, elementValue);
            }

            result = (Object[]) arrayObject;
        }

        return result;
    }

    /**
     * Convert the specified single value to the specified type.
     * This invokes the low-level alias conversion methods, with a few adjustments.
     *
     * @param value the value to be converted
     * @param dataType the class representing the target type
     * @throws IllegalArgumentException if the data type is not recognized
     * @return the value converted to the new type, or null if conversion failed
     */
    private static Object convertSingleValue(Object value, Class<?> dataType) {
        if (value == null) {
            return null;
        }

        String textValue;
        if (value instanceof char[]) {
            textValue = String.valueOf((char[]) value);
        } else {
            textValue = value.toString().trim();
            if (textValue.length() == 0) {
                return null;
            }
        }

        // This block of code is similar to the conversion in TypeUtils.convertToType(), but with some differences.
        // Custom MBeans only allow a subset of the data types of full alias conversion, and the Java types have to
        // be strictly maintained to be passed the the reflected set methods. In addition, convertToType() does not
        // convert arrays to the proper data type, so that is handled at a more granular level in this class.

        Object result;

        try {
            if (dataType == String.class) {
                result = textValue;

            } else if((dataType == Boolean.class) || (dataType == Boolean.TYPE)) {
                String booleanText = TypeUtils.convertToBoolean(textValue);
                result = Boolean.parseBoolean(booleanText);

            } else if(dataType == Integer.class) {
                result = Integer.valueOf(textValue);

            } else if(dataType == Short.class) {
                result = Short.valueOf(textValue);

            } else if(dataType == Long.class) {
                result = Long.valueOf(textValue);

            } else if(dataType == Float.class) {
                result = Float.valueOf(textValue);

            } else if(dataType == Double.class) {
                result = Double.valueOf(textValue);

            } else if(dataType == Character.class) {
                result = TypeUtils.convertToCharacter(textValue);

            } else if(dataType == byte[].class) {
                result = textValue.getBytes(StandardCharsets.UTF_8);

            } else {
                String message = ExceptionHelper.getMessage("WLSDPLY-12132", dataType);
                throw new IllegalArgumentException(message);
            }

        } catch(NumberFormatException nfe) {
            String message = ExceptionHelper.getMessage("WLSDPLY-12133", textValue, dataType);
            throw new IllegalArgumentException(message);
        }

        return result;
    }
}
