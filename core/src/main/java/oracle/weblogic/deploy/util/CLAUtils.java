/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Arrays;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * The utility class that provides helper methods for command-line argument processing.
 */
public final class CLAUtils {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    private static final String PROMPT_ENDING = ": ";
    private static final int MAX_PASSWORD_LENGTH = 80;

    private CLAUtils() {
        // hide the private constructor since this is a utility class
    }

    /**
     * Prompt the user for input and return what they type.
     *
     * @param messageKey the resource bundle message key to display
     * @param args the arguments to use to fill in the tokens in the message key
     * @return the user input
     * @throws IOException if an error occurs reading the user input
     */
    public static synchronized String getUserInput(String messageKey, Object...args) throws IOException {
        String result;
        promptInTerminalWindow(messageKey, args);
        if (System.console() != null) {
            result = System.console().readLine();
        } else {
            try (BufferedReader stdinReader = new BufferedReader(new InputStreamReader(System.in, UTF_8))){
                result = stdinReader.readLine();
            }
        }
        return result;
    }

    /**
     * Prompt the user for a password and return what they type.  The text that they
     * type will not be visible on the console window.
     *
     * @param messageKey the resource bundle message key to display
     * @param args the arguments to use to fill in the tokens in the message key
     * @return the user input
     * @throws IOException if an error occurs reading the user input
     */
    public static synchronized char[] getPasswordInput(String messageKey, Object... args) throws IOException {
        char[] result;
        promptInTerminalWindow(messageKey, args);
        if (System.console() != null) {
            result = System.console().readPassword();
        } else {
            result = readPasswordFromStdin(System.in);
        }
        return result;
    }

    private static void promptInTerminalWindow(String messageKey, Object... args) {
        System.out.print(ExceptionHelper.getMessage(messageKey, args) + PROMPT_ENDING);
    }

    private static char[] readPasswordFromStdin(InputStream stdinReader) throws IOException {
        char[] result = new char[MAX_PASSWORD_LENGTH];

        boolean eolFound = false;
        int idx;
        for (idx = 0; idx < MAX_PASSWORD_LENGTH; idx++) {
            char charRead = (char)stdinReader.read();
            if (charRead == '\n' || charRead == '\r') {
                eolFound = true;
                break;
            }
            result[idx] = charRead;
        }
        if (!eolFound) {
            LOGGER.warning("WLSDPLY-01000", MAX_PASSWORD_LENGTH);
        } else {
            char[] tmp = new char[idx];
            System.arraycopy(result, 0, tmp, 0, idx);
            Arrays.fill(result, (char)0);
            result = tmp;
        }
        return result;
    }
}
