/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.ParsingErrorListener;

/**
 * The YamlErrorListener is the error listener used by the Antlr YAML parser to collect error counts
 * and convert the errors into messages that can be used to throw exceptions.
 */
public class YamlErrorListener extends ParsingErrorListener {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.yaml");

    /**
     * The constructor.
     *
     * @param fileName the name of the YAML file being parsed
     */
    public YamlErrorListener(String fileName) {
        super(fileName);
    }

    /**
     * The constructor used to control the reporting level of the Antlr DiagnosticErrorListener,
     * which this class extends.
     *
     * @param fileName the name of the YAML file being parsed
     * @param exactOnly whether or not the listener should only report exact ambiguities or not
     */
    public YamlErrorListener(String fileName, boolean exactOnly) {
        super(fileName, exactOnly);
    }

    protected PlatformLogger getLogger() {
        return LOGGER;
    }
}
