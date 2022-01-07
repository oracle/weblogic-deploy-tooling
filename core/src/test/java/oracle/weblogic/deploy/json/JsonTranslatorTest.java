/*
 * Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import org.junit.Assert;
import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.logging.Level;
import java.util.logging.Logger;

import static java.nio.charset.StandardCharsets.UTF_8;

public class JsonTranslatorTest {

    /**
     * Verify that a lexical error will throw an Exception
     */
    @Test
    public void testLexicalError() {
        // Temporarily disable logging for this test. Intended lexical failure will log a stack trace.
        Logger logger = Logger.getLogger("wlsdeploy.json");
        Level originalLevel  = logger.getLevel();
        logger.setLevel(Level.OFF);

        try {
            // JSON { "abc": "xyz"\ } causes lexical error
            String text = "{ \"abc\": \"xyz\"/ }";
            InputStream stream = new ByteArrayInputStream(text.getBytes(UTF_8));
            JsonStreamTranslator translator = new JsonStreamTranslator("String", stream);
            translator.parse();
            Assert.fail("Test must raise JsonException when model has a lexical error");

        } catch(JsonException e) {
            // expected result

        } finally {
            logger.setLevel(originalLevel);
        }
    }
}
