/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import oracle.weblogic.deploy.exception.BundleAwareException;
import oracle.weblogic.deploy.exception.ExceptionHelper;

/**
 * This exception represents general IOExceptions that occur during WLSDeployArchive operations.
 */
public class WLSDeployArchiveIOException extends BundleAwareException {
    private static final long serialVersionUID = 1L;

    /**
     * Constructs a default exception.
     */
    public WLSDeployArchiveIOException() {
        super();
    }

    /**
     * The constructor used to specify the error message ID.
     *
     * @param messageId The error message ID to use.
     */
    public WLSDeployArchiveIOException(String messageId) {
        super(messageId);
    }

    /**
     * The constructor used to specify the error message ID and the parameters to use to construct
     * the exception message.
     *
     * @param messageId The error message ID to use.
     * @param params    The list os parameters to use to fill in the tokens of the error message. These tokens
     *                  must either be Strings or return the desired String from their toString() methods.
     */
    public WLSDeployArchiveIOException(String messageId, Object... params) {
        super(messageId, params);
    }

    /**
     * The constructor used to specify the error message ID to use and the exception that caused the error.
     *
     * @param messageId The error message ID to use.
     * @param cause     The exception that causes the error.
     */
    public WLSDeployArchiveIOException(String messageId, Throwable cause) {
        super(messageId, cause);
    }

    /**
     * The constructor used to specify the error message ID and the parameters to use to construct the
     * exception message as well as the exception that caused the error.
     *
     * @param messageId The error message ID to use.
     * @param cause     The exception that causes the error.
     * @param params    The list os parameters to use to fill in the tokens of the error message. These tokens
     *                  must either be Strings or return the desired String from their toString() methods.
     */
    public WLSDeployArchiveIOException(String messageId, Throwable cause, Object... params) {
        super(messageId, cause, params);
    }

    @Override
    public String getBundleName() {
        return ExceptionHelper.getResourceBundleName();
    }
}
