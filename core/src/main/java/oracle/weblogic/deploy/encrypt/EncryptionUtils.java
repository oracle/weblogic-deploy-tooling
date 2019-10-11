/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.encrypt;

import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.KeySpec;
import java.util.ArrayList;
import java.util.List;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;
import javax.xml.bind.DatatypeConverter;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.StringUtils;

import static java.nio.charset.StandardCharsets.US_ASCII;
import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * This class provides basic encryption/decryption capabilities.
 */
public final class EncryptionUtils {
    private static final String CLASS = EncryptionUtils.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.encrypt");

    private static final String SECRET_KEY_FACTORY_ALGORITHM = "PBKDF2WithHmacSHA256";
    private static final String SECRET_KEY_SPEC_ALGORITHM = "AES";
    private static final String CIPHER_ALGORITHM = "AES/GCM/NoPadding";
    private static final String CIPHER_TEXT_PREFIX = "{AES}";
    private static final String SEP = ":";
    private static final int ITERATIONS = 65536;
    private static final int AES_KEY_SIZE = 128;
    private static final int GCM_NONCE_LENGTH = 12;
    private static final int GCM_TAG_LENGTH = 16;
    private static final int SALT_SIZE = 8;
    private static final int BITS_PER_BYTE = 8;

    private static final int CIPHER_SECTIONS = 3;
    private static final int PWD_POS = 0;
    private static final int NONCE_POS = 1;
    private static final int SALT_POS = 2;

    private static final SecureRandom RANDOM = new SecureRandom();

    private EncryptionUtils() {
        // hide the constructor for this utility class
    }

    /**
     * Determines whether or not a string is already encrypted.
     *
     * @param text the string to check
     * @return whether or not the string is already encrypted,
     *         false is always returned for zero length or null strings
     */
    public static boolean isEncryptedString(String text) {
        return !StringUtils.isEmpty(text) && text.startsWith(CIPHER_TEXT_PREFIX);
    }

    /**
     * Get the unencrypted characters from an encrypted string.
     *
     * @param cipherText the encrypted string
     * @param userPassphrase the passphrase used to encrypt the string
     * @return the unencrypted characters
     * @throws EncryptionException if an error occurs while decrypting the string
     */
    public static char[] decryptString(String cipherText, final char[] userPassphrase) throws EncryptionException {
        final String METHOD = "decryptString";

        if (userPassphrase == null || userPassphrase.length == 0) {
            EncryptionException ee = new EncryptionException("WLSDPLY-04000");
            LOGGER.throwing(CLASS, METHOD, ee);
            throw ee;
        }

        char[] result = null;
        if (!StringUtils.isEmpty(cipherText)) {
            List<byte[]> parts = getCipherComponents(cipherText);
            if (parts.size() == CIPHER_SECTIONS) {
                byte[] cipherFodder = parts.remove(0);
                byte[] nonce = parts.remove(0);
                byte[] salt = parts.remove(0);

                SecretKey key = getKey(userPassphrase, salt);
                Cipher cipher = getCipher();
                try {
                    cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(GCM_TAG_LENGTH * BITS_PER_BYTE, nonce));
                    result = new String(cipher.doFinal(cipherFodder), UTF_8).toCharArray();
                } catch (InvalidAlgorithmParameterException | InvalidKeyException |
                    IllegalBlockSizeException | BadPaddingException ex) {

                    EncryptionException ee = new EncryptionException("WLSDPLY-04001", ex, ex.getLocalizedMessage());
                    LOGGER.throwing(CLASS, METHOD, ee);
                    throw ee;
                }
            }
        }
        return result;
    }

    /**
     * Get the encrypted string for the specified characters.
     *
     * @param clearText the characters to encrypt
     * @param userPassphrase the passphrase to use for encryption/decryption
     * @return the encrypted string
     * @throws EncryptionException if an error occurs while encrypting the characters
     */
    public static String encryptString(String clearText, final char[] userPassphrase) throws EncryptionException {
        final String METHOD = "encryptString";

        if (userPassphrase == null || userPassphrase.length == 0) {
            EncryptionException ee = new EncryptionException("WLSDPLY-04000");
            LOGGER.throwing(CLASS, METHOD, ee);
            throw ee;
        }

        String result = clearText;
        if (!StringUtils.isEmpty(clearText)) {
            final byte[] salt = new byte[SALT_SIZE];
            RANDOM.nextBytes(salt);
            SecretKey key = getKey(userPassphrase, salt);
            Cipher cipher = getCipher();
            try {
                final byte[] nonce = new byte[GCM_NONCE_LENGTH];
                RANDOM.nextBytes(nonce);
                GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH * BITS_PER_BYTE, nonce);
                cipher.init(Cipher.ENCRYPT_MODE, key, spec);
                byte[] encrypted = cipher.doFinal(clearText.getBytes(UTF_8));
                result = getEncryptedString(encrypted, nonce, salt);
            } catch (InvalidKeyException | InvalidAlgorithmParameterException |
                     IllegalBlockSizeException | BadPaddingException ex) {

                EncryptionException ee = new EncryptionException("WLSDPLY-04002", ex, ex.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, ee);
                throw ee;
            }
        }
        return  result;
    }

    private static SecretKey getKey(final char[] userPassphrase, byte[] saltBytes) throws EncryptionException {
        final String METHOD = "getKey";

        SecretKeyFactory factory;
        try {
            factory = SecretKeyFactory.getInstance(SECRET_KEY_FACTORY_ALGORITHM);
        } catch (NoSuchAlgorithmException nsae) {
            EncryptionException ee = new EncryptionException("WLSDPLY-04003", nsae, nsae.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ee);
            throw ee;
        }

        SecretKey result;
        KeySpec spec = new PBEKeySpec(userPassphrase, saltBytes, ITERATIONS, AES_KEY_SIZE);
        try {
            SecretKey tmp = factory.generateSecret(spec);
            result = new SecretKeySpec(tmp.getEncoded(), SECRET_KEY_SPEC_ALGORITHM);
        } catch (InvalidKeySpecException ikse) {
            EncryptionException ee = new EncryptionException("WLSDPLY-04004", ikse, ikse.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ee);
            throw ee;
        }
        return result;
    }

    private static Cipher getCipher() throws EncryptionException {
        final String METHOD = "getCipher";

        Cipher cipher;
        try {
            cipher = Cipher.getInstance(CIPHER_ALGORITHM);
        } catch (NoSuchPaddingException | NoSuchAlgorithmException ex) {
            EncryptionException ee = new EncryptionException("WLSDPLY-04005", ex, ex.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ee);
            throw ee;
        }
        return cipher;
    }

    private static String getEncryptedString(byte[] cipher, byte[] nonce, byte[] salt) {
        String cipherEncoded = DatatypeConverter.printBase64Binary(cipher);
        String nonceEncoded = DatatypeConverter.printBase64Binary(nonce);
        String saltEncoded = DatatypeConverter.printBase64Binary(salt);
        String all = cipherEncoded + SEP + nonceEncoded + SEP + saltEncoded;
        String allEncoded = DatatypeConverter.printBase64Binary(all.getBytes(US_ASCII));
        return CIPHER_TEXT_PREFIX + allEncoded;
    }

    private static List<byte[]> getCipherComponents(String text) throws EncryptionException {
        final String METHOD = "getCipherComponents";

        List<byte[]> result = new ArrayList<>();
        if (text.startsWith(CIPHER_TEXT_PREFIX) && text.length() > CIPHER_TEXT_PREFIX.length()) {
            String all = text.substring(CIPHER_TEXT_PREFIX.length());
            String allDecoded = new String(DatatypeConverter.parseBase64Binary(all), US_ASCII);
            String[] parts = allDecoded.split(SEP);
            if (parts.length != CIPHER_SECTIONS) {
                EncryptionException ee = new EncryptionException("WLSDPLY-04006", parts.length);
                LOGGER.throwing(CLASS, METHOD, ee);
                throw ee;
            }
            result.add(DatatypeConverter.parseBase64Binary(parts[PWD_POS]));
            result.add(DatatypeConverter.parseBase64Binary(parts[NONCE_POS]));
            result.add(DatatypeConverter.parseBase64Binary(parts[SALT_POS]));
        }
        return result;
    }
}
