/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.util.List;
import java.util.Properties;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Utility methods for string manipulation.
 */
public final class StringUtils {

    private static final int KEY_VALUE_LIST_LENGTH = 2;
    private static final String COMMA_SEPARATED_LIST_SPLITTER = "[ \t]*,[ \t]*";

    private StringUtils() {
        // hide the constructor for this utility class
    }

    /**
     * Test to see if the string is null or empty.
     *
     * @param string the string to test
     * @return true if the string is null or of zero length
     */
    public static boolean isEmpty(String string) {
        return string == null || string.isEmpty();
    }

    /**
     * Convert a list of strings into a string containing the list elements separated by commas.
     *
     * @param list the list of strings
     * @return a string containing the list elements separated by commas
     */
    public static String getCommaSeparatedListString(List<String> list) {
        return getStringFromList(list, ',');
    }

    /**
     * Convert a list of strings into a string containing the list elements separated by the specified separator.
     *
     * @param list the list of strings
     * @param separator the separator to use
     * @return a string containing the list elements separated by commas
     */
    public static String getStringFromList(List<String> list, char separator) {
        if (list == null || list.isEmpty()) {
            return "";
        }
        StringBuilder buf = new StringBuilder();
        boolean isFirst = true;
        for (String element : list) {
            if (!isFirst) {
                buf.append(separator);
            } else {
                isFirst = false;
            }
            buf.append(element);
        }
        return buf.toString();
    }

    /**
     * Strip surrounding quotes from the string, if they are present.
     *
     * @param string the string from which to remove the surround quotes
     * @return the string without any surrounding quotes or the string itself if no quotes were present
     */
    public static String stripQuotes(String string) {
        String result = string;
        if (!StringUtils.isEmpty(string) && string.length() > 1) {
            char first = string.charAt(0);
            char last = string.charAt(string.length() - 1);
            if ((first == '"' && last == '"') || (first == '\'' && last == '\'')) {
                result = string.substring(1, string.length() - 1);
            }
        }
        return result;
    }

    /**
     * Add surrounding quotes to the string, if not already present.
     *
     * @param string the string to surround with double quotes
     * @return the string with surrounding double quotes or the string itself is single or double quotes were present
     */
    public static String quoteString(String string) {
        String result = "\"" + string + "\"";
        if (!StringUtils.isEmpty(string) && string.length() > 1) {
            char first = string.charAt(0);
            char last = string.charAt(string.length() - 1);
            if ((first == '"' && last == '"') || (first == '\'' && last == '\'')) {
                result = string;
            }
        }
        return result;
    }

    /**
     * Determine if the provided string value matches the provided pattern.
     *
     * @param patternString regex to apply to the string value
     * @param matches       string value to test for pattern
     * @return true if the string value matches the regex pattern
     */
    public static boolean matches(String patternString, String matches) {
        return !(patternString == null || matches == null) && matches(Pattern.compile(patternString), matches);
    }

    /**
     * Determine if the provided string value matches the provided java Pattern. This method will
     * allow you to cache a compiled version of the pattern for multiple calls to this method.
     * @param pattern compiled Pattern with regexp to apply to the string value
     * @param matches string value to test for pattern
     * @return true if the string value matches the regex pattern
     */
    public static boolean matches(Pattern pattern, String matches) {
        Matcher matcher = pattern.matcher(matches);
        return matcher.matches();
    }

    /**
     * Create a Properties object from the key=value pairs in the weblogic formatted properties string.
     *
     * @param stringProperties properties string of key=value pairs
     * @return Properties object from the key=value pairs
     */
    public static Properties formatPropertiesFromString(String stringProperties) {
        Properties properties = new Properties();
        if (!StringUtils.isEmpty(stringProperties)) {
            String[] split;
            if (stringProperties.contains(";")) {
                split = stringProperties.split(";");
            } else {
                split = stringProperties.split(",");
            }
            if (split.length > 0) {
                for (String property : split) {
                    if (!StringUtils.isEmpty(property)) {
                        String[] entry = property.split("=");
                        if (entry.length == KEY_VALUE_LIST_LENGTH) {
                            properties.setProperty(entry[0], entry[1]);
                        }
                    }
                }
            }
        }
        return properties;
    }

    /**
     * Return an array of Strings from the provided comma separated list
     * @param listString containing comma separated strings.
     * @return String[] from string or empty array if the listString is null or empty
     */
    public static String[] splitCommaSeparatedList(String listString) {
        if (StringUtils.isEmpty(listString)) {
            return new String[0];
        }
        return listString.split(COMMA_SEPARATED_LIST_SPLITTER);
    }

    /**
     * Return a printable string representing the Boolean True or False value for the integer.
     * @param value containing the integer value of a boolean
     * @return String representation of the boolean integer
     */
    public static String stringForBoolean(int value) {
        switch(value) {
            case 0:
                return Boolean.FALSE.toString();
            case 1:
                return Boolean.TRUE.toString();
            default:
                return "UNKNOWN";
        }
    }

    /***
     * Convert the String to an Integer. If the string does not contain a valid integer, return a null.
     * @param value String to convert to an Integer
     * @return converted Integer or null if invalid number
     */
    public static Integer stringToInteger(String value) {
        try {
            return Integer.valueOf(value);
        } catch (NumberFormatException nfe) {
            return null;
        }
    }

}
