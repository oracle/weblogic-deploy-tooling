/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.encrypt;

import oracle.weblogic.deploy.exception.BundleAwareException;
import oracle.weblogic.deploy.exception.ExceptionHelper;

/**
 * The exception used by the encryption utilities.
 */
public class EncryptionException extends BundleAwareException {
    private static final long serialVersionUID = 1L;

    /**
     * Constructs a default exception.
     */
    public EncryptionException() {
        // default constructor
    }

    /**
     * Constructs a new exception with the specified message id.
     *
     * @param messageID the message ID
     */
    public EncryptionException(String messageID) {
        super(messageID);
    }

    /**
     * Constructs a new exception with the specified message id and parameters.
     *
     * @param messageID the message ID
     * @param params    the parameters to use to fill in the message tokens
     */
    public EncryptionException(String messageID, Object... params) {
        super(messageID, params);
    }

    /**
     * Constructs a new exception with the specified message id and cause.
     *
     * @param messageID the message ID
     * @param cause     the exception that triggered the creation of this exception
     */
    public EncryptionException(String messageID, Throwable cause) {
        super(messageID, cause);
    }

    /**
     * Constructs a new exception with passed message id, cause, and parameters.
     *
     * @param messageID the message ID
     * @param cause     the exception that triggered the creation of this exception
     * @param params    the parameters to use to fill in the message tokens
     */
    public EncryptionException(String messageID, Throwable cause, Object... params) {
        super(messageID, cause, params);
    }

    /**
     * Constructs a new exception with the specified cause.
     *
     * @param cause the exception that triggered the creation of this exception
     */
    public EncryptionException(Throwable cause) {
        super(cause);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public String getBundleName() {
        return ExceptionHelper.getResourceBundleName();
    }
}
