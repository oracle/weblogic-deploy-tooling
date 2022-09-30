/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * The internal class that does the heavy-lifting with zip files for the WLSDeployArchive class.
 */
public class WLSDeployZipFile {
    private static final String CLASS = WLSDeployZipFile.class.getName();
    private static final int ZIP_FILE_OPEN_MODE = ZipFile.OPEN_READ;
    private static final char DOT = '.';
    private static final char OPEN_PAREN_CHAR = '(';
    private static final String OPEN_PAREN = "(";
    private static final char CLOSE_PAREN_CHAR = ')';
    private static final String CLOSE_PAREN = ")";
    private static final char ZIP_SEP_CHAR = '/';
    private static final String ZIP_SEP = "/";
    private static final int READ_BUFFER_SIZE = 4096;

    private static final int MAX_DIGITS = Integer.toString(Integer.MAX_VALUE).length() - 1;
    private static final String ARCHIVE_RENAME_PATTERN_REGEX = ".+\\([0-9]{1," + MAX_DIGITS + "}\\)/?$";
    private static final Pattern ARCHIVE_RENAME_PATTERN = Pattern.compile(ARCHIVE_RENAME_PATTERN_REGEX);
    private static final int ARCHIVE_RENAME_INITIAL_NUMBER = 1;

    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.archive");

    private File file;
    private ZipFile openZipFile;
    private boolean newFile;

    //////////////////////////////////////////////////////////////////////////////////////////////////
    // Public APIs                                                                                  //
    //////////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Constructor for the WLSDeployZipFile class.
     *
     * @param file File object representing the zip file in the file system
     * @throws IllegalArgumentException if the file is null
     * @throws IllegalStateException    if the zip file does not exist and cannot be created
     */
    public WLSDeployZipFile(File file) {
        final String METHOD = "<init>";

        LOGGER.entering(CLASS, METHOD, file != null ? file.getAbsolutePath() : "null");
        if (file == null) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01104", METHOD, CLASS, "file");
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        this.file = new File(file.getAbsolutePath());
        this.newFile = !file.exists();
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Get the absolute path name of the underlying zip file.
     *
     * @return the absolute path to the file
     */
    public String getFileName() {
        return getFile().getAbsolutePath();
    }



    /**
     * Get an entry from the zip file.  Because this code returns an input stream from the ZipFile,
     * the caller must call close() when they are finished with the input stream.
     *
     * @param key entry name
     * @return an InputStream for the entry content, or null if the entry does not exist
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     */
    public InputStream getZipEntry(String key) throws WLSDeployArchiveIOException {
        final String METHOD = "getZipEntry";

        LOGGER.entering(CLASS, METHOD, key);
        closeOpenZipFile();

        LinkedHashMap<String, ZipEntry> map = getZipFileEntries(getFile());
        InputStream stream = null;
        boolean leaveOpen = false;
        try {
            if (map.containsKey(key)) {
                LOGGER.finer("WLSDPLY-01500", getFileName(), key);
                openZipFile = new ZipFile(getFile(), ZIP_FILE_OPEN_MODE);
                ZipEntry ze = new ZipEntry(key);
                sanitizeZipEntry(ze);
                stream = openZipFile.getInputStream(ze);
                leaveOpen = true;
                LOGGER.finer("WLSDPLY-01501", getFileName(), ze.getName(), stream.toString());
            } else {
                LOGGER.finer("WLSDPLY-01502", getFileName(), key);
            }
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01503", ioe,
                getFileName(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        } finally {
            if (!leaveOpen && openZipFile != null) {
                closeOpenZipFile();
            }
        }
        LOGGER.exiting(CLASS, METHOD, stream);
        return stream;
    }

    /**
     * Get the list of entries in the zip file.
     *
     * @return the list of zip file entries
     * @throws WLSDeployArchiveIOException if an error occurs while reading the zip file
     */
    public List<String> listZipEntries() throws WLSDeployArchiveIOException {
        final String METHOD = "listZipEntries";

        LOGGER.entering(CLASS, METHOD);
        closeOpenZipFile();

        Map<String, ZipEntry> zipEntries = getZipFileEntries(file);
        List<String> result = new ArrayList<>(zipEntries.keySet());
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get the list of entries in the zip file that start with the specified prefix.
     *
     * @param prefix the prefix to use as a filter
     * @return the list of zip file entries that match the prefix
     * @throws WLSDeployArchiveIOException if an error occurs while reading the zip file
     */
    public List<String> listZipEntries(String prefix) throws WLSDeployArchiveIOException {
        final String METHOD = "listZipEntries";

        LOGGER.entering(CLASS, METHOD, prefix);
        closeOpenZipFile();

        Map<String, ZipEntry> zipEntries = getZipFileEntries(file);
        List<String> result = new ArrayList<>();
        for (String name : zipEntries.keySet()) {
            if (name.startsWith(prefix)) {
                result.add(name);
            }
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get the entries in the zip file.  Because this code returns input streams from the ZipFile,
     * the caller must call close() when they are finished with the input streams.
     *
     * @return a map of InputStreams keyed by the entry name
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     */
    public Map<String, InputStream> getZipEntries() throws WLSDeployArchiveIOException {
        final String METHOD = "getZipEntries";

        LOGGER.entering(CLASS, METHOD);
        closeOpenZipFile();

        LinkedHashMap<String, ZipEntry> map = getZipFileEntries(getFile());
        LinkedHashMap<String, InputStream> zipEntries = new LinkedHashMap<>();
        boolean leaveOpen = false;
        try {
            if (!map.isEmpty()) {
                LOGGER.finer("WLSDPLY-01504", getFileName(), map.size());
                openZipFile = new ZipFile(getFile(), ZIP_FILE_OPEN_MODE);
                for (String key : map.keySet()) {
                    addEntryToMap(map, zipEntries, key);
                }
                leaveOpen = true;
            }
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01503", ioe,
                getFileName(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        } finally {
            if (!leaveOpen && openZipFile != null) {
                closeOpenZipFile();
            }
        }
        LOGGER.exiting(CLASS, METHOD, zipEntries);
        return zipEntries;
    }

    /**
     * Get the entries in the zip file whose names start with the specified value.  Because this code
     * returns input streams from the ZipFile, the caller must call close() when they are finished
     * with the input streams.
     *
     * @param key the beginning part of the entry names to match
     * @return a map of InputStreams keyed by the entry name
     * @throws WLSDeployArchiveIOException if an IOException occurred while rading or writing changes
     */
    public Map<String, InputStream> getZipEntries(String key) throws WLSDeployArchiveIOException {
        final String METHOD = "getZipEntries";

        LOGGER.entering(CLASS, METHOD, key);
        closeOpenZipFile();

        LinkedHashMap<String, ZipEntry> map = getZipFileEntries(getFile());
        LinkedHashMap<String, InputStream> zipEntries = new LinkedHashMap<>();
        boolean leaveOpen = false;
        try {
            if (!map.isEmpty()) {
                LOGGER.finer("WLSDPLY-01504", getFileName(), map.size());
                openZipFile = new ZipFile(getFile(), ZIP_FILE_OPEN_MODE);
                Iterator<String> savedKeys = map.keySet().iterator();
                while (savedKeys.hasNext()) {
                    String savedKey = savedKeys.next();
                    if (savedKey.startsWith(key)) {
                        addEntryToMap(map, zipEntries, savedKey);
                    }
                }
                leaveOpen = true;
            }
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01503", ioe,
                getFileName(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        } finally {
            if (!leaveOpen && openZipFile != null) {
                closeOpenZipFile();
            }
        }
        LOGGER.exiting(CLASS, METHOD, zipEntries);
        return zipEntries;
    }

    /**
     * Removes a single entry from the zip file.
     *
     * @param key the name of the entry to remove
     * @return true if the entry was found and removed, false otherwise
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     */
    public boolean removeZipEntry(String key) throws WLSDeployArchiveIOException {
        final String METHOD = "removeZipEntry";

        LOGGER.entering(CLASS, METHOD, key);
        closeOpenZipFile();

        boolean removedEntry = false;
        LinkedHashMap<String, ZipEntry> map = getZipFileEntries(getFile());
        if (map.containsKey(key)) {
            LOGGER.finer("WLSDPLY-01500", getFileName(), key);
            map.remove(key);
            saveChangesToZip(map, null);
            removedEntry = true;
        } else {
            LOGGER.finer("WLSDPLY-01502", getFileName(), key);
        }

        LOGGER.exiting(CLASS, METHOD, removedEntry);
        return removedEntry;
    }

    /**
     * Removes all entries beginning with the provided name.  For example, removeZipEntries("/dir1")
     * will remove the directory "dir1" and all of its contents from the zip.
     *
     * @param key the key prefix to use to delete entries from the zip
     * @return whether ot not any entries were deleted from the zip
     * @throws WLSDeployArchiveIOException if an error occurs reading or writing the zip file
     */
    public boolean removeZipEntries(String key) throws WLSDeployArchiveIOException {
        final String METHOD = "removeZipEntries";

        LOGGER.entering(CLASS, METHOD, key);
        closeOpenZipFile();

        boolean removedEntry = false;
        LinkedHashMap<String, ZipEntry> entriesMap = getZipFileEntries(getFile());
        if (!entriesMap.isEmpty()) {
            ArrayList<String> matchingKeys = getMatchingKeysFromMap(entriesMap, key);
            if (!matchingKeys.isEmpty()) {
                LOGGER.finer("WLSDPLY-01505", getFileName(), key, matchingKeys.size());

                for (String matchingKey : matchingKeys) {
                    entriesMap.remove(matchingKey);
                }
                saveChangesToZip(entriesMap, null);
                removedEntry = true;
            } else {
                LOGGER.finer("WLSDPLY-01506", getFileName(), key);
            }
        }
        LOGGER.exiting(CLASS, METHOD, removedEntry);
        return removedEntry;
    }

    /**
     * Add the provided entry to the unsaved changes list, optionally renaming it to prevent conflicts.
     *
     * @param entryName   the name of the entry to add
     * @param inputStream the InputStream that will be used to read the entry when it is saved
     * @param rename      whether or not to rename the entry if it conflicts with an existing entry
     * @return the entry name used to store the entry or null if the add failed due to an entry name conflict
     * @throws WLSDeployArchiveIOException if an IOException occurred while adding the entry
     */
    public String addZipEntry(String entryName, InputStream inputStream, boolean rename)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addZipEntry";

        LOGGER.entering(CLASS, METHOD, entryName, inputStream, rename);
        closeOpenZipFile();

        String newEntryName = entryName;
        if (rename && isRenameNecessary(newEntryName)) {
            LOGGER.finer("WLSDPLY-01507", entryName);
            newEntryName = getNextUniqueEntryName(entryName);
            LOGGER.finer("WLSDPLY-01508", entryName, newEntryName);
        }

        boolean success = addZipEntry(newEntryName, inputStream);
        if (!success) {
            newEntryName = null;
        }
        LOGGER.exiting(CLASS, METHOD, newEntryName);
        return newEntryName;
    }

    /**
     * Adds the provided entry to the zip if the zip does not have an entry with the same name.
     *
     * @param key         the name of the entry to add
     * @param inputStream the InputStream that will be used to read the entry when it is saved
     * @return true if the entry was added, false if the zip file already has an entry with that name
     * @throws WLSDeployArchiveIOException if an IOException occurred while adding the entry
     */
    public boolean addZipEntry(String key, InputStream inputStream) throws WLSDeployArchiveIOException {
        final String METHOD = "addZipEntry";

        LOGGER.entering(CLASS, METHOD, key, inputStream);
        closeOpenZipFile();

        boolean addedEntry = true;
        LinkedHashMap<String, ZipEntry> zipEntriesMap = getZipFileEntries(getFile());
        if (zipEntriesMap.containsKey(key)) {
            LOGGER.finer("WLSDPLY-01509", getFileName(), key);
            addedEntry = false;
        }
        // still true so ok to proceed
        if (addedEntry) {
            LOGGER.finer("WLSDPLY-01510", getFileName(), key);
            LinkedHashMap<String, InputStream> newEntries = new LinkedHashMap<>();
            newEntries.put(key, inputStream);
            saveChangesToZip(zipEntriesMap, newEntries);
            LOGGER.finer("WLSDPLY-01511", getFileName(), key);
        }
        LOGGER.exiting(CLASS, METHOD, addedEntry);
        return addedEntry;
    }

    /**
     * Add the provided directory entry to the unsaved changes list, optionally renaming it to prevent conflicts.
     *
     * @param entryName the entry name to add
     * @param rename whether or not to rename the entry to prevent conflicts
     * @return the name of the added entry
     * @throws WLSDeployArchiveIOException if an IOException occurred while adding the entry
     */
    public String addZipDirectoryEntry(String entryName, boolean rename) throws WLSDeployArchiveIOException {
        final String METHOD = "addZipDirectoryEntry";

        LOGGER.entering(CLASS, METHOD, entryName, rename);
        closeOpenZipFile();

        String newEntryName = entryName;
        if (!entryName.endsWith("/")) {
            newEntryName = entryName + "/";
        }

        if (rename && isRenameNecessary(newEntryName)) {
            LOGGER.finer("WLSDPLY-01507", entryName);
            newEntryName = getNextUniqueEntryName(entryName);
            LOGGER.finer("WLSDPLY-01508", entryName, newEntryName);
            if (!newEntryName.endsWith("/")) {
                newEntryName += "/";
            }
        }

        boolean success = addZipDirectoryEntry(newEntryName);
        if (!success) {
            newEntryName = null;
        }
        LOGGER.exiting(CLASS, METHOD, newEntryName);
        return newEntryName;
    }

    /**
     * Adds the provided directory entry to the zip if the zip does not have an entry with the same name.
     *
     * @param key the name of the entry to add
     * @return whether or not the entry was added
     * @throws WLSDeployArchiveIOException if an IOException occurred while adding the entry
     */
    public boolean addZipDirectoryEntry(String key) throws WLSDeployArchiveIOException {
        final String METHOD = "addZipDirectoryEntry";

        LOGGER.entering(CLASS, METHOD, key);
        closeOpenZipFile();

        boolean addedEntry = true;
        LinkedHashMap<String, ZipEntry> zipEntriesMap = getZipFileEntries(getFile());
        if (zipEntriesMap.containsKey(key)) {
            LOGGER.finer("WLSDPLY-01509", getFileName(), key);
            addedEntry = false;
        }
        // still true so ok to proceed
        if (addedEntry) {
            LOGGER.finer("WLSDPLY-01510", getFileName(), key);
            LinkedHashMap<String, InputStream> newEntries = new LinkedHashMap<>();
            newEntries.put(key, null);
            saveChangesToZip(zipEntriesMap, newEntries);
            LOGGER.finer("WLSDPLY-01511", getFileName(), key);
        }
        LOGGER.exiting(CLASS, METHOD, addedEntry);
        return addedEntry;
    }

    /**
     * Add the provided directory entry and all of its contents to the zip file, renaming the directory
     * entry name to prevent conflicts.
     *
     * @param entryName the name of the directory entry to add
     * @param directory the directory to add including all of its content, recursively
     * @return the entry name used to store the directory or null if the add failed
     * @throws WLSDeployArchiveIOException if an IOException occurred while adding the entry
     * @throws IllegalArgumentException if the file provided is not a valid directory
     */
    public String addDirectoryZipEntries(String entryName, File directory) throws WLSDeployArchiveIOException {
        final String METHOD = "addDirectoryZipEntries";

        LOGGER.entering(CLASS, METHOD, entryName, directory);
        closeOpenZipFile();

        if (!directory.exists()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01423", directory.getAbsolutePath());
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!directory.isDirectory()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01424", directory.getAbsolutePath());
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        String newEntryName = entryName;
        if (!newEntryName.endsWith(ZIP_SEP)) {
            newEntryName += ZIP_SEP;
        }
        if (isRenameNecessary(newEntryName)) {
            LOGGER.finer("WLSDPLY-01507", entryName);
            newEntryName = getNextUniqueEntryName(newEntryName);
            LOGGER.finer("WLSDPLY-01508", entryName, newEntryName);
        }

        // Now, we need to add the top-level entry and recurse to add entries.  Don't need to worry about renaming
        // any other elements since the unique directory name protects us from collisions.
        //
        String rootEntryName = newEntryName;
        if (!rootEntryName.endsWith(ZIP_SEP)) {
            rootEntryName += ZIP_SEP;
        }
        LinkedHashMap<String, ZipEntry> existingEntries = getZipFileEntries(getFile());
        LinkedHashMap<String, InputStream> newEntries = new LinkedHashMap<>();
        try {
            addDirectoryToUnsavedMap(newEntries, directory, rootEntryName);
            saveChangesToZip(existingEntries, newEntries);
        } finally {
            cleanupUnsavedEntries(newEntries);
        }
        LOGGER.exiting(CLASS, METHOD, newEntryName);
        return newEntryName;
    }

    /**
     * Adds or replaces an existing entry without renaming.
     *
     * @param key the entry to add/replace
     * @param inputStream the InputStream to use to read the contents
     * @throws WLSDeployArchiveIOException if an error occurs while reading or writing the zip file.
     */
    public void putZipEntry(String key, InputStream inputStream) throws WLSDeployArchiveIOException {
        final String METHOD = "putZipEntry";

        LOGGER.entering(CLASS, METHOD, key, inputStream);
        closeOpenZipFile();

        LinkedHashMap<String, ZipEntry> zipEntriesMap = getZipFileEntries(getFile());
        if (zipEntriesMap.containsKey(key)) {
            zipEntriesMap.remove(key);
        }

        LinkedHashMap<String, InputStream> entryToPut = new LinkedHashMap<>();
        entryToPut.put(key, inputStream);
        try {
            LOGGER.finer("WLSDPLY-01510", getFileName(), key);
            saveChangesToZip(zipEntriesMap, entryToPut);
            LOGGER.finer("WLSDPLY-01511", getFileName(), key);
        } finally {
            cleanupUnsavedEntries(entryToPut);
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Closes the open zip file from the last call, if any, which in turn closes all open input streams into the zip.
     */
    public void close() {
        final String METHOD = "close";

        LOGGER.entering(CLASS, METHOD);
        closeOpenZipFile();
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Allows the WLSDeployArchive to determine if the file is new or not.
     *
     * @return true if the file is new, false otherwise
     */
    boolean isNewFile() {
        return this.newFile;
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////
    // Private Getters/Setters                                                                     //
    /////////////////////////////////////////////////////////////////////////////////////////////////
    private File getFile() {
        return this.file;
    }

    private void setNewFile(boolean newFile) {
        this.newFile = newFile;
    }

    private ZipFile getOpenZipFile() {
        return this.openZipFile;
    }

    private void setOpenZipFile(ZipFile openZipFile) {
        this.openZipFile = openZipFile;
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private Helper Methods                                                //
    ///////////////////////////////////////////////////////////////////////////

    private static void sanitizeZipEntry(ZipEntry ze) {
        ze.setCompressedSize(-1);
    }

    private void logZipEntries(Map<String, ?> entries, String sizeKey) {
        if (entries != null && !entries.isEmpty()) {
            LOGGER.finer(sizeKey, getFileName(), entries.size());
            if (LOGGER.isFinestEnabled()) {
                for (String key : entries.keySet()) {
                    LOGGER.finest("WLSDPLY-01512", getFileName(), key);
                }
            }
        }
    }

    private void closeOpenZipFile() {
        final String METHOD = "closeOpenZipFile";

        LOGGER.entering(CLASS, METHOD);
        if (getOpenZipFile() != null) {
            LOGGER.finer("WLSDPLY-01513", getFileName());
            ZipFile zf = getOpenZipFile();
            try {
                zf.close();
            } catch (IOException ioe) {
                LOGGER.warning("WLSDPLY-01514", ioe, getFileName(), ioe.getLocalizedMessage());
                // continue since this is best effort only
            } finally {
                setOpenZipFile(null);
            }
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private boolean zipFileIsNotEmpty() {
        final String METHOD = "zipFileIsNotEmpty";

        LOGGER.entering(CLASS, METHOD);
        boolean value = false;

        if (!isNewFile()) {
            LOGGER.finer("WLSDPLY-01515", getFileName());
            long len = getFile().length();
            if (len > 0) {
                value = true;
            }
        }
        LOGGER.exiting(CLASS, METHOD, value);
        return value;
    }

    private LinkedHashMap<String, ZipEntry> getZipFileEntries(File zipFile) throws WLSDeployArchiveIOException {
        final String METHOD = "getZipEntries";

        LinkedHashMap<String, ZipEntry> savedZipEntries = new LinkedHashMap<>();
        if (zipFileIsNotEmpty()) {
            savedZipEntries = new LinkedHashMap<>();
            try (ZipFile zipper = new ZipFile(zipFile, ZIP_FILE_OPEN_MODE)) {
                Enumeration<?> entries = zipper.entries();
                while (entries.hasMoreElements()) {
                    ZipEntry entry = (ZipEntry) entries.nextElement();
                    String key = entry.getName();
                    savedZipEntries.put(key, entry);
                }
            } catch (IOException ioe) {
                WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01503",
                    ioe, getFileName(), ioe.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, wdaioe);
                throw wdaioe;
            }
        }
        return savedZipEntries;
    }

    private void saveChangesToZip(Map<String, ZipEntry> updatedZipEntries, Map<String, InputStream> newEntries)
        throws WLSDeployArchiveIOException {
        final String METHOD = "saveChangesToZip";

        LOGGER.entering(CLASS, METHOD, updatedZipEntries, newEntries);

        File newOutputFile = getNewOutputFile();
        if ((updatedZipEntries != null && !updatedZipEntries.isEmpty()) ||
            (newEntries != null && !newEntries.isEmpty())) {

            logZipEntries(updatedZipEntries, "WLSDPLY-01504");
            logZipEntries(newEntries, "WLSDPLY-01516");

            // If both saved and unsaved changes exist, remove the keys in unsaved changes
            // from the saved changes list so that the updated value is written below.
            //
            if (updatedZipEntries != null && !updatedZipEntries.isEmpty() &&
                newEntries != null && !newEntries.isEmpty()) {

                for (String unsavedKey : newEntries.keySet()) {
                    // Any key that appears in unsavedChanges takes precedence over the same key
                    // in savedChanges when writing the new zip file.  As such, remove any keys from
                    // the unsavedChanges list that also appear in the savedChanges list.
                    //
                    ZipEntry removedSavedEntry = updatedZipEntries.remove(unsavedKey);
                    if (removedSavedEntry != null) {
                        LOGGER.finest("WLSDPLY-01517", getFileName(), removedSavedEntry.getName());
                    } else {
                        LOGGER.finest("WLSDPLY-01518", getFileName(), unsavedKey);
                    }
                }
            }

            InputStream inputStream = null;
            try (ZipOutputStream zos = new ZipOutputStream(new FileOutputStream(newOutputFile, false))) {
                if (updatedZipEntries != null && !updatedZipEntries.isEmpty()) {
                    openZipFile = new ZipFile(getFile(), ZIP_FILE_OPEN_MODE);

                    ZipEntry ze;
                    for (Map.Entry<String, ZipEntry> updatedEntry : updatedZipEntries.entrySet()) {
                        ze = updatedEntry.getValue();
                        sanitizeZipEntry(ze);
                        String updatedKey = updatedEntry.getKey();
                        if (updatedKey.endsWith("/")) {
                            zos.putNextEntry(ze);
                            zos.closeEntry();
                        } else {
                            inputStream = openZipFile.getInputStream(ze);

                            zos.putNextEntry(ze);
                            readWriteBytes(updatedKey, inputStream, zos);
                            zos.closeEntry();
                            inputStream = closeZipInputStream(inputStream, getFileName(), ze);
                        }
                        LOGGER.finer("WLSDPLY-01519", updatedKey, getFileName(), newOutputFile.getAbsolutePath());
                    }
                    closeOpenZipFile();
                }

                if (newEntries != null && !newEntries.isEmpty()) {
                    for (Map.Entry<String, InputStream> entry : newEntries.entrySet()) {
                        String newKey = entry.getKey();
                        inputStream = entry.getValue();
                        ZipEntry ze = new ZipEntry(newKey);
                        sanitizeZipEntry(ze);

                        if (newKey.endsWith("/")) {
                            zos.putNextEntry(ze);
                            zos.closeEntry();
                        } else {
                            zos.putNextEntry(ze);
                            readWriteBytes(newKey, inputStream, zos);
                            zos.closeEntry();
                            inputStream = closeFileInputStream(inputStream, newKey);
                        }
                        LOGGER.finer("WLSDPLY-01520", newKey, getFileName(), newOutputFile.getAbsolutePath());
                    }
                    LOGGER.fine("WLSDPLY-01521", newOutputFile.getAbsolutePath(), getFileName());
                }
                zos.finish();
            } catch (IOException ioe) {
                WLSDeployArchiveIOException wdaioee = new WLSDeployArchiveIOException("WLSDPLY-01522",
                    ioe, getFileName(), ioe.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, wdaioee);
                throw wdaioee;
            } finally {
                if (inputStream != null) {
                    closeFileInputStream(inputStream, "unknown");
                }
                if (openZipFile != null) {
                    closeOpenZipFile();
                }
            }
        } else {
            // save empty zip file...
            try (ZipOutputStream zos = new ZipOutputStream(new FileOutputStream(newOutputFile, false))) {
                zos.flush();
                zos.finish();
            } catch (IOException ioe) {
                WLSDeployArchiveIOException wdaioee =
                    new WLSDeployArchiveIOException("WLSDPLY-01522", ioe, getFileName(), ioe.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, wdaioee);
                throw wdaioee;
            } finally {
                if (openZipFile != null) {
                    closeOpenZipFile();
                }
            }
        }
        if (isNewFile()) {
            setNewFile(false);
        } else {
            swapFiles(getFile(), newOutputFile);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    private File getNewOutputFile() throws WLSDeployArchiveIOException {
        final String METHOD = "getNewOutputFile";


        File directory = getFile().getParentFile();
        File newOutputFile;
        try {
            if (isNewFile()) {
                newOutputFile = getFile();
                LOGGER.finest("WLSDPLY-01523", newOutputFile.getAbsolutePath());
            } else {
                // Is there a real case the the archive file with no extension ?
                String fileName = getFileName();
                if (fileName.contains(File.separator)) {
                    int lastSeparator = fileName.lastIndexOf(File.separator);
                    if (lastSeparator > 0)
                        fileName = fileName.substring(lastSeparator+1);
                }
                String[] nameComponents = FileUtils.parseFileName(fileName);

                // prefix shouldn't matter what we put here, but it has to be at least 3 characters

                newOutputFile = File.createTempFile("wdt_temparchive", DOT + nameComponents[1], directory);
                LOGGER.finest("WLSDPLY-01524", newOutputFile.getAbsolutePath());
            }
            LOGGER.finer("WLSDPLY-01525", getFileName(), newOutputFile.getAbsolutePath());
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01526", ioe,
                getFileName(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        }
        LOGGER.exiting(CLASS, METHOD, newOutputFile);
        return newOutputFile;
    }

    private static void readWriteBytes(String inputKeyName, InputStream readStream, ZipOutputStream writeStream)
        throws IOException, WLSDeployArchiveIOException {

        int bytesRead;
        byte[] readBuffer = new byte[READ_BUFFER_SIZE];

        while (true) {
            // Catch read exceptions and add more detail about the error...
            //
            try {
                bytesRead = readStream.read(readBuffer);
                if (bytesRead < 0) {
                    break;
                }
            } catch (IOException ioe) {
                WLSDeployArchiveIOException wdaioe =  new WLSDeployArchiveIOException(
                    "WLSDPLY-01527", ioe, inputKeyName, ioe.getLocalizedMessage());
                LOGGER.throwing(wdaioe);
                throw wdaioe;
            }
            writeStream.write(readBuffer, 0, bytesRead);
        }
    }

    private static void swapFiles(File originalFile, File newFile) throws WLSDeployArchiveIOException {
        final String METHOD = "swapFiles";

        LOGGER.entering(CLASS, METHOD, originalFile.getAbsolutePath(), newFile.getAbsolutePath());
        String originalFileName = originalFile.getAbsolutePath();
        String newFileName = newFile.getAbsolutePath();

        Path originalPath = originalFile.toPath();
        Path newPath = newFile.toPath();

        try {
            Files.deleteIfExists(originalPath);
            LOGGER.finer("WLSDPLY-01528", newFileName, originalFileName);
            Files.move(newPath, originalPath);
            LOGGER.finer("WLSDPLY-01529", newFileName, originalFileName);
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01530", ioe,
                newFileName, originalFileName, ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static ArrayList<String> getMatchingKeysFromMap(Map<String, ?> map, String keyToMatch) {
        final String METHOD = "getMatchingKeysFromMap";

        LOGGER.entering(CLASS, METHOD, map, keyToMatch);
        ArrayList<String> matchingKeys = new ArrayList<>();
        Iterator<String> keys = map.keySet().iterator();
        while (keys.hasNext()) {
            String key = keys.next();
            LOGGER.finest("WLSDPLY-01531", key);
            if (key.startsWith(keyToMatch)) {
                LOGGER.finest("WLSDPLY-01532", key, keyToMatch);
                matchingKeys.add(key);
            } else {
                LOGGER.finest("WLSDPLY-01533", key, keyToMatch);
            }
        }
        return matchingKeys;
    }

    private boolean isRenameNecessary(String entryName) throws WLSDeployArchiveIOException {
        LOGGER.entering(entryName);

        boolean renameNeeded = false;
        Map<String, ZipEntry> zipEntryMap = getZipFileEntries(getFile());
        if (zipEntryMap.containsKey(entryName)) {
            LOGGER.finest("WLSDPLY-01534", entryName);
            renameNeeded = true;
        }
        LOGGER.exiting(renameNeeded);
        return renameNeeded;
    }


    private String getNextUniqueEntryName(String entryName) throws WLSDeployArchiveIOException {
        final String METHOD = "getNextUniqueEntryName";

        LOGGER.entering(CLASS, METHOD, entryName);
        // First, strip off the file extension and look for matching entries
        //
        String[] entryNameComps = FileUtils.parseFileName(entryName);

        String entryNameBase = entryNameComps[0];
        String entryNameExtension = entryNameComps[1];
        if (StringUtils.isEmpty(entryNameBase)) {
            // .file case
            entryNameBase = entryNameExtension;
            entryNameExtension = null;
        }
        LOGGER.finer("WLSDPLY-01535", entryName, entryNameBase, entryNameExtension);
        ArrayList<String> matchingSavedEntries = new ArrayList<>();
        Map<String, ZipEntry> zipEntriesMap = getZipFileEntries(getFile());

        for (String zipEntryKey : zipEntriesMap.keySet()) {
            if (zipEntryKey.startsWith(entryNameBase) && entryReallyMatches(zipEntryKey, entryNameBase,
                entryNameExtension)) {
                LOGGER.finer("WLSDPLY-01536", entryName, zipEntryKey);
                matchingSavedEntries.add(zipEntryKey);
            }
        }

        // Now, find the highest unique key in each list
        //
        int newUniqueKey = getNewUniqueKey(entryNameBase, matchingSavedEntries);
        String newEntryName = entryNameBase + OPEN_PAREN + newUniqueKey + CLOSE_PAREN;
        if (!StringUtils.isEmpty(entryNameExtension)) {
            newEntryName += DOT + entryNameExtension;
        }
        LOGGER.exiting(CLASS, METHOD, newEntryName);
        return newEntryName;
    }

    // Matching entries should only be either:
    //     - path/to/entry.<fileExtension>
    //     - path/to/entry-####.<fileExtension>
    //
    // We must take case to not match other entries like:
    //     - path/to/entryxyz.<fileExtension>
    //     - path/to/entry/myentry.<fileExtension>
    //
    boolean entryReallyMatches(String entry, String basename, String extension) {
        boolean reallyMatches = true;

        // check that the extensions match
        String[] entryParts = FileUtils.parseFileName(entry);
        if (!StringUtils.isEmpty(extension)) {
            if (StringUtils.isEmpty(entryParts[1]) || !entryParts[1].equals(extension)) {
                reallyMatches = false;
            }
        } else if (!StringUtils.isEmpty(entryParts[1])) {
            reallyMatches = false;
        }

        if (reallyMatches) {
            String strippedEntry = stripPath(entryParts[0], false);
            String strippedBasename = stripPath(basename, false);
            if (!strippedEntry.startsWith(strippedBasename)) {
                reallyMatches = false;
            } else if (!strippedEntry.equals(strippedBasename) &&
                !ARCHIVE_RENAME_PATTERN.matcher(strippedEntry).matches()) {
                reallyMatches = false;
            }
        }
        return reallyMatches;
    }

    private int getNewUniqueKey(String entryPatternWithoutExtension, ArrayList<String> matchingSavedEntries) {
        final String METHOD = "getNewUniqueKey";

        LOGGER.entering(CLASS, METHOD, entryPatternWithoutExtension, matchingSavedEntries);
        int newKey = -1;

        for (String entry : matchingSavedEntries) {
            String strippedEntry = stripPath(entry, true);
            LOGGER.finest("WLSDPLY-01537", entry, strippedEntry);
            if (ARCHIVE_RENAME_PATTERN.matcher(strippedEntry).matches()) {
                int key = getKey(strippedEntry);
                LOGGER.finest("WLSDPLY-01538", strippedEntry, key);
                if (key > newKey) {
                    newKey = key;
                }
            }
        }
        if (newKey == -1) {
            // found no renamed files, only the original
            newKey = ARCHIVE_RENAME_INITIAL_NUMBER;
        } else {
            newKey++;
        }
        LOGGER.exiting(CLASS, METHOD, newKey);
        return newKey;
    }

    // package protection for unit tests...
    //
    String stripPath(String itemToStrip, boolean stripExtension) {
        String item = itemToStrip;

        // Strip off any trailing slash
        if (item.endsWith(ZIP_SEP)) {
            item = item.substring(0, item.length() - 1);
        }
        // Now, find the last slash and take what's left as the item
        int lastPathSeparatorIdx = item.lastIndexOf(ZIP_SEP_CHAR);
        item = item.substring(lastPathSeparatorIdx + 1);

        if (stripExtension) {
            int dotIdx = item.lastIndexOf(DOT);
            // dotIdx == 0 is the pathological case for a .file with no extension
            if (dotIdx > 1) {
                item = item.substring(0, dotIdx);
            }
        }
        return item;
    }

    // package protection for unit tests...
    //
    int getKey(String strippedEntry) {
        int openParenIdx = strippedEntry.lastIndexOf(OPEN_PAREN_CHAR);
        String numberStr = strippedEntry.substring(openParenIdx + 1, strippedEntry.lastIndexOf(CLOSE_PAREN_CHAR));
        return Integer.parseInt(numberStr);
    }

    private void addDirectoryToUnsavedMap(Map<String, InputStream> unsavedChanges,
        File directory, String directoryEntryName) throws WLSDeployArchiveIOException {
        final String METHOD = "addDirectoryToUnsavedMap";

        LOGGER.entering(CLASS, METHOD, directory.getAbsolutePath(), directoryEntryName);
        File[] dirEntries = directory.listFiles();
        if (dirEntries != null) {
            for (File dirEntry : dirEntries) {
                String newEntryName = directoryEntryName + dirEntry.getName();
                if (dirEntry.isDirectory()) {
                    newEntryName += ZIP_SEP;
                    addDirectoryToUnsavedMap(unsavedChanges, dirEntry, newEntryName);
                } else {
                    FileInputStream inputStream;
                    try {
                        inputStream = new FileInputStream(dirEntry);
                    } catch (IOException ioe) {
                        WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException(
                            "WLSDPLY-01425", ioe, getFileName(), dirEntry.getAbsolutePath(), newEntryName,
                            ioe.getLocalizedMessage());
                        LOGGER.throwing(CLASS, METHOD, wdaioe);
                        throw wdaioe;
                    }
                    unsavedChanges.put(newEntryName, inputStream);
                }
            }
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static void cleanupUnsavedEntries(Map<String, InputStream> unsavedEntries) {
        if (unsavedEntries != null && !unsavedEntries.isEmpty()) {
            for (Map.Entry<String, InputStream> entry : unsavedEntries.entrySet()) {
                InputStream is = entry.getValue();
                if (is != null) {
                    // Don't print a warning for these since some or all might already have been closed...
                    //
                    try {
                        is.close();
                    } catch (IOException ignore) {
                        LOGGER.finest("WLSDPLY-01539", ignore, entry.getKey(), ignore.getLocalizedMessage());
                    }
                }
            }
        }
    }

    private void addEntryToMap(LinkedHashMap<String, ZipEntry> zipMap, LinkedHashMap<String, InputStream> map,
        String key) throws IOException {

        LOGGER.finer("WLSDPLY-01500", getFileName(), key);
        ZipEntry entry = zipMap.get(key);
        sanitizeZipEntry(entry);
        InputStream stream = openZipFile.getInputStream(entry);
        LOGGER.finer("WLSDPLY-01501", getFileName(), key, stream);
        map.put(key, stream);
    }

    private static InputStream closeZipInputStream(InputStream inputStream, String fileName, ZipEntry ze) {
        try {
            inputStream.close();
        } catch (IOException ioe) {
            LOGGER.warning("WLSDPLY-01540", ioe, fileName, ze.getName(), ioe.getLocalizedMessage());
            // continue, best effort only...
        }
        return null;
    }

    private static InputStream closeFileInputStream(InputStream inputStream, String fileName) {
        try {
            inputStream.close();
        } catch (IOException ioe) {
            LOGGER.warning("WLSDPLY-01541", ioe, fileName, ioe.getLocalizedMessage());
            // continue...best effort only
        }
        return null;
    }
}
