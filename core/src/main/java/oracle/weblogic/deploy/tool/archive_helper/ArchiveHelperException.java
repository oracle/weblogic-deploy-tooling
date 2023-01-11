/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper;

import oracle.weblogic.deploy.exception.BundleAwareException;
import oracle.weblogic.deploy.exception.ExceptionHelper;

public class ArchiveHelperException extends BundleAwareException {
    private static final long serialVersionUID = 1L;

    private final int exitCode;

    /**
     * Constructs a default exception with exit code of 2.
     */
    public ArchiveHelperException() {
        this.exitCode = 2;
    }

    /**
     * Construct a default exception with specified exit code
     * @param exitCode the exit code to use
     */
    public ArchiveHelperException(int exitCode) {
        this.exitCode = exitCode;
    }

    /**
     * Constructs a new exception with the specified message id.
     *
     * @param exitCode  the exit code to use
     * @param messageID the message ID
     */
    public ArchiveHelperException(int exitCode, String messageID) {
        super(messageID);
        this.exitCode = exitCode;
    }

    /**
     * Constructs a new exception with the specified message id and parameters.
     *
     * @param exitCode  the exit code to use
     * @param messageID the message ID
     * @param params    the parameters to use to fill in the message tokens
     */
    public ArchiveHelperException(int exitCode, String messageID, Object... params) {
        super(messageID, params);
        this.exitCode = exitCode;
    }

    /**
     * Constructs a new exception with the specified message id and cause.
     *
     * @param exitCode  the exit code to use
     * @param messageID the message ID
     * @param cause     the exception that triggered the creation of this exception
     */
    public ArchiveHelperException(int exitCode, String messageID, Throwable cause) {
        super(messageID, cause);
        this.exitCode = exitCode;
    }

    /**
     * Constructs a new exception with passed message id, cause, and parameters.
     *
     * @param exitCode  the exit code to use
     * @param messageID the message ID
     * @param cause     the exception that triggered the creation of this exception
     * @param params    the parameters to use to fill in the message tokens
     */
    public ArchiveHelperException(int exitCode, String messageID, Throwable cause, Object... params) {
        super(messageID, cause, params);
        this.exitCode = exitCode;
    }

    /**
     * Constructs a new exception with the specified cause.
     *
     * @param exitCode  the exit code to use
     * @param cause the exception that triggered the creation of this exception
     */
    public ArchiveHelperException(int exitCode, Throwable cause) {
        super(cause);
        this.exitCode = exitCode;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public String getBundleName() {
        return ExceptionHelper.getResourceBundleName();
    }

    /**
     * Get the exit code associated with this exception.
     *
     * @return the exit code associated with this exception
     */
    public int getExitCode() {
        return this.exitCode;
    }
}
