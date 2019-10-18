/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.ParsingErrorListener;

/**
 * The JsonErrorListener is the error listener used by the Antlr JSON parser to collect error counts
 * and convert the errors into messages that can be used to throw exceptions.
 */
public class JsonErrorListener extends ParsingErrorListener {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.json");

    /**
     * The constructor.
     *
     * @param fileName the name of the JSON file being parsed
     */
    public JsonErrorListener(String fileName) {
        super(fileName);
    }

    /**
     * The constructor used to control the reporting level of the Antlr DiagnosticErrorListener,
     * which this class extends.
     *
     * @param fileName the name of the JSON file being parsed
     * @param exactOnly whether or not the listener should only report exact ambiguities or not
     */
    public JsonErrorListener(String fileName, boolean exactOnly) {
        super(fileName, exactOnly);
    }

    protected PlatformLogger getLogger() {
        return LOGGER;
    }

}
