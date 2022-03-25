/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.exception;

import java.text.MessageFormat;
import java.util.Locale;
import java.util.MissingResourceException;
import java.util.ResourceBundle;

import oracle.weblogic.deploy.util.StringUtils;

/**
 * The base class for resource bundle aware exceptions.
 */
public abstract class BundleAwareException extends Exception {
    private static final long serialVersionUID = 1L;
    private static final int DEFAULT_BUFFER_SIZE = 128;

    /**
     * Message id, for example "WLSDPLY-02001".
     */
    private String messageID;

    /**
     * Array of parameters to the message.
     */
    private transient Object[] params;

    /**
     * Flag set to true in the case where the exception was created with a cause, but with no message set. In that case,
     * and IFF cause is itself a BundleAwareException, we copy the contents of the cause, such that our fancy locale
     * awareness works as expected. Refer bug 13740123.
     */
    private boolean messageFromCause;

    /**
     * Constructs a default exception.
     */
    protected BundleAwareException() {
        super();
    }

    /**
     * Constructs a new exception with the specified message id.
     *
     * @param messageID the message to use
     */
    protected BundleAwareException(String messageID) {
        super();
        this.messageID = messageID;
    }

    /**
     * Constructs a new exception with the specified message id and parameters.
     *
     * @param messageID the message to use
     * @param params the arguments to use to fill in the placeholders in the message
     */
    protected BundleAwareException(String messageID, Object... params) {
        super();
        this.messageID = messageID;
        this.params = params;
    }

    /**
     * Constructs a new exception with the specified message id and cause.
     *
     * @param messageID the message to use
     * @param cause the nested exception
     */
    protected BundleAwareException(String messageID, Throwable cause) {
        super(cause);
        if (messageID != null) {
            this.messageID = messageID;
        } else if (cause != null) {
            copyFromCause(cause);
        }
    }

    /**
     * Constructs a new exception with passed message id, cause, and parameters.
     *
     * @param messageID the message to use
     * @param cause the nested exception
     * @param params the arguments to use to fill in the placeholders in the message
     */
    protected BundleAwareException(String messageID, Throwable cause, Object... params) {
        super(cause);
        if (messageID != null) {
            this.messageID = messageID;
            this.params = params;
        } else if (cause != null) {
            // This means that if any params were passed, those will be ignored. But
            // given no message was passed to apply them to, this is correct...
            copyFromCause(cause);
        }
    }

    /**
     * Constructs a new exception with the specified cause.
     *
     * @param cause the nested exception
     */
    protected BundleAwareException(Throwable cause) {
        super(cause);
        if (cause != null) {
            copyFromCause(cause);
        }
    }

    /**
     * Returns the class name of the ResourceBundle holding messages for this component. It's required this
     * be overridden by the top-level exception class for each component.
     *
     * @return the ResourceBundle name
     */
    public abstract String getBundleName();

    /**
     * Returns the same string as {@link #getMessage()}. Invoking it is the default <code>Throwable</code>
     * behavior, but this method declares that to be our expected/supported behavior as well.
     *
     * @return the formatted message
     */
    @Override
    public String getLocalizedMessage() {
        if (messageFromCause) {
            return getCause().getLocalizedMessage();
        } else {
            return getMessage(Locale.getDefault());
        }
    }

    /**
     * Returns the message id that was passed in on creation, if any.
     *
     * @return the messageID or null
     */
    public String getMessageID() {
        return messageID;
    }

    /**
     * {@inheritDoc} In addition, the message id is included as a separate field from the message itself if those are
     * distinct.
     */
    @Override
    public String toString() {
        boolean isBundleKey = false;
        String pattern = searchBundle(Locale.getDefault());
        if (pattern != null) {
            isBundleKey = true;
        }

        if (isBundleKey) {
            StringBuilder sb = new StringBuilder(DEFAULT_BUFFER_SIZE);

            sb.append(this.getClass().getName());
            sb.append(": ");

            if (messageFromCause) {
                // ...then instead of using our copy of the data, we should let cause
                // print itself. Its class name will be included, any further chaining
                // needed will occur, and so we remain compatible with Exception behavior.
                sb.append(getCause());
            } else {
                sb.append(getMessageID());
                sb.append(": ");
                sb.append(getMessage());
            }
            return sb.toString();
        } else {
            return super.toString();
        }
    }

    /**
     * Returns the detail message string associated with the message id for the current locale. If not found, the
     * message id itself is returned. If there is no message id, either cause details (if a cause was set) or null.
     *
     * @return the formatted message
     */
    @Override
    public String getMessage() {
        if (messageFromCause) {
            return getCause().getMessage();
        } else {
            return getMessage(Locale.getDefault());
        }
    }

    ///////////////////////////////////////////////////////////////////////////
    // Non-public helper methods.                                            //
    ///////////////////////////////////////////////////////////////////////////

    /**
     * Returns the detail message string associated with the message id for the requested locale, if available. If not
     * found, the message id itself is returned. If there is no message id, either cause details (if a cause was set) or
     * null.
     *
     * @param locale the locale to use to retrieve the message
     * @return the message string or null, if not found
     */
    private String getMessage(Locale locale) {
        String pattern = searchBundle(locale);
        if (pattern == null) {
            pattern = messageID;
        }
        if (pattern == null) {
            // We have no message, which is the case if we were created with a simple
            // string message (unlikely and probably bad), or we are wrapping a cause
            // which is not itself a BundleAwareException.
            // Let Exception deal with it.
            return super.getMessage();
        } else {
            MessageFormat mf = new MessageFormat(pattern, locale);
            return mf.format(params, new StringBuffer(DEFAULT_BUFFER_SIZE), null).toString();
        }
    }

    /**
     * Returns the unprocessed message params. This is only for interaction between two BundleAwareExceptions.
     *
     * @return the array of message param objects
     */
    Object[] getMessageParams() {
        return params;
    }

    /**
     * Looks for a message in the bundle, using the message id as the key, for the passed locale.
     * Either the found message or null is returned.
     *
     * @param locale the locale to use to retrieve the message
     * @return the message or null, if not found
     */
    private String searchBundle(Locale locale) {
        return getPatternFromBundle(messageID, getBundleName(), locale);
    }

    // Also used by BundleAwareRuntimeException...
    static String getPatternFromBundle(String msgId, String bundleName, Locale locale) {
        String pattern = null;
        if (!StringUtils.isEmpty(msgId)) {
            try {
                ClassLoader cl = Thread.currentThread().getContextClassLoader();
                ResourceBundle bundle = ResourceBundle.getBundle(bundleName, locale, cl);
                pattern = bundle.getString(msgId);
            } catch (MissingResourceException mre) {
                // OK, not found.
            }
        }
        return pattern;
    }

    private void copyFromCause(Throwable cause) {
        if (cause instanceof BundleAwareException) {
            BundleAwareException te = (BundleAwareException) cause;
            this.messageID = te.getMessageID();
            this.params = te.getMessageParams();
            this.messageFromCause = true;
        }
    }
}
