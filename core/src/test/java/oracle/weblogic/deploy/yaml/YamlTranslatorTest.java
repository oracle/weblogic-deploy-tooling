/*
 * Copyright (c) 2020, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import org.junit.Assert;
import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.logging.Level;
import java.util.logging.Logger;

import static java.nio.charset.StandardCharsets.UTF_8;

public class YamlTranslatorTest {

    /**
     * Verify that a lexical error will throw an Exception
     */
    @Test
    public void testLexicalError() {
        // Temporarily disable logging for this test. Intended lexical failure will log a stack trace.
        Logger logger = Logger.getLogger("wlsdeploy.yaml");
        Level originalLevel  = logger.getLevel();
        logger.setLevel(Level.OFF);

        try {
            // YAML causes lexical error:
            // abc:
            //   xyz: aa-bb
            String text = "abc:\n  xyz: aa-bb\n";
            InputStream stream = new ByteArrayInputStream(text.getBytes(UTF_8));
            YamlStreamTranslator translator = new YamlStreamTranslator("String", stream);
            translator.parse();
            Assert.fail("Test must raise YamlException when model has a lexical error");

        } catch(YamlException e) {
            // expected result

        } finally {
            logger.setLevel(originalLevel);
        }
    }
}
