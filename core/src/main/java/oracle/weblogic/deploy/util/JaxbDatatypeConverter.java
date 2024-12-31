/*
 * Copyright (c) 2024, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * A utility class that acts as an abstraction layer to JAXB classes so that
 * we can operate with either javax or jakarta package implementation classes.
 */
public class JaxbDatatypeConverter {
    private static final String CLASS = JaxbDatatypeConverter.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    private static final String JAVAX_DATATYPE_CONVERTER_CLASS_NAME = "javax.xml.bind.DatatypeConverter";
    private static final String JAKARTA_DATATYPE_CONVERTER_CLASS_NAME = "jakarta.xml.bind.DatatypeConverter";

    private static final Class<?> DATATYPE_CONVERTER_CLASS;

    static {
        Class<?> datatypeConverterClass = null;
        try {
            datatypeConverterClass =
                JaxbDatatypeConverter.class.getClassLoader().loadClass(JAVAX_DATATYPE_CONVERTER_CLASS_NAME);
        } catch (ClassNotFoundException e) {
            LOGGER.fine("WLSDPLY-08600", JAVAX_DATATYPE_CONVERTER_CLASS_NAME, e.getLocalizedMessage());

            try {
                datatypeConverterClass =
                    JaxbDatatypeConverter.class.getClassLoader().loadClass(JAKARTA_DATATYPE_CONVERTER_CLASS_NAME);
            } catch (ClassNotFoundException e2) {
                LOGGER.fine("WLSDPLY-08600", JAKARTA_DATATYPE_CONVERTER_CLASS_NAME, e.getLocalizedMessage());

                WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08601", JAVAX_DATATYPE_CONVERTER_CLASS_NAME,
                    JAKARTA_DATATYPE_CONVERTER_CLASS_NAME);
                LOGGER.throwing(CLASS, "static initializer", ex);
            }
        }
        DATATYPE_CONVERTER_CLASS = datatypeConverterClass;
    }

    public static String printBase64Binary(byte[] val) throws WdtJaxbException {
        final String METHOD = "printBase64Binary";
        LOGGER.entering(CLASS, METHOD);

        String result = null;
        try {
            Method method = getPrintBase64BinaryMethod();
            result = (String) method.invoke(null, (Object) val);
        } catch (IllegalAccessException | IllegalArgumentException | InvocationTargetException | SecurityException e) {
           WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08603", e, METHOD, e.getLocalizedMessage());
           LOGGER.throwing(CLASS, METHOD, ex);
           throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    public static byte[] parseBase64Binary(String val) throws WdtJaxbException {
        final String METHOD = "parseBase64Binary";
        LOGGER.entering(CLASS, METHOD);

        byte[] result = new byte[] {};
        try {
            Method method = getParseBase64BinaryMethod();
            result = (byte[]) method.invoke(null, val);
        } catch (IllegalAccessException | IllegalArgumentException | InvocationTargetException | SecurityException e) {
            WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08603", e, METHOD, e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    public static String printHexBinary(byte[] val) throws WdtJaxbException {
        final String METHOD = "printHexBinary";
        LOGGER.entering(CLASS, METHOD);

        String result = null;
        try {
            Method method = getPrintHexBinaryMethod();
            result = (String) method.invoke(null, (Object) val);
        } catch (IllegalAccessException | IllegalArgumentException | InvocationTargetException | SecurityException e) {
            WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08603", e, METHOD, e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    private static Method getPrintBase64BinaryMethod() throws WdtJaxbException {
        final String METHOD = "getPrintBase64BinaryMethod";
        LOGGER.entering(CLASS, METHOD);

        Method method;
        try {
            method = DATATYPE_CONVERTER_CLASS.getMethod("printBase64Binary", byte[].class);
        } catch (NoSuchMethodException | SecurityException e) {
            WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08602", e, "printBase64Binary", e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD, method);
        return method;
    }

    private static Method getPrintHexBinaryMethod() throws WdtJaxbException {
        final String METHOD = "getPrintHexBinaryMethod";
        LOGGER.entering(CLASS, METHOD);

        Method method;
        try {
            method = DATATYPE_CONVERTER_CLASS.getMethod("printHexBinary", byte[].class);
        } catch (NoSuchMethodException | SecurityException e) {
            WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08602", e, "printHexBinary", e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD, method);
        return method;
    }

    private static Method getParseBase64BinaryMethod() throws WdtJaxbException {
        final String METHOD = "getParseBase64BinaryMethod";
        LOGGER.entering(CLASS, METHOD);

        Method method;
        try {
            method = DATATYPE_CONVERTER_CLASS.getMethod("parseBase64Binary", String.class);
        } catch (NoSuchMethodException | SecurityException e) {
            WdtJaxbException ex = new WdtJaxbException("WLSDPLY-08602", e, "parseBase64Binary", e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD, method);
        return method;
    }
}
