/*
 * Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import oracle.weblogic.deploy.util.WLSDeployContext;

/**
 * This interface should be used by a Logger Handler that wishes to perform some action or clean-up
 * before the wlsdeploy tool exits. A class that implements this interface should include
 * the appropriate wrap-up action in the logEnd method.
 *
 * <p>If the tool calls the WLSDeployExit.exit(), that method will search the Handlers on all WLSDEPLOY
 * loggers. If a handler implements this interface, the logEnd method is called. The handlers' methods are called
 * in parent / child order. If the same handler instance is found on more than one logger, the handler is only called
 * once, with parent / child order insured for all.
 *
 * @see oracle.weblogic.deploy.util.WLSDeployExit
 */
public interface WLSDeployLogEndHandler {

    /**
     * The handler performs any wrap-up action.
     *
     * @param context containing contextual information about the tool
     */
    void logEnd(WLSDeployContext context);

}