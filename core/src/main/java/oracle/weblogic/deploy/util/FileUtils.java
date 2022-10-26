/*
 * Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FilenameFilter;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.attribute.PosixFilePermission;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.xml.bind.DatatypeConverter;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * Utility methods related to file handling.
 */
public final class FileUtils {
    private static final String CLASS = FileUtils.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");
    private static final boolean WINDOWS = File.separatorChar == '\\';

    private static final int NUMBER_OF_FILENAME_COMPONENTS = 2;
    private static final int FILE_NAME_POS = 0;
    private static final int FILE_EXT_POS = 1;
    private static final int READ_BUFFER_SIZE = 4096;

    private FileUtils() {
        // hide the constructor for this utility class
    }

    /**
     * Get the specified resource as an InputStream.
     *
     * @param fileName the resource to get
     * @return the InputStream, or null if it was not found
     */
    public static InputStream getResourceAsStream(String fileName) {
        return FileUtils.class.getClassLoader().getResourceAsStream(fileName);
    }

    /**
     * Get the specified file as an InputStream. This method will first
     * resolve the name to an absolute path and then get the InputStream
     *
     * @param fileName of the file to get
     * @return the InputStream, or null if it was not found.
     *
     * @param fileName
     * @return
     * @throws IOException
     */
    public static InputStream getFileAsStream(String fileName) throws IOException {
        File file = validateExistingFile(fileName);
        return new FileInputStream(getCanonicalFile(file));
    }

    /**
     * Convert a file path into one that Jython will handle.
     *
     * @param filename the filename to convert
     * @return the converted filename that is Jython compatible
     */
    public static String fixupFileSeparatorsForJython(String filename) {
        String newFileName = filename;
        if (WINDOWS) {
            newFileName = newFileName.replace('\\', '/');
        }
        return newFileName;
    }

    /**
     * Create a temporary directory.
     *
     * @param parent the parent directory
     * @param dirBaseName the base name for the new directory
     * @return the temporary directory file
     * @throws IOException if an error occurs while create the temporary directory
     */
    public static File createTempDirectory(File parent, String dirBaseName) throws IOException {
        return getCanonicalFile(Files.createTempDirectory(parent.toPath(), dirBaseName).toFile());
    }

    /**
     * Create a temporary directory.
     *
     * @param dirBaseName the base name for the new directory
     * @return the temporary directory file
     * @throws IOException if an error occurs while create the temporary directory
     */
    public static File createTempDirectory(String dirBaseName) throws IOException {
        return getCanonicalFile(Files.createTempDirectory(dirBaseName).toFile());
    }

    /**
     * A exception free version of getCanonicalFile() that falls back to the absolute file if getCanonicalFile fails.
     *
     * @param f the input file
     * @return the canonical file
     */
    public static File getCanonicalFile(File f) {
        File canonicalFile = null;
        if (f != null) {
            try {
                canonicalFile = f.getCanonicalFile();
            } catch (IOException ioe) {
                LOGGER.warning("WLSDPLY-01100", ioe, f.getPath(), ioe.getLocalizedMessage());
                canonicalFile = f.getAbsoluteFile();
            }
        }
        return canonicalFile;
    }

    /**
     * A exception free version of getCanonicalFile() that falls back to the absolute file if getCanonicalFile fails.
     *
     * @param fileName the file name
     * @return the canonical file
     */
    public static File getCanonicalFile(String fileName) {
        File canonicalFile = null;
        if (!StringUtils.isEmpty(fileName)) {
            canonicalFile = getCanonicalFile(new File(fileName));
        }
        return canonicalFile;
    }

    /**
     * A exception free version of getCanonicalPath() that falls back to the absolute file if getCanonicalPath fails.
     *
     * @param f the input file
     * @return the canonical path
     */
    @SuppressWarnings("WeakerAccess")
    public static String getCanonicalPath(File f) {
        String canonicalPath = null;
        if (f != null) {
            File cf = getCanonicalFile(f);
            canonicalPath = cf.getAbsolutePath();
        }
        return canonicalPath;
    }

    /**
     * A exception free version of getCanonicalPath() that falls back to the absolute file if getCanonicalPath fails.
     *
     * @param fileName the file name
     * @return the canonical path
     */
    @SuppressWarnings("unused")
    public static String getCanonicalPath(String fileName) {
        String canonicalPath = null;
        if (!StringUtils.isEmpty(fileName)) {
            canonicalPath = getCanonicalPath(new File(fileName));
        }
        return canonicalPath;
    }

    /**
     * This method validates that the specified file name is an existing file that is not a directory.
     *
     * @param fileName the file name to validate
     * @return the canonical file representing the file name
     * @throws IllegalArgumentException if the file name is not valid or does not exist
     */
    public static File validateExistingFile(String fileName) {
        final String METHOD = "validateExistingFile";

        LOGGER.entering(CLASS, METHOD, fileName);
        File file = FileUtils.validateFileName(fileName);
        file = validateExistingFile(file);
        LOGGER.exiting(CLASS, METHOD, file);
        return file;
    }

    /**
     * This method validates that the specified file name is an existing file that is not a directory.
     *
     * @param f the file to validate
     * @return the canonical file representing the file name
     * @throws IllegalArgumentException if the file name is not valid or does not exist
     */
    public static File validateExistingFile(File f) {
        final String METHOD = "validateExistingFile";

        LOGGER.entering(CLASS, METHOD, f);
        File file = FileUtils.validateFileName(f.getAbsolutePath());
        if (!file.exists()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01101", file.getAbsolutePath());
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD, file);
        return file;
    }


    /**
     * This method validates that the specified directory name is an existing directory.
     *
     * @param directoryName the directory name to validate
     * @return the canonical file representing the directory name
     * @throws IllegalArgumentException if the directory name is empty,
     *     not a directory, or the directory does not exist
     */
    public static File validateExistingDirectory(String directoryName) {
        final String METHOD = "validateExistingDirectory";

        LOGGER.entering(CLASS, METHOD, directoryName);
        File directory = validateDirectoryName(directoryName);
        if (!directory.exists()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01102", directory.getAbsolutePath());
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD, directory);
        return directory;
    }

    /**
     * This method validates that the specified file name is writable.
     *
     * @param fileName the file name to validate
     * @return the canonical file representing the file name
     * @throws IllegalArgumentException if the file name is not valid or is not writable
     */
    public static File validateWritableFile(String fileName) {
        final String METHOD = "validateWritableFile";

        LOGGER.entering(CLASS, METHOD, fileName);
        File file = validateFileName(fileName);
        if (file.exists() && !file.canWrite()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01103", file.getAbsolutePath());
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD, file);
        return file;
    }

    /**
     * This method validates that the specified directory name is writable.
     *
     * @param directoryName the directory name to validate
     * @return the canonical file representing the directory name
     * @throws IllegalArgumentException if the directory name is not valid, doesn't exist, or is not writable
     */
    public static File validateWritableDirectory(String directoryName) {
        final String METHOD = "validateWritableDirectory";

        LOGGER.entering(CLASS, METHOD, directoryName);
        File directory = FileUtils.validateDirectoryName(directoryName);
        if (directory.isDirectory() && directory.exists() && !directory.canWrite()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01103", directory.getAbsolutePath());
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD, directory);
        return directory;
    }

    /**
     * Parses the filename to separate the base name and extension.
     *
     * @param f File object to use
     * @return 2 element array (where the first element is the base name and the second is the extension)
     *          or null if the argument is null
     */
    public static String[] parseFileName(File f) {
        if (f == null) {
            return new String[0];
        }
        return parseFileName(f.getName());
    }

    /**
     * Parses the filename to separate the base name and extension.
     *
     * @param filename the file name to parse
     * @return 2 element array where the first element is the base name and the second is the extension,
     *      or null if the argument was either null or an empty string
     */
    public static String[] parseFileName(String filename) {

        if (StringUtils.isEmpty(filename)) {
            return new String[0];
        }

        String[] nameComponents = new String[NUMBER_OF_FILENAME_COMPONENTS];
        int idx = filename.lastIndexOf('.');
        switch (idx) {
            case -1:
                // no extension
                nameComponents[FILE_NAME_POS] = filename;
                nameComponents[FILE_EXT_POS] = "";
                break;

            case 0:
                // dot file or "."
                if (filename.length() > 1) {
                    nameComponents[FILE_NAME_POS] = "";
                    nameComponents[FILE_EXT_POS] = filename.substring(1);
                } else {
                    nameComponents[FILE_NAME_POS] = ".";
                    nameComponents[FILE_EXT_POS] = "";
                }
                break;

            default:
                if (filename.length() > idx) {
                    // normal case
                    nameComponents[FILE_NAME_POS] = filename.substring(0, idx);
                    nameComponents[FILE_EXT_POS] = filename.substring(idx + 1);
                } else {
                    //pathological case
                    nameComponents[FILE_NAME_POS] = filename.substring(0, idx);
                    nameComponents[FILE_EXT_POS] = "";
                }
                break;
        }
        return nameComponents;
    }

    /**
     * Whether or not the specified file has a YAML file extension.
     *
     * @param file the file
     * @return true, if the file extension matches the known YAML file extensions
     */
    public static boolean isYamlFile(File file) {
        String fileName = file.getName().toLowerCase(Locale.ENGLISH);
        return fileName.endsWith(".yaml") || fileName.endsWith(".yml");
    }

    /**
     * Whether or not the specified file has a JSON file extension.
     *
     * @param file the file
     * @return true, if the file extension matches the known JSON file extensions
     */
    public static boolean isJsonFile(File file) {
        String fileName = file.getName().toLowerCase(Locale.ENGLISH);
        return fileName.endsWith(".json");
    }

    /**
     * Get the model file from the specified, existing directory.
     *
     * @param modelDirectory the existing directory location to search for a model file.
     * @return the model file or null, if it does not exist
     * @throws IllegalArgumentException if the directory is not a valid, existing, and readable directory
     * @throws IllegalStateException if the modelDirectory contains more than one YAML and/or JSON file
     */
    public static File getModelFile(File modelDirectory) {
        final String METHOD = "getModelFile";

        LOGGER.entering(CLASS, METHOD, modelDirectory);
        if (modelDirectory == null) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01104", METHOD, CLASS, "modelDirectory");
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!modelDirectory.exists()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01102", modelDirectory.getAbsolutePath());
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!modelDirectory.isDirectory()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01105", modelDirectory.getAbsolutePath());
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!modelDirectory.canRead()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01106", modelDirectory.getAbsolutePath());
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        File[] dirEntries;
        try {
            dirEntries = modelDirectory.listFiles(new ModelFilenameFilter());
        } catch (SecurityException se) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01107", se,
                modelDirectory.getAbsolutePath(), se.getLocalizedMessage());
            IllegalArgumentException iae = new IllegalArgumentException(message, se);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        File modelFile = getModelFileFromArray(dirEntries, modelDirectory);
        LOGGER.exiting(CLASS, METHOD, modelFile);
        return modelFile;
    }

    /**
     * Find the model filename from the list.
     *
     * @param filenames the list of filenames
     * @param modelDirectoryName the directory name (for logging purposes only)
     * @return the model file name or null, if it was not found
     * @throws IllegalStateException if the modelDirectory contains more than one YAML and/or JSON file
     */
    public static String getModelFileName(List<String> filenames, String modelDirectoryName) {
        return getModelFileNameFromList(filenames, modelDirectoryName);
    }

    /**
     * Validate the file for the provided file name and return a File object handle. The file name
     * must not be a directory
     *
     * @param fileName of the file to validate
     * @return File handle for the file name
     * @throws IllegalArgumentException if the file name is empty or is a directory
     */
    public static File validateFileName(String fileName) {
        final String METHOD = "validateFileName";

        LOGGER.entering(CLASS, METHOD, fileName);
        if (StringUtils.isEmpty(fileName)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01108");
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        File file = FileUtils.getCanonicalFile(new File(fileName));
        if (file.isDirectory()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01109", file.getAbsolutePath());
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD, file);
        return file;
    }

    /**
     * Validate the directory for the provided directory name and return a File object handle.
     * The directory name must not be a directory.
     *
     * @param directoryName of the file to validate
     * @return File handle for the file name
     * @throws IllegalArgumentException if the directory name is empty or is not a directory
     */
    @SuppressWarnings("WeakerAccess")
    public static File validateDirectoryName(String directoryName) {
        final String METHOD = "validateDirectoryName";

        LOGGER.entering(CLASS, METHOD, directoryName);
        if (StringUtils.isEmpty(directoryName)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01110");
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        File directory = FileUtils.getCanonicalFile(new File(directoryName));
        if (!directory.isDirectory()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01105", directory.getAbsolutePath());
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD, directory);
        return directory;
    }

    /**
     * Delete a directory and all of its contents, recursively.
     *
     * @param directory the directory to delete
     */
    public static void deleteDirectory(File directory) {
        LOGGER.entering(directory);
        if (directory != null) {
            LOGGER.finest("WLSDPLY-01111", directory.getAbsolutePath());
            File[] listing = directory.listFiles();
            if (listing != null) {
                LOGGER.finest("WLSDPLY-01112", directory.getAbsolutePath(), listing.length);
                for (File entry : listing) {
                    if (entry.isDirectory()) {
                        LOGGER.finest("WLSDPLY-01113", directory.getAbsolutePath(), entry.getAbsolutePath());
                        deleteDirectory(entry);
                    } else {
                        String dirPath = directory.getAbsolutePath();
                        String fileName = entry.getAbsolutePath();
                        LOGGER.finest("WLSDPLY-01114", dirPath, fileName);
                        if (!entry.delete()) {
                            LOGGER.finer("WLSDPLY-01115", fileName, dirPath);
                        }
                    }
                }
            }
            if (!directory.delete()) {
                LOGGER.finer("WLSDPLY-01116", directory);
            }
        }
        LOGGER.exiting(directory);
    }

    /**
     * Compute the Base64-encoded hash for the specified file.
     *
     * @param fileName the file name
     * @return the Base64-encoded hash
     * @throws IOException if an error occurs reading the file
     * @throws NoSuchAlgorithmException if an error occurs obtaining the hashing algorithm
     * @throws IllegalArgumentException if the file is not a valid, existing file
     */
    public static String computeHash(String fileName) throws IOException, NoSuchAlgorithmException {
        final String METHOD = "computeHash";

        LOGGER.entering(CLASS, METHOD, fileName);
        validateFileName(fileName);

        String result = computeHash(getCanonicalFile(new File(fileName)));
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Compute the Base64-encoded hash for the specified file.
     *
     * @param file the file
     * @return the Base64-encoded hash
     * @throws IOException if an error occurs reading the file
     * @throws NoSuchAlgorithmException if an error occurs obtaining the hashing algorithm
     * @throws IllegalArgumentException if the file is not a valid, existing file
     */
    public static String computeHash(File file) throws IOException, NoSuchAlgorithmException {
        final String METHOD = "computeHash";

        LOGGER.entering(CLASS, METHOD, file);
        validateExistingFile(file);

        byte[] fileBytes = readFileToByteArray(file);
        String result = computeHash(fileBytes);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Compute the Base64-encoded hash for the specified bytes.
     *
     * @param bytes the bytes to use
     * @return the Base64-encoded hash
     * @throws NoSuchAlgorithmException if an error occurs obtaining the hashing algorithm
     */
    public static String computeHash(byte[] bytes) throws NoSuchAlgorithmException {
        MessageDigest messageDigest = MessageDigest.getInstance("SHA-512");
        byte[] hash = messageDigest.digest(bytes);
        return DatatypeConverter.printBase64Binary(hash);
    }

    /**
     * Get the byte array of the file contents.
     *
     * @param file the file
     * @return the bytes of the file contents
     * @throws IOException if an error occurs reading the file
     * @throws IllegalArgumentException if the file is not a valid, existing file
     */
    @SuppressWarnings("WeakerAccess")
    public static byte[] readFileToByteArray(File file) throws IOException {
        validateExistingFile(getCanonicalPath(file));
        byte[] result;
        try (FileInputStream fis = new FileInputStream(file)) {
            result = readInputStreamToByteArray(fis);
        }
        return result;
    }

    /**
     * Get the bytes of the specified input stream contents.
     *
     * @param input the input stream to use
     * @return the bytes of the input stream contents
     * @throws IOException if an error occurs reading the input stream
     */
    public static byte[] readInputStreamToByteArray(InputStream input) throws IOException {
        byte[] readBuffer = new byte[READ_BUFFER_SIZE];
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream(READ_BUFFER_SIZE);

        int bytesRead;
        while (true) {
            bytesRead = input.read(readBuffer);
            if (bytesRead < 0) {
                break;
            }
            outputStream.write(readBuffer, 0, bytesRead);
        }
        return outputStream.toByteArray();
    }

    public static File writeInputStreamToFile(InputStream input, String fileName) throws IOException {
        File tmpdir = getTmpDir();
        File file = new File(tmpdir, fileName);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            byte[] byteArray = FileUtils.readInputStreamToByteArray(input);
            fos.write(byteArray);
        }
        return file;
    }

    public static File getTmpDir() {
        return new File(System.getProperty("java.io.tmpdir"));
    }

    public static void extractZipFileContent(WLSDeployArchive archiveFile, String zipEntry, String extractPath)  {
        final String METHOD = "extractZipFileContent";

        try {
            if (zipEntry != null) {
                File extractDir = new File(extractPath);
                extractDir.mkdirs();
                String walletZip = archiveFile.extractFile(zipEntry,
                    Files.createTempDirectory("tempwallet").toFile());

                if (!Files.exists(Paths.get(extractPath))) {
                    Files.createDirectory(Paths.get(extractPath));
                }

                // verify that each target file is under the extract directory,
                // to protect from the file overwrite security vulnerability (zip slip).
                String canonicalExtractPath = extractDir.getCanonicalPath();

                byte[] buffer = new byte[1024];
                FileInputStream fis = new FileInputStream(walletZip);
                ZipInputStream zis = new ZipInputStream(fis);
                ZipEntry ze = zis.getNextEntry();
                while (ze != null) {
                    String fileName = ze.getName();
                    File newFile = new File(extractPath + File.separator + fileName);
                    String canonicalNewFile = newFile.getCanonicalPath();
                    if(!canonicalNewFile.startsWith(canonicalExtractPath + File.separator)) {
                        throw new WLSDeployArchiveIOException("WLSDPLY-01119", ze.getName());
                    }

                    new File(newFile.getParent()).mkdirs();
                    FileOutputStream fos = new FileOutputStream(newFile);
                    int len = zis.read(buffer);
                    while (len > 0) {
                        fos.write(buffer, 0, len);
                        len = zis.read(buffer);
                    }
                    fos.close();
                    zis.closeEntry();
                    ze = zis.getNextEntry();
                }
                zis.closeEntry();
                zis.close();
                fis.close();
                Files.delete(Paths.get(walletZip));
            }
        } catch (IOException | WLSDeployArchiveIOException ioe) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01118", archiveFile.getArchiveFileName(),
                    ioe.getLocalizedMessage());
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
    }

    /**
     * Return a PrintWriter instance for the provided file name.
     * @param fileName Name of output file
     * @return PrintWriter instance which is automatically closed
     * @throws IllegalArgumentException if the file is not writable
     */
    public static PrintWriter getPrintWriter(String fileName)  {
        final String METHOD = "getPrintWriter";
        validateWritableFile(fileName);
        try {
            return new PrintWriter(new File(fileName));
        } catch (FileNotFoundException ioe) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01103", fileName);
            IllegalArgumentException iae  = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private helper methods                                                //
    ///////////////////////////////////////////////////////////////////////////

    private static File getModelFileFromArray(File[] files, File modelDirectory) {
        File modelFile = null;
        if (files != null && files.length > 0) {
            modelFile = getModelFileFromList(Arrays.asList(files), modelDirectory);
        }
        return modelFile;
    }

    private static String getModelFileNameFromList(List<String> filenames, String modelDirectoryName) {
        String result = null;
        if (filenames != null && !filenames.isEmpty()) {
            List<File> files = new ArrayList<>(filenames.size());
            for (String filename : filenames) {
                files.add(new File(filename));
            }
            File modelFile = getModelFileFromList(files, new File(modelDirectoryName));
            if (modelFile != null) {
                result = modelFile.getPath();
            }
        }
        return result;
    }

    private static File getModelFileFromList(List<File> files, File modelDirectory) {
        final String METHOD = "getModelFileFromList";

        File modelFile = null;
        if (files != null && !files.isEmpty()) {
            File yamlFile = null;
            File jsonFile = null;

            for (File file : files) {
                if (FileUtils.isYamlFile(file)) {
                    if (yamlFile == null) {
                        yamlFile = file;
                    } else {
                        String message = ExceptionHelper.getMessage("WLSDPLY-01117", modelDirectory.getAbsolutePath(),
                            "YAML", file.getName(), yamlFile.getName());
                        IllegalStateException ise = new IllegalStateException(message);
                        LOGGER.throwing(CLASS, METHOD, ise);
                        throw ise;
                    }
                } else if (isJsonFile(file)) {
                    if (jsonFile == null) {
                        jsonFile = file;
                    } else {
                        String message = ExceptionHelper.getMessage("WLSDPLY-01117", modelDirectory.getAbsolutePath(),
                            "JSON", file.getName(), jsonFile.getName());
                        IllegalStateException ise = new IllegalStateException(message);
                        LOGGER.throwing(CLASS, METHOD, ise);
                        throw ise;
                    }
                }
            }
            if (yamlFile != null) {
                modelFile = yamlFile;
            } else if (jsonFile != null) {
                modelFile = jsonFile;
            }
        }
        return modelFile;
    }

    /**
     * FilenameFilter class for model files.
     */
    private static class ModelFilenameFilter implements FilenameFilter {
        /**
         * {@inheritDoc}
         */
        @Override
        public boolean accept(File dir, String name) {
            boolean result = false;
            if (!StringUtils.isEmpty(name)) {
                File f = new File(dir, name);
                if (FileUtils.isYamlFile(f) || FileUtils.isJsonFile(f)) {
                    result = true;
                }
            }
            return result;
        }
    }


    /**
     * Convert an octal number into Posix File Permissions.
     * @param octals 3 octal digits representing posix file permissions rwxrwxrwx
     * @return a set of Posix file permissions
     */
    @SuppressWarnings("OctalInteger")
    static Set<PosixFilePermission> getPermissions(int octals) {
        Set<PosixFilePermission> result = new HashSet<>();
        if ( (0400 & octals) > 0) {
            result.add(PosixFilePermission.OWNER_READ);
        }
        if ( (0200 & octals) > 0) {
            result.add(PosixFilePermission.OWNER_WRITE);
        }
        if ( (0100 & octals) > 0) {
            result.add(PosixFilePermission.OWNER_EXECUTE);
        }
        if ( (0040 & octals) > 0) {
            result.add(PosixFilePermission.GROUP_READ);
        }
        if ( (0020 & octals) > 0) {
            result.add(PosixFilePermission.GROUP_WRITE);
        }
        if ( (0010 & octals) > 0) {
            result.add(PosixFilePermission.GROUP_EXECUTE);
        }
        if ( (0004 & octals) > 0) {
            result.add(PosixFilePermission.OTHERS_READ);
        }
        if ( (0002 & octals) > 0) {
            result.add(PosixFilePermission.OTHERS_WRITE);
        }
        if ( (0001 & octals) > 0) {
            result.add(PosixFilePermission.OTHERS_EXECUTE);
        }
        return result;
    }

    /**
     * Set OS file permissions given an Octal permission set.
     * Needed due to Jython 2.2 did not offer a os.chmod function.
     * @param path file name to be changed
     * @param octals octal number set like OS chmod permissions
     * @throws IOException if permissions update fails
     */
    public static void chmod(String path, int octals) throws IOException {
        if(!WINDOWS) {
            Files.setPosixFilePermissions(Paths.get(path), getPermissions(octals));
        }
    }
}
