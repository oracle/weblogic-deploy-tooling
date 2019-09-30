/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.exception;

import java.text.MessageFormat;
import java.util.ResourceBundle;

/**
 * Exception-related helper methods.
 */
public final class ExceptionHelper {
    private static final String RESOURCE_BUNDLE_NAME = "oracle.weblogic.deploy.messages.wlsdeploy_rb";

    private ExceptionHelper() {
        // hide the constructor for this utility class
    }

    /**
     * Get the name of the WLS-DEPLOY Resource Bundle.
     *
     * @return the name of the WLS-DEPLOY Resource Bundle
     */
    public static String getResourceBundleName() {
        return RESOURCE_BUNDLE_NAME;
    }

    /**
     * Get the formatted message from the resource bundle populated with values in the arguments.
     * The method should only be used to set messages in non-BundleAwareExceptions since the
     * message key is lost.  For BundleAwareExceptions and log messages, pass the message key
     * and arguments directly to the exception constructor or the logging method.
     *
     * @param messageKey the message key
     * @param args the arguments to use to populatge the message placeholders.
     * @return the message
     */
    public static String getMessage(String messageKey, Object... args) {
        ResourceBundle bundle = ResourceBundle.getBundle(RESOURCE_BUNDLE_NAME);
        String message = bundle.getString(messageKey);
        if (args != null && args.length > 0) {
            message = MessageFormat.format(message, args);
        }
        return message;
    }
}
