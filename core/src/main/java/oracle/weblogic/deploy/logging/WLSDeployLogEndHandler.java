/*
 * Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.logging;

/**
 * This interface should be used by a Log Handler that wishes to perform some action or clean-up
 * before ending within a weblogic deploy tool. A class that implements this interface should include
 * the appropriate wrap-up action in the logEnd method.
 *
 * The corresponding WLSDeployExit will look through the Handlers on the LogManager and call the logEnd
 * method if the interface is implemented.
 */
public interface WLSDeployLogEndHandler {

    void logEnd(boolean online);

}