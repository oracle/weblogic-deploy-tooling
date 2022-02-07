/*
 * Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;


public class CustomBeanUtilsTest {

    @Test
    public void testBooleanValueToBooleanConversion() {
        Object result = CustomBeanUtils.convertValue(Boolean.TRUE, Boolean.class);
        assertEquals(Boolean.TRUE, result, "Boolean result does not match");
    }

    @Test
    public void testStringToBooleanConversion() {
        Object result = CustomBeanUtils.convertValue("true", Boolean.class);
        assertEquals(Boolean.TRUE, result, "String to boolean result does not match");
    }

    @Test
    public void testCharacterConversion() {
        Object result = CustomBeanUtils.convertValue('x', Character.class);
        assertEquals('x', result, "Character result does not match");
    }

    @Test
    public void testStringToCharacterConversion() {
        Object result = CustomBeanUtils.convertValue("x", Character.class);
        assertEquals('x', result, "String to character result does not match");
    }

    @Test
    public void testStringToIntegerConversion() {
        Object result = CustomBeanUtils.convertValue("1234", Integer.class);
        assertEquals(1234, result, "String to integer does not match");
    }

    @Test
    public void testStringToLongConversion() {
        Object result = CustomBeanUtils.convertValue("1234", Long.class);
        assertEquals(1234L, result, "Boolean text result does not match");
    }

    @Test
    public void testStringToFloatConversion() {
        Object result = CustomBeanUtils.convertValue("123.4", Float.class);
        assertEquals(123.4f, result, "String to float result does not match");
    }

    @Test
    public void testStringToDoubleConversion() {
        Object result = CustomBeanUtils.convertValue("123.4", Double.class);
        assertEquals(123.4, result, "String to double result does not match");
    }

    @Test
    public void testStringToStringConversion() {
        String sourceText = "textValue";
        Object result = CustomBeanUtils.convertValue(sourceText, String.class);
        assertEquals(sourceText, result, "String result does not match");
    }

    @Test
    public void testBadStringToIntegerConversionThrowsException() {
        assertThrows(IllegalArgumentException.class, new Executable() {
            @Override
            public void execute() throws Throwable {
                CustomBeanUtils.convertValue("1234X", Integer.class);
            }
        });
    }

    @Test
    public void testStringArrayToStringArrayConversion() {
        String[] sourceTexts = { "textValue", "textValue2" };
        Object result = CustomBeanUtils.convertValue(sourceTexts, String[].class);
        assertTrue(arraysMatch(sourceTexts, (String[]) result), "String array result does not match");
    }

    @Test
    public void testDelimitedStringToStringArrayConversion() {
        String sourceDelimited = "textValue,textValue2";
        String[] sourceTexts = { "textValue", "textValue2" };

        Object result = CustomBeanUtils.convertValue(sourceDelimited, String[].class);
        assertTrue(arraysMatch(sourceTexts, (String[]) result), "Delimited string array result does not match");
    }

    @Test
    public void testIntegerArrayToIntegerArrayConversion() {
        Integer[] sourceInts = { 123, 456 };
        Object result = CustomBeanUtils.convertValue(sourceInts, Integer[].class);
        assertTrue(arraysMatch(sourceInts, (Integer[]) result), "String array result does not match");
    }

    @Test
    public void testStringArrayToIntegerArrayConversion() {
        String[] sourceTextInts = { "123", "456" };
        Integer[] sourceInts = { 123, 456 };

        Object result = CustomBeanUtils.convertValue(sourceTextInts, Integer[].class);
        assertTrue(arraysMatch(sourceInts, (Integer[]) result), "Integer string array result does not match");
    }

    @Test
    public void testDelimitedStringToIntegerArrayConversion() {
        String sourceDelimitedInts = "123,456";
        Integer[] sourceInts = { 123, 456 };

        Object result = CustomBeanUtils.convertValue(sourceDelimitedInts, Integer[].class);
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
