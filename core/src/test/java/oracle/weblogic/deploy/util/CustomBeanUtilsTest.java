/*
 * Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import org.junit.Assert;
import org.junit.Test;


public class CustomBeanUtilsTest {

    @Test
    public void testSimpleTypes() {
        Object result;

        // boolean to boolean
        result = CustomBeanUtils.convertValue(Boolean.TRUE, Boolean.class);
        Assert.assertEquals("Boolean result does not match", Boolean.TRUE, result);

        // string to boolean
        result = CustomBeanUtils.convertValue("true", Boolean.class);
        Assert.assertEquals("String to boolean result does not match", Boolean.TRUE, result);

        // character to character
        result = CustomBeanUtils.convertValue('x', Character.class);
        Assert.assertEquals("Character result does not match",'x', result);

        // string to character
        result = CustomBeanUtils.convertValue("x", Character.class);
        Assert.assertEquals("String to character result does not match", 'x', result);

        // string to double
        result = CustomBeanUtils.convertValue("123.4", Double.class);
        Assert.assertEquals("String to double result does not match", 123.4, result);

        // string to float
        result = CustomBeanUtils.convertValue("123.4", Float.class);
        Assert.assertEquals("String to float result does not match", 123.4f, result);

        // string to integer
        result = CustomBeanUtils.convertValue("1234", Integer.class);
        Assert.assertEquals("String to integer does not match", 1234, result);

        // string to long
        result = CustomBeanUtils.convertValue("1234", Long.class);
        Assert.assertEquals("Boolean text result does not match", 1234L, result);

        // string to string
        String sourceText = "textValue";
        result = CustomBeanUtils.convertValue(sourceText, String.class);
        Assert.assertEquals("String result does not match", sourceText, result);

        // fail with bad numeric value
        try {
            CustomBeanUtils.convertValue("1234X", Integer.class);
            Assert.fail("Numeric conversion should have failed");
        } catch(IllegalArgumentException e) {
            // pass, skipped over Assert.fail()
        }
    }

    @Test
    public void testArrayTypes() {
        Object result;

        // string[] to string[]
        String[] sourceTexts = { "textValue", "textValue2" };
        result = CustomBeanUtils.convertValue(sourceTexts, String[].class);
        Assert.assertTrue("String array result does not match", arraysMatch(sourceTexts, (String[]) result));

        // delimited string to string[]
        String sourceDelimited = "textValue,textValue2";
        result = CustomBeanUtils.convertValue(sourceDelimited, String[].class);
        Assert.assertTrue("Delimited string array result does not match", arraysMatch(sourceTexts, (String[]) result));

        // integer[] to integer[]
        Integer[] sourceInts = { 123, 456 };
        result = CustomBeanUtils.convertValue(sourceInts, Integer[].class);
        Assert.assertTrue("String array result does not match", arraysMatch(sourceInts, (Integer[]) result));

        // string[] to integer[]
        String[] sourceTextInts = { "123", "456" };
        result = CustomBeanUtils.convertValue(sourceTextInts, Integer[].class);
        Assert.assertTrue("Integer string array result does not match", arraysMatch(sourceInts, (Integer[]) result));

        // delimited string to string[]
        String sourceDelimitedInts = "123,456";
        result = CustomBeanUtils.convertValue(sourceDelimitedInts, Integer[].class);
        Assert.assertTrue("Delimited integer array result does not match", arraysMatch(sourceInts, (Integer[]) result));
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
