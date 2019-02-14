/*
 * Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.util;

/**
 * Utility methods related to data type conversion.
 */
public final class ConvertUtils {

    private ConvertUtils() {
        // hide the constructor for this utility class
    }

    /**
     * Convert the specified value to the specified type.
     * The conversions and available types are specific to user-defined custom mbeans.
     *
     * @param value the value to be converted
     * @param dataType the class representing the target type
     * @return the value converted to the new type, or null if conversion failed
     */
    public static Object convertValue(Object value, Class<?> dataType) {
        // TODO: fill in data types

        if(dataType.equals(String.class)) {
            return value;
        }

        return null;
    }
}
