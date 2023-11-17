/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.validate;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.StringUtils;

/**
 * The PasswordValidator class that works similar to the SystemPasswordValidator provider in WebLogic Server
 */
public class PasswordValidator {
    private static final String CLASS = PasswordValidator.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.validate");

    public static final String MAX_CONSECUTIVE_CHARACTERS = "MaxConsecutiveCharacters";
    public static final String MAX_INSTANCES_OF_ANY_CHARACTER = "MaxInstancesOfAnyCharacter";
    public static final String MAX_PASSWORD_LENGTH = "MaxPasswordLength";
    public static final String MIN_ALPHABETIC_CHARACTERS = "MinAlphabeticCharacters";
    public static final String MIN_LOWERCASE_CHARACTERS = "MinLowercaseCharacters";
    public static final String MIN_NON_ALPHANUMERIC_CHARACTERS = "MinNonAlphanumericCharacters";
    public static final String MIN_NUMERIC_CHARACTERS = "MinNumericCharacters";
    public static final String MIN_NUMERIC_OR_SPECIAL_CHARACTERS = "MinNumericOrSpecialCharacters";
    public static final String MIN_PASSWORD_LENGTH = "MinPasswordLength";
    public static final String MIN_UPPERCASE_CHARACTERS = "MinUppercaseCharacters";
    public static final String REJECT_EQUAL_OR_CONTAIN_REVERSE_USERNAME = "RejectEqualOrContainReverseUsername";
    public static final String REJECT_EQUAL_OR_CONTAIN_USERNAME = "RejectEqualOrContainUsername";

    private static final int NO_RESTRICTION = 0;
    private static final boolean NOT_SET = false;

    private static final char[] DISALLOWED_PASSWORD_START_CHARACTERS = { '{' };

    private final Map<String, Object> config;
    private final Map<String, Object> cieDefaults;
    private final Set<String> notifications;

    /**
     * The constructor.
     *
     * @param config      a map of the configuration values from the model
     * @param cieDefaults a map of the default values from the aliases
     */
    public PasswordValidator(Map<String, Object> config, Map<String, Object> cieDefaults) {
        this.config = config;
        this.cieDefaults = cieDefaults;
        this.notifications = new HashSet<>();
    }

    /**
     * Validate the password using the configured rules.
     *
     * @param username the username of the user whose password is being validated
     * @param pass     the password
     * @return true, if the password is valid; false otherwise
     * @throws ValidateException if the username (after trimming whitespace) or password is empty
     */
    public boolean validate(String username, String pass) throws ValidateException {
        final String METHOD = "validate";

        LOGGER.entering(CLASS, METHOD, username);
        String user = username.trim();

        if (StringUtils.isEmpty(user)) {
            ValidateException ex = new ValidateException("WLSDPLY-05400");
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        } else if (StringUtils.isEmpty(pass)) {
            ValidateException ex = new ValidateException("WLSDPLY-05401", user);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        boolean isValid = !validatePasswordLength(user, pass);
        if (validatePasswordDoesNotContainUsername(user, pass)) {
            isValid = false;
        }
        if (validatePasswordDoesNotContainReverseUsername(user, pass)) {
            isValid = false;
        }
        if (validatePasswordMaxInstancesOfCharacter(user, pass)) {
            isValid = false;
        }
        if (validatePasswordMaxConsecutiveCharacter(user, pass)) {
            isValid = false;
        }
        if (validatePasswordMinCharacterTypeRequirements(user, pass)) {
            isValid = false;
        }
        if (validatePasswordDisallowedStartCharacters(user, pass)) {
            isValid = false;
        }

        LOGGER.exiting(CLASS, METHOD, isValid);
        return isValid;
    }

    private boolean validatePasswordLength(String user, String pass) {
        final String METHOD = "validatePasswordLength";
        LOGGER.entering(CLASS, METHOD, user);

        boolean foundErrors = false;
        final int minLength = getIntegerFieldConfiguration(MIN_PASSWORD_LENGTH);
        final int maxLength = getIntegerFieldConfiguration(MAX_PASSWORD_LENGTH);
        if (minLength > NO_RESTRICTION && pass.length() < minLength) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05402", user, pass.length(), minLength);
        }
        if (maxLength > NO_RESTRICTION && pass.length() > maxLength) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05403", user, pass.length(), maxLength);
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private boolean validatePasswordDoesNotContainUsername(String user, String pass) {
        final String METHOD = "validatePasswordDoesNotContainUsername";
        LOGGER.entering(CLASS, METHOD, user);

        boolean foundErrors = false;
        final boolean checkForUserName = getBooleanFieldConfiguration(REJECT_EQUAL_OR_CONTAIN_USERNAME);
        if (checkForUserName) {
            int index = pass.toLowerCase().indexOf(user.toLowerCase());
            if (index >= 0) {
                foundErrors = true;
                LOGGER.severe("WLSDPLY-05404", user);
            }
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private boolean validatePasswordDoesNotContainReverseUsername(String user, String pass) {
        final String METHOD = "validatePasswordDoesNotContainReverseUsername";
        LOGGER.entering(CLASS, METHOD, user);

        boolean foundErrors = false;
        final boolean checkForUserName = getBooleanFieldConfiguration(REJECT_EQUAL_OR_CONTAIN_REVERSE_USERNAME);
        if (checkForUserName) {
            String reversedUser = new StringBuffer(user).reverse().toString();
            int index = pass.toLowerCase().indexOf(reversedUser.toLowerCase());
            if (index >= 0) {
                foundErrors = true;
                LOGGER.severe("WLSDPLY-05405", user, reversedUser);
            }
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private boolean validatePasswordMaxInstancesOfCharacter(String user, String pass) {
        final String METHOD = "validatePasswordMaxInstancesOfCharacter";
        LOGGER.entering(CLASS, METHOD, user);

        boolean foundErrors = false;
        final int maxInstancesOfChar = getIntegerFieldConfiguration(MAX_INSTANCES_OF_ANY_CHARACTER);
        if (maxInstancesOfChar > NO_RESTRICTION) {
            Map<Character, Integer> characterCountMap = new HashMap<>();
            for (int i = 0; i < pass.length(); i++) {
                char c = pass.charAt(i);
                incrementCharacterCount(characterCountMap, c);
            }

            // Look for errors.
            for (Map.Entry<Character, Integer> entry : characterCountMap.entrySet()) {
                char c = entry.getKey();
                int count = entry.getValue();
                if (count > maxInstancesOfChar) {
                    foundErrors = true;
                    LOGGER.severe("WLSDPLY-05406", user, maxInstancesOfChar, count, String.valueOf(c));
                }
            }
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private boolean validatePasswordMaxConsecutiveCharacter(String user, String pass) {
        final String METHOD = "validatePasswordMaxConsecutiveCharacter";
        LOGGER.entering(CLASS, METHOD, user);

        boolean foundErrors = false;
        int maxConsecutiveChars = getIntegerFieldConfiguration(MAX_CONSECUTIVE_CHARACTERS);
        if (maxConsecutiveChars > NO_RESTRICTION) {
            char lastChar = 0;
            int count = 0;
            for (int i = 0; i < pass.length(); i++) {
                char c = pass.charAt(i);
                if (c == lastChar) {
                    count++;
                } else {
                    if (count > maxConsecutiveChars) {
                        foundErrors = true;
                        LOGGER.severe("WLSDPLY-05407", user, maxConsecutiveChars, count, lastChar);
                    }
                    lastChar = c;
                    count = 1;
                }
            }
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private boolean validatePasswordMinCharacterTypeRequirements(String user, String pass) {
        final String METHOD = "validatePasswordMinCharacterTypeRequirements";
        LOGGER.entering(CLASS, METHOD, user);

        int minAlphabeticChars = getIntegerFieldConfiguration(MIN_ALPHABETIC_CHARACTERS);
        int minNumericChars = getIntegerFieldConfiguration(MIN_NUMERIC_CHARACTERS);
        int minNonAlphanumericChars = getIntegerFieldConfiguration(MIN_NON_ALPHANUMERIC_CHARACTERS);
        int minLowercaseChars = getIntegerFieldConfiguration(MIN_LOWERCASE_CHARACTERS);
        int minUppercaseChars = getIntegerFieldConfiguration(MIN_UPPERCASE_CHARACTERS);
        int minNumericOrSpecialChars = getIntegerFieldConfiguration(MIN_NUMERIC_OR_SPECIAL_CHARACTERS);

        int alphabeticCount = 0;
        int numericCount = 0;
        int nonAlphanumericCount = 0;
        int lowercaseCount = 0;
        int uppercaseCount = 0;
        int numericOrSpecialCount = 0;
        for (int i = 0; i < pass.length(); i++) {
            char c = pass.charAt(i);
            if (Character.isLowerCase(c)) {
                alphabeticCount++;
                lowercaseCount++;
            } else if (Character.isUpperCase(c)) {
                alphabeticCount++;
                uppercaseCount++;
            } else if (Character.isDigit(c)) {
                numericCount++;
                numericOrSpecialCount++;
            } else {
                nonAlphanumericCount++;
                numericOrSpecialCount++;
            }
        }

        boolean foundErrors = false;
        if (minAlphabeticChars > NO_RESTRICTION && alphabeticCount < minAlphabeticChars) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05408", user, alphabeticCount, minAlphabeticChars);
        }
        if (minNumericChars > NO_RESTRICTION && numericCount < minNumericChars) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05409", user, numericCount, minNumericChars);
        }
        if (minLowercaseChars > NO_RESTRICTION && lowercaseCount < minLowercaseChars) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05410", user, lowercaseCount, minLowercaseChars);
        }
        if (minUppercaseChars > NO_RESTRICTION && uppercaseCount < minUppercaseChars) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05411", user, uppercaseCount, minUppercaseChars);
        }
        if (minNonAlphanumericChars > NO_RESTRICTION && nonAlphanumericCount < minNonAlphanumericChars) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05412", user, uppercaseCount, minNonAlphanumericChars);
        }
        if (minNumericOrSpecialChars > NO_RESTRICTION && numericOrSpecialCount < minNumericOrSpecialChars) {
            foundErrors = true;
            LOGGER.severe("WLSDPLY-05413", user, numericOrSpecialCount, minNumericOrSpecialChars);
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private boolean validatePasswordDisallowedStartCharacters(String user, String pass) {
        final String METHOD = "validatePasswordDisallowedStartCharacters";
        LOGGER.entering(CLASS, METHOD, user);

        boolean foundErrors = false;
        char startChar = pass.charAt(0);
        for (char c : DISALLOWED_PASSWORD_START_CHARACTERS) {
            if (startChar == c) {
                foundErrors = true;
                LOGGER.severe("WLSDPLY-05414", user, String.valueOf(c));
            }
        }

        LOGGER.exiting(CLASS, METHOD, foundErrors);
        return foundErrors;
    }

    private int getIntegerFieldConfiguration(String fieldName) {
        int result = NO_RESTRICTION;
        if (config.containsKey(fieldName)) {
            Object value = config.get(fieldName);
            if (Integer.class.isAssignableFrom(value.getClass())) {
                result = (int) value;
            }
        }
        if (cieDefaults.containsKey(fieldName)) {
            Object value = cieDefaults.get(fieldName);
            if (Integer.class.isAssignableFrom(value.getClass())) {
                int cieDefault  = (int) value;

                if (cieDefault > result) {
                    if (result != NO_RESTRICTION && !notifications.contains(fieldName)) {
                        LOGGER.notification("WLSDPLY-05415", fieldName, result, cieDefault);
                        notifications.add(fieldName);
                    }
                    result = cieDefault;
                }
            }
        }
        return result;
    }

    private boolean getBooleanFieldConfiguration(String fieldName) {
        boolean result = NOT_SET;
        if (config.containsKey(fieldName)) {
            Object value = config.get(fieldName);
            if (Boolean.class.isAssignableFrom(value.getClass())) {
                result = (Boolean) value;
            }
        } else if (cieDefaults.containsKey(fieldName)) {
            Object value = cieDefaults.get(fieldName);
            if (Boolean.class.isAssignableFrom(value.getClass())) {
                result = (Boolean) value;
            }
        }
        return result;
    }

    private void incrementCharacterCount(Map<Character, Integer> charCountMap, Character c) {
        int count = 0;
        if (charCountMap.containsKey(c)) {
            count = charCountMap.get(c);
        }
        count++;
        charCountMap.put(c, count);
    }
}
