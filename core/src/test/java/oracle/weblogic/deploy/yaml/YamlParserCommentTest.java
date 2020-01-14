/*
 * Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import org.junit.Before;
import org.junit.Test;

import java.io.File;
import java.util.Map;

/**
 * Verifies the parsing of files with an assortment of comment styles.
 */
public class YamlParserCommentTest {
    private static final boolean DEBUG = System.getProperty("DEBUG") != null;
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.yaml");
    private static final File YAML_FILE =
            new File("src/test/resources/yaml/comment-model.yaml").getAbsoluteFile();

    private YamlJavaTranslator translator;
    private Map<String, Object> fileDict;

    @Before
    public void init() throws Exception {
        translator = new YamlJavaTranslator(YAML_FILE.getPath());
        fileDict = translator.parse();

        if (DEBUG) {
            LOGGER.info("fileDict = " + fileDict.toString());
        }
    }

    @Test
    public void testParseComments() throws Exception {
        translator.checkForParseErrors();
        if (DEBUG) {
            StringBuilder builder = new StringBuilder("\n");
            dumpMap(fileDict, builder, "");
            LOGGER.info(builder.toString());
        }
    }

    @SuppressWarnings("WeakerAccess")
    static void dumpMap(Map<?, ?> map, StringBuilder builder, String indent) {
        for(Object key: map.keySet()) {
            Object value = map.get(key);
            if(value instanceof Map) {
                builder.append(indent + key + ":\n");
                dumpMap((Map<?, ?>) value, builder, indent + "    ");
            } else {
                builder.append(indent + key + ": " + value + "\n");
            }
        }
    }
}
