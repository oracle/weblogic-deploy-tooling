/*
 * Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertThrows;

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

        // JSON { "abc": "xyz"\ } causes lexical error
        String text = "{ \"abc\": \"xyz\"/ }";
        InputStream stream = new ByteArrayInputStream(text.getBytes(UTF_8));
        final JsonStreamTranslator translator = new JsonStreamTranslator("String", stream);
        assertThrows(JsonException.class, new Executable() {
            @Override
            public void execute() throws Throwable {
                translator.parse();
            }
        }, "Test must raise JsonException when model has a lexical error");

        logger.setLevel(originalLevel);
    }
}
