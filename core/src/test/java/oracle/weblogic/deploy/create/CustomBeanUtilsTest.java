/*
 * Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;


public class CustomBeanUtilsTest {

    @Test
    public void testSimpleTypes() {
        Object result;

        // boolean to boolean
        result = CustomBeanUtils.convertValue(Boolean.TRUE, Boolean.class);
        assertEquals(Boolean.TRUE, result, "Boolean result does not match");

        // string to boolean
        result = CustomBeanUtils.convertValue("true", Boolean.class);
        assertEquals(Boolean.TRUE, result, "String to boolean result does not match");

        // character to character
        result = CustomBeanUtils.convertValue('x', Character.class);
        assertEquals('x', result, "Character result does not match");

        // string to character
        result = CustomBeanUtils.convertValue("x", Character.class);
        assertEquals('x', result, "String to character result does not match");

        // string to double
        result = CustomBeanUtils.convertValue("123.4", Double.class);
        assertEquals(123.4, result, "String to double result does not match");

        // string to float
        result = CustomBeanUtils.convertValue("123.4", Float.class);
        assertEquals(123.4f, result, "String to float result does not match");

        // string to integer
        result = CustomBeanUtils.convertValue("1234", Integer.class);
        assertEquals(1234, result, "String to integer does not match");

        // string to long
        result = CustomBeanUtils.convertValue("1234", Long.class);
        assertEquals(1234L, result, "Boolean text result does not match");

        // string to string
        String sourceText = "textValue";
        result = CustomBeanUtils.convertValue(sourceText, String.class);
        assertEquals(sourceText, result, "String result does not match");

        // fail with bad numeric value
        assertThrows(IllegalArgumentException.class, () -> CustomBeanUtils.convertValue("1234X", Integer.class));
    }

    @Test
    public void testArrayTypes() {
        Object result;

        // string[] to string[]
        String[] sourceTexts = { "textValue", "textValue2" };
        result = CustomBeanUtils.convertValue(sourceTexts, String[].class);
        assertTrue(arraysMatch(sourceTexts, (String[]) result), "String array result does not match");

        // delimited string to string[]
        String sourceDelimited = "textValue,textValue2";
        result = CustomBeanUtils.convertValue(sourceDelimited, String[].class);
        assertTrue(arraysMatch(sourceTexts, (String[]) result), "Delimited string array result does not match");

        // integer[] to integer[]
        Integer[] sourceInts = { 123, 456 };
        result = CustomBeanUtils.convertValue(sourceInts, Integer[].class);
        assertTrue(arraysMatch(sourceInts, (Integer[]) result), "String array result does not match");

        // string[] to integer[]
        String[] sourceTextInts = { "123", "456" };
        result = CustomBeanUtils.convertValue(sourceTextInts, Integer[].class);
        assertTrue(arraysMatch(sourceInts, (Integer[]) result), "Integer string array result does not match");

        // delimited string to string[]
        String sourceDelimitedInts = "123,456";
        result = CustomBeanUtils.convertValue(sourceDelimitedInts, Integer[].class);
        assertTrue(arraysMatch(sourceInts, (Integer[]) result), "Delimited integer array result does not match");
    }

    private boolean arraysMatch(Object[] array1, Object[] array2) {
        if(array1.length != array2.length) {
            return false;
        }

        for(int i = 0; i < array1.length; i++) {
            if(!array1[i].equals(array2[i])) {
                return false;
            }
        }

        return true;
    }
}
