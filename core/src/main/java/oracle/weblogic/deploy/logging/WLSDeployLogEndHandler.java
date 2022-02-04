/*
 * Copyright (c) 2018, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Handler;

import oracle.weblogic.deploy.util.WLSDeployContext;

import static oracle.weblogic.deploy.logging.WLSDeployLoggingConfig.WLSDEPLOY_SUMMARY_HANDLER;

/**
 * This abstract class must be extended by any handler that wishes to perform some action or clean-up
 * before the wlsdeploy tool exits. A class that extends this class should include the appropriate wrap-up
 * action in its logEnd method.
 *
 * <p>If the tool calls the WLSDeployExit.exit(), that method will search the Handlers on all WLSDEPLOY
 * loggers. If a handler implements this interface, the logEnd method is called. The handlers' methods are called
 * in parent / child order. If the same handler instance is found on more than one logger, the handler is only called
 * once, with parent / child order insured for all.
 *
 * @see oracle.weblogic.deploy.util.WLSDeployExit
 */
public abstract class WLSDeployLogEndHandler extends Handler {
    private static final List<WLSDeployLogEndHandler> endHandlers = new ArrayList<>(1);

    /**
     * The constructor.
     */
    protected WLSDeployLogEndHandler() {
        synchronized (WLSDeployLogEndHandler.class) {
            endHandlers.add(this);
        }
    }

    /**
     * Get the list of handlers that are WLSDeployLogEndHandlers.
     *
     * @return the list of handlers that are WLSDeployLogEndHandlers
     */
    public static synchronized List<WLSDeployLogEndHandler> getEndHandlers() {
        return new ArrayList<>(endHandlers);
    }

    /**
     * Get the SummaryHandler instance.
     *
     * @return the SummaryHandler or null if there is no SummaryHandler instance
     */
    public static synchronized WLSDeployLogEndHandler getSummaryHandler() {
        WLSDeployLogEndHandler summaryHandler = null;
        for (WLSDeployLogEndHandler handler : endHandlers) {
            if (WLSDEPLOY_SUMMARY_HANDLER.equals(handler.getClass().getName())) {
                summaryHandler = handler;
                break;
            }
        }
        return summaryHandler;
    }

    // For Python unit tests only
    @SuppressWarnings("unused")
    public static synchronized void clearHandlers() {
        endHandlers.clear();
    }

    /**
     * Invoke the logEnd() method on every WLSDeployLogEndHandler handler.
     *
     * @param context the context object
     */
    @SuppressWarnings("unused")
    public static synchronized void closeLog(WLSDeployContext context) {
        for (WLSDeployLogEndHandler endHandler : endHandlers) {
            endHandler.logEnd(context);
        }
    }

    /**
     * The handler performs any wrap-up action.
     *
     * @param context containing contextual information about the tool
     */
    public abstract void logEnd(WLSDeployContext context);
}
