/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.encrypt;

import oracle.weblogic.deploy.encrypt.EncryptionUtils;
import org.junit.Assert;
import org.junit.Test;

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
        Assert.assertNotNull("Expected an encrypted password not null", result);
        Assert.assertTrue("Excepted encrypted password to start with " + CIPHER_TEXT_PREFIX + " marker",
            result.startsWith(CIPHER_TEXT_PREFIX));

        char[] password = EncryptionUtils.decryptString(result, PASSPHRASE);
        Assert.assertNotNull("Excepted non-empty decrypted password", password);
        Assert.assertNotEquals("expected non-zero length password", 0, password.length);
        result = new String(password);
        Assert.assertEquals("Excepted decrypted password to match", PASSWORD1, result);
    }

    @Test
    public void decryptOldStringTest() throws Exception {
        char[] password = EncryptionUtils.decryptString(ENCRYPTED_PASSWORD1_1, PASSPHRASE);
        Assert.assertNotNull("Excepted non-empty decrypted password", password);
        Assert.assertNotEquals("expected non-zero length password", 0, password.length);
        String result = new String(password);
        Assert.assertEquals("Excepted decrypted password to match", PASSWORD1, result);

        password = EncryptionUtils.decryptString(ENCRYPTED_PASSWORD1_2, PASSPHRASE);
        Assert.assertNotNull("Excepted non-empty decrypted password", password);
        Assert.assertNotEquals("expected non-zero length password", 0, password.length);
        result = new String(password);
        Assert.assertEquals("Excepted decrypted password to match", PASSWORD1, result);
    }
}
