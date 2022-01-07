/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.encrypt;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class EncryptionUtilsTest {
    private static final char[] PASSPHRASE = "My dog is a rottweiler".toCharArray();
    private static final String PASSWORD1 = "welcome1";
    private static final String ENCRYPTED_PASSWORD1_1 =
        "{AES}VFk3Ukdmc2lqZVp5bk8yVVdGSi9PcURTRzVTcTNrNjc6b1paa3ltQ3FTYUUrL25ZVjpLWnBweDhoSS9WND0=";
    private static final String ENCRYPTED_PASSWORD1_2 =
        "{AES}bG5WbXk3T012eXFISkJnZTYyRjdUTWJSZE5Ha2N3WWQ6eWpRQTV0amtoaWtHcjhzMjo2WmdmRitlVjFNUT0=";
    private static final String CIPHER_TEXT_PREFIX = "{AES}";

    @Test
    public void encryptStringTest() throws Exception {
        String result = EncryptionUtils.encryptString(PASSWORD1, PASSPHRASE);
        assertNotNull(result, "Expected an encrypted password not null");
        assertTrue(result.startsWith(CIPHER_TEXT_PREFIX), "Excepted encrypted password to start with " + CIPHER_TEXT_PREFIX + " marker");

        char[] password = EncryptionUtils.decryptString(result, PASSPHRASE);
        assertNotNull(password, "Excepted non-empty decrypted password");
        assertNotEquals(0, password.length, "expected non-zero length password");
        result = new String(password);
        assertEquals(PASSWORD1, result, "Excepted decrypted password to match");
    }

    @Test
    public void decryptOldStringTest() throws Exception {
        char[] password = EncryptionUtils.decryptString(ENCRYPTED_PASSWORD1_1, PASSPHRASE);
        assertNotNull(password, "Excepted non-empty decrypted password");
        assertNotEquals(0, password.length, "expected non-zero length password");
        String result = new String(password);
        assertEquals(PASSWORD1, result, "Excepted decrypted password to match");

        password = EncryptionUtils.decryptString(ENCRYPTED_PASSWORD1_2, PASSPHRASE);
        assertNotNull(password, "Excepted non-empty decrypted password");
        assertNotEquals(0, password.length, "expected non-zero length password");
        result = new String(password);
        assertEquals(PASSWORD1, result, "Excepted decrypted password to match");
    }
}
