/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.NoSuchAlgorithmException;
import java.util.List;
import java.util.Map;
import java.util.jar.JarFile;
import java.util.jar.Manifest;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * The purpose of this class is to hide the organizational details of the WLS Deploy archive.  This class is
 * not thread-safe so any concurrent access must be synchronized by the calling application.
 */
public class WLSDeployArchive {
    private static final String CLASS = WLSDeployArchive.class.getName();

    public static final String WLSDPLY_ARCHIVE_BINARY_DIR = "wlsdeploy";

    /**
     * Top-level archive subdirectory where the config
     * will be extracted.
     */
    public static final String ARCHIVE_CONFIG_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/config";

    /**
     * Top-level archive subdirectory where the atp wallet is stored
     */
    public static final String ARCHIVE_ATP_WALLET_PATH = "atpwallet";

    /**
     * Top-level archive subdirectory where the opss wallet is stored
     */
    public static final String ARCHIVE_OPSS_WALLET_PATH = "opsswallet";
    /**
     * Top-level archive subdirectory where the model is stored and the subdirectory to which it will be extracted.
     */
    public static final String ARCHIVE_MODEL_TARGET_DIR = "model";

    /**
     * Top-level archive subdirectory where the applications are stored and the subdirectory to which
     * they will be extracted.
     */
    public static final String ARCHIVE_APPS_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/applications";

    /**
     * Top-level archive subdirectory where the applications are stored and the subdirectory to which
     * they will be extracted. This is for structured applications found under /app
     */
    public static final String ARCHIVE_STRUCT_APPS_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/structuredApplications";

    /**
     * Top-level archive subdirectory where the shared libraries are stored and the subdirectory to
     * which they will be extracted.
     */
    public static final String ARCHIVE_SHLIBS_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/sharedLibraries";

    /**
     * Top-level archive subdirectory where the $DOMAIN_HOME/lib are stored.
     */
    public static final String ARCHIVE_DOMLIB_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/domainLibraries";

    /**
     * Top-level archive subdirectory where the classpath JARs/directories are stored and the
     * subdirectory to which they will be extracted.
     */
    public static final String ARCHIVE_CPLIB_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/classpathLibraries";

    /**
     * Top-level archive subdirectory where the classpath JARs/directories are stored and the
     * subdirectory to which they will be extracted.
     */
    public static final String ARCHIVE_CUSTOM_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/custom";
    /**
     * Top-level archive subdirectory where the $DOMAIN_HOME/bin scripts are stored.
     */
    public static final String ARCHIVE_DOM_BIN_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/domainBin";
    /**
     * Top-level archive subdirectory where the FileStore directories are stored and the subdirectory
     * to which they will be extracted.
     */
    public static final String ARCHIVE_FILE_STORE_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/stores";

    /**
     * Top-level archive subdirectory where the server files are stored and the
     * subdirectory to which they will be extracted.
     */
    public static final String ARCHIVE_SERVER_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/servers";

    /**
     * Top-level archive subdirectory where the Coherence persistence directories are stored and the
     * subdirectory to which they will be extracted.
     */
    public static final String ARCHIVE_COHERENCE_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/coherence";

    /**
     * The subdirectory where node manager files are stored and extracted (such as keystore file).
     */
    public static final String ARCHIVE_NODE_MANAGER_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/nodeManager";

    /**
     * The subdirectory to which the scripts are extracted.
     */
    public static final String ARCHIVE_SCRIPTS_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/scripts";

    /**
     * Top-level archive subdirectory for JMS and in which its sub-directories will be separated.
     */
    public static final String ARCHIVE_JMS_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/jms";

    /**
     * Top-level archive subdirectory where the JMS Foreign Server bindings files are stored and the
     * subdirectory to which they will be extracted.
     */
    public static final String ARCHIVE_JMS_FOREIGN_SERVER_DIR = ARCHIVE_JMS_DIR + "/foreignServer";

    public enum ArchiveEntryType { SHARED_LIBRARIES, APPLICATIONS,
        APPLICATION_PLAN,
        SHLIB_PLAN,
        DOMAIN_LIB,
        DOMAIN_BIN,
        CLASSPATH_LIB,
        SCRIPTS,
        SERVER_KEYSTORE,
        MIME_MAPPING,
        COHERENCE,
        JMS_FOREIGN_SERVER,
        COHERENCE_CONFIG,
        COHERENCE_PERSISTENCE_DIR,
        FILE_STORE,
        NODE_MANAGER_KEY_STORE
    }

    // Used by the unit tests so it requires package level scoping...
    //
    /* package */
    static final String ZIP_SEP = "/";

    private static final String SEP = File.separator;
    private static final int READ_BUFFER_SIZE = 4096;
    private static final String COHERENCE_CONFIG_FILE_EXTENSION = ".xml";
    private static final int HTTP_OK = 200;
    private static final int HTTP_CREATED = 201;

    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.archive");

    private WLSDeployZipFile zipFile;

    /**
     * Constructor for a JCSLifecycleArchive, which hides the details of the bundle generated by export domain.
     *
     * @param archiveFileName the name of the archive file
     * @throws IllegalArgumentException if the archiveFileName is null or an empty string
     * @throws IllegalStateException    if the archive file does not exist and cannot be created
     */
    public WLSDeployArchive(String archiveFileName) {
        final String METHOD = "<init>";

        LOGGER.entering(CLASS, METHOD, archiveFileName);
        validateNonEmptyString(archiveFileName, "archiveFileName", METHOD);

        File f = new File(archiveFileName);
        this.zipFile = new WLSDeployZipFile(f);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Constructor to create an archive file instance for no generation of an archive file.
     */
    private WLSDeployArchive() {
        final String METHOD = "<init>";
        LOGGER.entering(CLASS, METHOD);
        LOGGER.exiting(CLASS, METHOD);
    }

    public static WLSDeployArchive noArchiveFile() {return new WLSDeployArchive();}

    /**
     * Determine whether or not the specified path string is a valid archive location.
     *
     * @param path the path
     * @return true if the path is relative and starts with the expected directory name, false otherwise
     */
    public static boolean isPathIntoArchive(String path) {
        final String METHOD = "isPathIntoArchive";

        LOGGER.entering(CLASS, METHOD, path);
        boolean result = false;
        if (!StringUtils.isEmpty(path)) {
            result = path.startsWith(WLSDPLY_ARCHIVE_BINARY_DIR + ZIP_SEP) || path
                .startsWith(ARCHIVE_ATP_WALLET_PATH + ZIP_SEP) || path.startsWith(ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Determine if the specified path is in the classpath libraries folder.
     * This includes the case where the specified path is the classpath libraries folder.
     *
     * @param path the path to be checked
     * @return true if the specified path matches or is under the classpath libraries folder
     */
    public static boolean isClasspathEntry(String path) {
        return path.startsWith(ARCHIVE_CPLIB_TARGET_DIR);
    }

    /**
     * Get the current file name for the JCSLifecycleArchive file.
     *
     * @return the file name
     */
    public String getArchiveFileName() {
        return getZipFile().getFileName();
    }

    /**
     * Adds the model file into the archive.
     *
     * @param model the model file to add
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the model is null, does not exist, or is not a file
     */
    public void addModel(File model) throws WLSDeployArchiveIOException {
        final String METHOD = "addModel";

        LOGGER.entering(CLASS, METHOD, model);
        validateExistingFile(model, "model", getArchiveFileName(), METHOD);
        getZipFile().removeZipEntries(ARCHIVE_MODEL_TARGET_DIR);
        addItemToZip(ARCHIVE_MODEL_TARGET_DIR, model);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Adds the model file into the archive using the specified model file name.
     *
     * @param model         the file containing the model
     * @param modelFileName the file name to use
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the model is null, does not exist, or is not a file
     */
    public void addModel(File model, String modelFileName) throws WLSDeployArchiveIOException {
        final String METHOD = "addModel";

        LOGGER.entering(CLASS, METHOD, model, modelFileName);
        validateExistingFile(model, "model", getArchiveFileName(), METHOD);
        getZipFile().removeZipEntries(ARCHIVE_MODEL_TARGET_DIR);
        addItemToZip(ARCHIVE_MODEL_TARGET_DIR, model, modelFileName);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Extracts the model, if any, from the existing archive.
     *
     * @param modelDirectory the directory where to place the extracted model
     * @return the model file or null, if no model exists
     * @throws WLSDeployArchiveIOException if an error occurs
     * @throws IllegalArgumentException    if the modelDirectory is null, does not exist, or is not a directory
     */
    public File extractModel(File modelDirectory) throws WLSDeployArchiveIOException {
        final String METHOD = "extractModel";

        LOGGER.entering(CLASS, METHOD, modelDirectory);
        validateExistingDirectory(modelDirectory, "modelDirectory", getArchiveFileName(), METHOD);

        extractDirectoryFromZip(ARCHIVE_MODEL_TARGET_DIR, modelDirectory);

        File modelFile = null;
        File resultDirectory = new File(modelDirectory, ARCHIVE_MODEL_TARGET_DIR);
        if (resultDirectory.exists()) {
            try {
                modelFile = FileUtils.getModelFile(resultDirectory);
            } catch (IllegalArgumentException | IllegalStateException ex) {
                WLSDeployArchiveIOException wsdioe =
                    new WLSDeployArchiveIOException("WLSDPLY-01400", ex, resultDirectory.getAbsolutePath(),
                        ex.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, wsdioe);
                throw wsdioe;
            }
        }
        LOGGER.exiting(CLASS, METHOD, modelFile);
        return modelFile;
    }

    /**
     * Determines whether or not the archive contains a model file.
     *
     * @return true if the archive contains a model file, false otherwise
     * @throws WLSDeployArchiveIOException if an error occurs while reading the archive
     */
    public boolean containsModel() throws WLSDeployArchiveIOException {
        final String METHOD = "containsModel";

        LOGGER.entering(CLASS, METHOD);
        List<String> modelDirContents = getZipFile().listZipEntries(ARCHIVE_MODEL_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list, if it exists...
        modelDirContents.remove(ARCHIVE_MODEL_TARGET_DIR + ZIP_SEP);

        boolean result;
        if (modelDirContents.isEmpty()) {
            result = false;
        } else {
            try {
                String modelEntryName = FileUtils.getModelFileName(modelDirContents, getZipFile().getFileName());
                result = !StringUtils.isEmpty(modelEntryName);
            } catch (IllegalArgumentException iae) {
                WLSDeployArchiveIOException wsdioe =
                    new WLSDeployArchiveIOException("WLSDPLY-01401", iae, iae.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, wsdioe);
                throw wsdioe;
            }
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get the list of entries in the archive file.
     *
     * @return the list of entry path names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive file
     */
    public List<String> getArchiveEntries() throws WLSDeployArchiveIOException {
        final String METHOD = "getArchiveEntries";

        LOGGER.entering(CLASS, METHOD);
        List<String> entries = getZipFile().listZipEntries();
        LOGGER.exiting(CLASS, METHOD, entries);
        return entries;
    }

    /**
     * Determines whether or not the archive contains the specified file or directory.
     *
     * @param path the path into the archive file to test
     * @return true if the specified location was found int the archive, false otherwise
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive file
     * @throws IllegalArgumentException    if the path is null or empty
     */
    public boolean containsFile(String path) throws WLSDeployArchiveIOException {
        final String METHOD = "containsFile";

        LOGGER.entering(CLASS, METHOD, path);
        validateNonEmptyString(path, "path", METHOD);

        boolean result = false;
        // Verify that the path is into the binary root directory so that we do not allow random content.
        if (isPathIntoArchive(path)) {
            List<String> entries = getZipFile().listZipEntries();
            result = entries.contains(path);
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Determines whether or not the provided path is a directory in the archive file.
     *
     * @param path the path into the archive file to test
     * @return true if the specified location was found in the archive file and is a directory
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive file
     * @throws IllegalArgumentException    if the path is null or empty
     */
    public boolean containsPath(String path) throws WLSDeployArchiveIOException {
        final String METHOD = "isAPath";

        LOGGER.entering(CLASS, METHOD, path);
        validateNonEmptyString(path, "path", METHOD);

        boolean result = false;
        // Verify that the path is into the binary root directory so that we do not allow random content.
        if (isPathIntoArchive(path)) {
            List<String> entries = getZipFile().listZipEntries();
            result = !entries.contains(path) && zipListContainsPath(entries, path);
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Determines whether or not the provided path is a directory or a file in a directory
     * in the archive file.
     *
     * @param path the path into the archive file to test
     * @return true if the specified location was found in the archive file
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive file
     * @throws IllegalArgumentException    if the path is null or empty
     */
    public boolean containsFileOrPath(String path) throws WLSDeployArchiveIOException {
        final String METHOD = "containsFileOrPath";

        LOGGER.entering(CLASS, METHOD, path);
        validateNonEmptyString(path, "path", METHOD);

        boolean result = false;
        // Verify that the path is into the binary root directory so that we do not allow random content.
        if (isPathIntoArchive(path)) {
            List<String> entries = getZipFile().listZipEntries();
            result = entries.contains(path) || zipListContainsPath(entries, path);
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Extract the specified file to the specified location (which is typically the domain home).  For example,
     * if the path is wlsdeploy/applications/myapp.ear and the extractToLocation is the domain home, the file
     * will be written to $DOMAIN_HOME/wlsdeploy/applications/myapp.ear.
     *
     * @param path              the path into the archive file to extract
     * @param extractToLocation the base directory to which to write the extracted file or directory.
     * @return the canonical extracted file name
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive or writing the file
     * @throws IllegalArgumentException    if the path is null or empty or the extractToLocation
     *                                     was not a valid, existing directory
     */
    public String extractFile(String path, File extractToLocation) throws WLSDeployArchiveIOException {
        return extractFile(path, extractToLocation, false);
    }

    /**
     * Extract the specified directory to the specified location (which is typically the domain home).  For example,
     * if the path is wlsdeploy/applications/myapp and the extractToLocation is the domain home, the directory
     * will be written to $DOMAIN_HOME/wlsdeploy/applications/myapp .
     *
     * @param path              the path into the archive file to extract
     * @param extractToLocation the base directory to which to write the extracted directory.
     * @return the canonical extracted directory name
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive or writing the directory
     * @throws IllegalArgumentException    if the path is null or empty or the extractToLocation
     *                                     was not a valid, existing directory
     */
    public String extractDirectory(String path, File extractToLocation) throws WLSDeployArchiveIOException {
        String result = FileUtils.getCanonicalFile(new File(extractToLocation, path)).getAbsolutePath();
        this.extractDirectoryFromZip(path, extractToLocation);
        return result;
    }

    /**
     * Extract the specified file to the specified location.
     *
     * @param path                        the path into the archive file to extract
     * @param extractToLocation           the base directory to which to write the extracted file or directory
     * @param stripLeadingPathDirectories whether or not to strip the leading directories
     *                                    when writing to the target location
     * @return the canonical extracted file name
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive or writing the file
     * @throws IllegalArgumentException    if the path is null or empty or the extractToLocation
     *                                     was not a valid directory
     */
    public String extractFile(String path, File extractToLocation, boolean stripLeadingPathDirectories)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractFile";
        LOGGER.entering(CLASS, METHOD, path, extractToLocation, stripLeadingPathDirectories);
        validateNonEmptyString(path, "path", METHOD);
        validateExistingDirectory(extractToLocation, "extractToLocation", getArchiveFileName(), METHOD);

        String result = null;
        if (isPathIntoArchive(path)) {
            if (containsFile(path)) {
                if (stripLeadingPathDirectories) {
                    String dirToStrip;
                    String fileName;
                    if (path.endsWith(ZIP_SEP)) {
                        String tmp = path.substring(0, path.length() - 1);
                        int lastSlash = tmp.lastIndexOf('/');
                        if (lastSlash == -1) {
                            WLSDeployArchiveIOException aioe =
                                new WLSDeployArchiveIOException("WLSDPLY-01402", path, getArchiveFileName());
                            LOGGER.throwing(CLASS, METHOD, aioe);
                            throw aioe;
                        }
                        dirToStrip = tmp.substring(0, lastSlash);
                        fileName = path.substring(lastSlash + 1);
                    } else {
                        int lastSlash = path.lastIndexOf('/');
                        dirToStrip = path.substring(0, lastSlash);
                        fileName = path.substring(lastSlash + 1);
                    }
                    result = FileUtils.getCanonicalFile(new File(extractToLocation, fileName)).getAbsolutePath();
                    extractFileFromZip(path, dirToStrip, "", extractToLocation);
                } else {
                    result = FileUtils.getCanonicalFile(new File(extractToLocation, path)).getAbsolutePath();
                    extractFileFromZip(path, extractToLocation);
                }
            } else {
                WLSDeployArchiveIOException aioe =
                    new WLSDeployArchiveIOException("WLSDPLY-01403", path, getArchiveFileName());
                LOGGER.throwing(CLASS, METHOD, aioe);
                throw aioe;
            }
        } else {
            LOGGER.warning("WLSDPLY-01404", path);
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get the Base64-encoded hash for the specified archive file entry.
     *
     * @param path the path into the archive file
     * @return the Base64-encoded hash for the entry
     * @throws WLSDeployArchiveIOException if an error occurs
     */
    public String getFileHash(String path) throws WLSDeployArchiveIOException {
        final String METHOD = "getFileHash";

        LOGGER.entering(CLASS, METHOD, path);
        validateNonEmptyString(path, "path", METHOD);

        if (path.endsWith(ZIP_SEP)) {
            WLSDeployArchiveIOException aioe =
                new WLSDeployArchiveIOException("WLSDPLY-01405", getArchiveFileName(), path);
            LOGGER.throwing(CLASS, METHOD, aioe);
            throw aioe;
        }

        Map<String, InputStream> zipEntries = getZipFile().getZipEntries(path);
        if (zipEntries.isEmpty() || !zipEntries.containsKey(path)) {
            WLSDeployArchiveIOException aioe =
                new WLSDeployArchiveIOException("WLSDPLY-01406", getArchiveFileName(), path);
            LOGGER.throwing(CLASS, METHOD, aioe);
            closeMapInputStreams(zipEntries);
            getZipFile().close();
            throw aioe;
        }

        byte[] fileBytes;
        try {
            fileBytes = FileUtils.readInputStreamToByteArray(zipEntries.get(path));
        } catch (IOException ioe) {
            WLSDeployArchiveIOException aioe =
                new WLSDeployArchiveIOException("WLSDPLY-01407", ioe, getArchiveFileName(), path,
                    ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, aioe);
            throw aioe;
        } finally {
            closeMapInputStreams(zipEntries);
            getZipFile().close();
        }

        String result;
        try {
            result = FileUtils.computeHash(fileBytes);
        } catch (NoSuchAlgorithmException e) {
            WLSDeployArchiveIOException aioe =
                new WLSDeployArchiveIOException("WLSDPLY-01407", e, getArchiveFileName(), path,
                    e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, aioe);
            throw aioe;
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get archive path for the application name for use in the model.
     *
     * @param appPath name of the application
     * @return archive path for use in the model
     */
    public String getApplicationArchivePath(String appPath) {
        return getArchiveName(ARCHIVE_APPS_TARGET_DIR, appPath);
    }

    /**
     * Get the archive path for the application in a well-formed application directory
     * @param appPath name of the application path
     * @return archive path for use in the model
     */
    public String getApplicationDirectoryArchivePath(String appName, String appPath) {
        File zipAppPath = new File(appPath).getParentFile();
        File zipAppFile = new File(appPath);
        return ARCHIVE_STRUCT_APPS_TARGET_DIR + "/" + appName + "/" + zipAppPath.getName() + "/" + zipAppFile.getName();
    }

    /**
     * This method adds an application to the archive.  If an application with the same name already exists, this
     * method assumes that the new one also needs to be added so it changes the name to prevent conflicts by adding
     * a numeric value onto the file's basename (e.g., myapp(1).ear, myapp(2).ear).
     *
     * @param appPath - file name representing the actual path of the archive or directory in the local or remote
     *                file system
     * @return the relative path where the application will be unpacked by the unpackApplications() method
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String addApplication(String appPath) throws WLSDeployArchiveIOException {
        final String METHOD = "addApplication";

        LOGGER.entering(CLASS, METHOD, appPath);

        File filePath = new File(appPath);

        validateExistingFile(filePath, "appPath", getArchiveFileName(), METHOD, true);

        String newName = addItemToZip(ARCHIVE_APPS_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    public String replaceApplication(String appPath, String tempFile) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceApplication";
        LOGGER.entering(CLASS, METHOD, appPath);
        getZipFile().removeZipEntry(appPath);
        String newName = addApplication(tempFile);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    public String addApplicationFolder(String appName, String appPath)
            throws WLSDeployArchiveIOException {
        final String METHOD = "addApplicationFolder";
        LOGGER.entering(CLASS, METHOD, appName, appPath);
        File zipPath = new File(appPath);
        if (zipPath.getParentFile() != null) {
            zipPath = zipPath.getParentFile();
        }
        String firstPrefix = ARCHIVE_STRUCT_APPS_TARGET_DIR + "/" + appName + "/" + zipPath.getName();
        String newName = walkDownFolders(firstPrefix, zipPath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    public String addApplicationPlanFolder(String appName, String planDir)
            throws WLSDeployArchiveIOException {
        final String METHOD = "addApplicationPathFolder";
        LOGGER.entering(CLASS, METHOD, appName, planDir);
        File zipPlan = new File(planDir);
        String zipPrefix = ARCHIVE_STRUCT_APPS_TARGET_DIR + "/" + appName + "/" + zipPlan.getName();
        String newName = walkDownFolders(zipPrefix, zipPlan);

        LOGGER.exiting(CLASS, METHOD, newName);
        return zipPrefix;
    }

    /**
     * Get the list of application names in the archive.
     *
     * @return the list of application names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public List<String> listApplications() throws WLSDeployArchiveIOException {
        final String METHOD = "listApplications";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_APPS_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list...
        result.remove(ARCHIVE_APPS_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get the path of the ATP wallet in the archive.
     *
     * @return path of the ATP wallet
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public String getATPWallet() throws WLSDeployArchiveIOException {
        final String METHOD = "getATPWallet";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_ATP_WALLET_PATH + ZIP_SEP);
        result.remove(ARCHIVE_ATP_WALLET_PATH + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        if (result.isEmpty()) {
            return null;
        } else {
            return result.get(0);
        }
    }

    /**
     * Get the path of the OPSS wallet in the archive.
     *
     * @return path of the OPSS wallet
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public String getOPSSWallet() throws WLSDeployArchiveIOException {
        final String METHOD = "getOPSSWallet";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
        result.remove(ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        if (result.isEmpty()) {
            return null;
        } else {
            return result.get(0);
        }
    }

    /**
     * Extract the specified application from the archive to the domain home directory.
     *
     * @param applicationPath the application path into the archive file
     * @param domainHome      the domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     *                                     or the application path is empty
     */
    public void extractApplication(String applicationPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractApplication";

        LOGGER.entering(CLASS, METHOD, applicationPath);
        validateNonEmptyString(applicationPath, "applicationPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String appPath = applicationPath;
        if (!applicationPath.startsWith(ARCHIVE_STRUCT_APPS_TARGET_DIR) &&
            !applicationPath.startsWith(ARCHIVE_APPS_TARGET_DIR)) {
            appPath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + applicationPath;
        }
        extractFileFromZip(appPath, domainHome);
        LOGGER.exiting(CLASS, METHOD);

    }

    /**
     * Get the best guess of the name of the shared library as if it is in the archive file.
     * This does not reconcile duplicate names and other items that require the archive file.
     * @param shlibPath file name to find the name for
     * @return name for model archive file name
     */
    public String getSharedLibraryArchivePath(String shlibPath) {
        return getArchiveName(ARCHIVE_SHLIBS_TARGET_DIR, shlibPath);
    }

    /**
     * Add a shared library to the archive.  If a shared library with the same name already exists, this method
     * assumes that the new one also needs to be added so it changes the name to prevent conflicts by adding a
     * numeric value onto the file's basename (e.g., myapp(1).ear, myapp(2).ear).
     *
     * @param shlibPath - File name representing the actual path of the archive or directory in the local or remote
     *                  file system
     * @return the relative path where the shared library will be unpacked by the unpackSharedLibraries() method
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String addSharedLibrary(String shlibPath) throws WLSDeployArchiveIOException {
        final String METHOD = "addSharedLibrary";
        File filePath = new File(shlibPath);
        LOGGER.entering(CLASS, METHOD, shlibPath);
        validateExistingFile(filePath, "shlibPath", getArchiveFileName(), METHOD, true);

        String newName = addItemToZip(ARCHIVE_SHLIBS_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the list of shared library names in the archive.
     *
     * @return the list of shared library names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public List<String> listSharedLibraries() throws WLSDeployArchiveIOException {
        final String METHOD = "listSharedLibraries";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list...
        result.remove(ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Extract the specified shared library from the archive to the domain home directory.
     *
     * @param sharedLibraryPath the shared library path into the archive file
     * @param domainHome        the domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     *                                     or the application path is empty
     */
    public void extractSharedLibrary(String sharedLibraryPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractSharedLibrary";

        LOGGER.entering(CLASS, METHOD, sharedLibraryPath);
        validateNonEmptyString(sharedLibraryPath, "sharedLibraryPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String libPath = sharedLibraryPath;
        if (!sharedLibraryPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR)) {
            libPath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + sharedLibraryPath;
        }
        extractFileFromZip(libPath, domainHome);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Get the archive file name for the Domain library file. This does not reconcile duplicate names or other
     * items that require the archive file.
     * @param domainLibPath the file name to get the archive file name
     * @return model ready archive file name
     */
    public String getDomainLibArchiveName(String domainLibPath) {
        return getArchiveName(ARCHIVE_DOMLIB_TARGET_DIR, domainLibPath);
    }

    /**
     * Adds a $DOMAIN_HOME/lib library to the archive.  If a library with the same name already exists, this method
     * assumes that the new one also needs to be added so it changes the name to prevent conflicts by adding a
     * numeric value onto the file's basename (e.g., mylib(1).jar, mylib(2).jar).
     *
     * @param domainLibPath - File name representing the actual path of the archive or directory in the local or remote
     *                      file system
     * @return the relative path where the library will be unpacked by the unpackApplications() method
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String addDomainLibLibrary(String domainLibPath) throws WLSDeployArchiveIOException {
        final String METHOD = "addDomainLibLibrary";

        LOGGER.entering(CLASS, METHOD, domainLibPath);
        File filePath = new File(domainLibPath);
        validateExistingFile(filePath, "domainLibPath", getArchiveFileName(), METHOD);

        String newName = addItemToZip(ARCHIVE_DOMLIB_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the list of $DOMAIN_HOME/lib library names in the archive.
     *
     * @return the list of $DOMAIN_HOME/lib library names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public List<String> listDomainLibLibraries() throws WLSDeployArchiveIOException {
        final String METHOD = "listDomainLibLibraries";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list...
        result.remove(ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Extract the specified domain library to the specified location (e.g., $DOMAIN_HOME/lib).
     *
     * @param archivePath       the path of the library within the archive
     * @param extractToLocation the location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while extracting or writing the file
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public void extractDomainLibLibrary(String archivePath, File extractToLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "extractDomainLibLibrary";

        LOGGER.entering(CLASS, METHOD, archivePath, extractToLocation);
        validateNonEmptyString(archivePath, "archivePath", METHOD);
        validateExistingDirectory(extractToLocation, "extractToLocation", getArchiveFileName(), METHOD);

        extractFileFromZip(archivePath, ARCHIVE_DOMLIB_TARGET_DIR, "", extractToLocation);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Get the archive path for the domain/bin scripts
     *
     * @param domainBinPath domain/bin
     * @return Archive path for domain/bin in the model
     */
    public String getDomainBinScriptArchivePath(String domainBinPath) {
        return getArchiveName(ARCHIVE_DOM_BIN_TARGET_DIR, domainBinPath);
    }

    /**
     * Adds a $DOMAIN_HOME/bin script to the archive.  If a script with the same name already exists, this method
     * assumes that the new one also needs to be added so it changes the name to prevent conflicts by adding a
     * numeric value onto the file's basename (e.g., myscript(1).cmd, myscript(2).cmd).
     *
     * @param domainBinPath - File name representing the actual path of the script file in the local or remote
     *                      file system
     * @return the relative path where the script is stored within the archive
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String addDomainBinScript(String domainBinPath) throws WLSDeployArchiveIOException {
        final String METHOD = "addDomainBinScript";

        LOGGER.entering(CLASS, METHOD, domainBinPath);
        File filePath = new File(domainBinPath);
        validateExistingFile(filePath, "domainBinPath", getArchiveFileName(), METHOD);

        String newName = addItemToZip(ARCHIVE_DOM_BIN_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the list of $DOMAIN_HOME/bin script names in the archive.
     *
     * @return the list of $DOMAIN_HOME/bin script names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public List<String> listDomainBinScripts() throws WLSDeployArchiveIOException {
        final String METHOD = "listDomainBinScripts";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list...
        result.remove(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Extract the specified domain bin user script to the specified location (e.g., $DOMAIN_HOME/bin).
     *
     * @param archivePath       the path of the script within the archive
     * @param extractToLocation the location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while extracting or writing the file
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public void extractDomainBinScript(String archivePath, File extractToLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "extractDomainBinScript";

        LOGGER.entering(CLASS, METHOD, archivePath, extractToLocation);
        validateNonEmptyString(archivePath, "archivePath", METHOD);
        validateExistingDirectory(extractToLocation, "extractToLocation", getArchiveFileName(), METHOD);

        extractFileFromZip(archivePath, ARCHIVE_DOM_BIN_TARGET_DIR, "", extractToLocation);
        LOGGER.exiting(CLASS, METHOD);
    }

    public void removeDomainBinScripts() throws WLSDeployArchiveIOException {
        final String METHOD = "removeDomainBinScripts";

        LOGGER.entering(CLASS, METHOD);
        getZipFile().removeZipEntries(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Get the archive path for the classpath library for use in the model.
     * @param libPath to get the archive path for
     * @return Archive path for the classpath library for use in the model
     */
    public String getClasspathArchivePath(String libPath) {
        return getArchiveName(ARCHIVE_CPLIB_TARGET_DIR, libPath);
    }

    /**
     * This method adds a classpath library to the archive.  If a library with the same name already exists, this
     * method assumes that the new one also needs to be added so it changes the name to prevent conflicts by adding
     * a numeric value onto the file's basename (e.g., mylib(1).jar, mylib(2).jar).
     *
     * @param libPath - File name representing the actual path of the archive or directory in the local or remote
     *                file system
     * @return the relative path where the library will be unpacked by the unpackApplications() method
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String addClasspathLibrary(String libPath) throws WLSDeployArchiveIOException {
        final String METHOD = "addClasspathLibrary";

        LOGGER.entering(CLASS, METHOD, libPath);
        File filePath = new File(libPath);

        validateExistingFile(filePath, "libPath", getArchiveFileName(), METHOD, true);

        String newName = addItemToZip(ARCHIVE_CPLIB_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the list of classpath library names in the archive.
     *
     * @return the list of $DOMAIN_HOME/lib library names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public List<String> listClasspathLibraries() throws WLSDeployArchiveIOException {
        final String METHOD = "listClasspathLibraries";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list...
        result.remove(ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Extract the classpath libraries in the archive to the specified domain home directory.
     *
     * @param domainHome the domain home directory
     * @throws WLSDeployArchiveIOException in an error occurs reading the archive or writing the files.
     * @throws IllegalArgumentException    if the domain home directory is not a valid, existing directory
     */
    public void extractClasspathLibraries(File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractClasspathLibraries";

        LOGGER.entering(CLASS, METHOD, domainHome);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        extractDirectoryFromZip(ARCHIVE_CPLIB_TARGET_DIR, domainHome);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Get the list of user custom file names in the archive.
     *
     * @return the list of $DOMAIN_HOME/wlsdeploy/custom library names
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive
     */
    public List<String> listCustomFiles() throws WLSDeployArchiveIOException {
        final String METHOD = "listCustomFiles";

        LOGGER.entering(CLASS, METHOD);
        List<String> result = getZipFile().listZipEntries(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP);
        // Remove the top-level directory entry from the list...
        result.remove(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Extract the user custom files in the archive to the specified domain home directory.
     *
     * @param domainHome the domain home directory
     * @throws WLSDeployArchiveIOException in an error occurs reading the archive or writing the files.
     * @throws IllegalArgumentException    if the domain home directory is not a valid, existing directory
     */
    public void extractCustomFiles(File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractCustomFiles";

        LOGGER.entering(CLASS, METHOD, domainHome);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        extractDirectoryFromZip(ARCHIVE_CUSTOM_TARGET_DIR, domainHome);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Get the archive path of the application deployment plan.
     * @param planFile The deployment plan file name
     * @return Archive path for use in the model
     */
    public String getApplicationPlanArchivePath(String planFile) {
        return getArchiveName(ARCHIVE_APPS_TARGET_DIR, planFile);
    }

    /**
     * Get the archive path of a well formed plan directory in app directory,
     *
     * @param appName The application name of the app directory
     * @param planDir The deployment plan file directory
     * @return Archive path for use in the model
     */
    public String getApplicationPlanDirArchivePath(String appName, String planDir) {
        File zipPath = new File(planDir);
        return ARCHIVE_STRUCT_APPS_TARGET_DIR + "/" + appName + "/" + zipPath.getName();
    }

    /**
     * Adds an application's deployment plan file to the archive.
     *
     * @param planFile      the deployment plan file name
     * @param preferredName the preferred name of the file to add
     * @return the actual name of the file in the archive
     * @throws WLSDeployArchiveIOException if an error occurs adding the file
     * @throws IllegalArgumentException    if the file does not exist or the preferredName was empty or null
     */
    public String addApplicationDeploymentPlan(String planFile, String preferredName) throws WLSDeployArchiveIOException {
        final String METHOD = "addApplicationDeploymentPlan";

        LOGGER.entering(CLASS, METHOD, planFile, preferredName);
        File filePath = new File(planFile);

        validateExistingFile(filePath, "planFile", getArchiveFileName(), METHOD);
        validateNonEmptyString(preferredName, "preferredName", METHOD);

        String newName = addItemToZip(ARCHIVE_APPS_TARGET_DIR, filePath, preferredName);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the Archive Path for the Shared Library Plan
     * @param planFile Shared Library Deployment Plan file name
     * @return Archive path for the plan file for use in the model
     */
    public String getShlibPlanArchivePath(String planFile) {
        return getArchiveName(ARCHIVE_SHLIBS_TARGET_DIR, planFile);
    }

    /**
     * Adds a shared library's deployment plan file to the archive.
     *
     * @param planFile      the deployment plan file name
     * @param preferredName the preferred name of the file to add
     * @return the actual name of the file in the archive
     * @throws WLSDeployArchiveIOException if an error occurs adding the file
     * @throws IllegalArgumentException    if the file does not exist or the preferredName was empty or null
     */
    public String addSharedLibraryDeploymentPlan(String planFile, String preferredName)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addSharedLibraryDeploymentPlan";

        LOGGER.entering(CLASS, METHOD, planFile, preferredName);
        File filePath = new File(planFile);

        validateExistingFile(filePath, "planFile", getArchiveFileName(), METHOD);
        validateNonEmptyString(preferredName, "preferredName", METHOD);

        String newName = addItemToZip(ARCHIVE_SHLIBS_TARGET_DIR, filePath, preferredName);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the archive path for the scriptfile name.
     * @param scriptFile the script file to get the path name
     * @return The name of the file in the archive for use in the model
     */
    public String getScriptArchivePath(String scriptFile) {
        return getArchiveName(ARCHIVE_SCRIPTS_DIR, scriptFile);
    }

    /**
     * Add a script file to the archive.
     *
     * @param scriptFile the script file to add
     * @return the actual name of the file in the archive
     * @throws WLSDeployArchiveIOException if an error occurs adding the file
     * @throws IllegalArgumentException    if the file does not exist
     */
    public String addScript(String scriptFile) throws WLSDeployArchiveIOException {
        final String METHOD = "addScript";

        LOGGER.entering(CLASS, METHOD, scriptFile);
        File filePath = new File(scriptFile);

        validateExistingFile(filePath, "scriptFile", getArchiveFileName(), METHOD);
        String newName = addItemToZip(ARCHIVE_SCRIPTS_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the archive path for the servr identity key store file for use in the model
     * @param serverName name of the server used to separate paths
     * @param keystoreFile the file to get the archive path name
     * @return Archive path name for the server key store file
     */
    public String getServerKeyStoreArchivePath(String serverName, String keystoreFile) {
        return getArchiveName(ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + serverName, keystoreFile);
    }

    /**
     * Add a Server Identity Key Store file to the server's directory in the archive.
     *
     * @param serverName   the Server name used to segregate the directories
     * @param keystoreFile the file to add
     * @return the new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the file does not exist or the clusterName is empty or null
     */
    public String addServerKeyStoreFile(String serverName, String keystoreFile) throws WLSDeployArchiveIOException {
        final String METHOD = "addServerKeyStoreFile";

        LOGGER.entering(CLASS, METHOD, serverName, keystoreFile);
        File filePath = new File(keystoreFile);

        validateNonEmptyString(serverName, "serverName", METHOD);
        validateExistingFile(filePath, "keyStoreFile", getArchiveFileName(), METHOD);
        String newName = addItemToZip(ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + serverName, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the archive path name for the WebAppContainer mime mapping file.
     *
     * @param mimeMappingFile the path name of the file to use
     * @return The archive path of the mimeMappingFile for the model
     */
    public String getMimeMappingArchivePath(String mimeMappingFile) {
        return getArchiveName(ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP, mimeMappingFile);
    }

    /**
     * Add a WebAppContainer mime mapping file to the archive.
     *
     * @param mimeMappingFile the file to add
     * @return the new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the file does not exist or the clusterName is empty or null
     */
    public String addMimeMappingFile(String mimeMappingFile) throws WLSDeployArchiveIOException {
        final String METHOD = "addMimeMappingFile";

        LOGGER.entering(CLASS, METHOD, mimeMappingFile);
        File filePath = new File(mimeMappingFile);

        validateExistingFile(filePath, "mimeMappingFile", getArchiveFileName(), METHOD);
        String newName = addItemToZip(ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the Coherence configuration file name in the archive to use in the model.
     *
     * @param clusterName The Coherence cluster name used to segregate the directories
     * @param configFile the file name of the config file
     * @return Archive name for use in the model
     */
    public String getCoherenceConfigArchivePath(String clusterName, String configFile) {
        return getArchiveName(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, configFile);
    }

    /**
     * Add a Coherence configuration file to the archive.
     *
     * @param clusterName the Coherence cluster name used to segregate the directories
     * @param configFile  the file to add
     * @return thje new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the file does not exist or the clusterName is empty or null
     */
    public String addCoherenceConfigFile(String clusterName, String configFile) throws WLSDeployArchiveIOException {
        final String METHOD = "addCoherenceConfigFile";

        LOGGER.entering(CLASS, METHOD, clusterName, configFile);
        File filePath = new File(configFile);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateExistingFile(filePath, "configFile", getArchiveFileName(), METHOD);
        String newName = addItemToZip(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the archive name for the foreign server binding file.
     * @param foreignServer The foreign server name used to segregate the directories
     * @param configFile The file name to add
     * @return The location of the file in the archive to use in the model
     */
    public String getForeignServerArchivePath(String foreignServer, String configFile) {
        return getArchiveName(ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServer, configFile);
    }

    /**
     * Add a Foreign Server binding file to the archive
     *
     * @param foreignServer the Foreign Server name used to segregate the directories
     * @param configFile  the file or directory to add
     * @return the new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the file does not exist or the foreignServer is empty or null
     */
    public String addForeignServerFile(String foreignServer, String configFile) throws WLSDeployArchiveIOException {
        final String METHOD = "addForeignServerFile";

        LOGGER.entering(CLASS, METHOD, foreignServer, configFile);
        File filePath = new File(configFile);
        validateNonEmptyString(foreignServer, "foreignServerName", METHOD);
        validateExistingFile(filePath, "configFile", getArchiveFileName(), METHOD, true);
        String newName = addItemToZip(ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServer, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    public String getCoherenceURLArchivePath(String clusterName, URL urlForConfigFile) {
        return getURLArchiveName(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, urlForConfigFile,
                 true);
    }

    /**
     * Add a Coherence configuration file to the archive from an http site.
     *
     * @param clusterName      the Coherence cluster name used to segregate the directories
     * @param urlForConfigFile a file object representing the path at the remote url
     * @return the new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the clusterName is empty or null or the urlForConfigFile is null
     */
    public String addCoherenceConfigFileFromUrl(String clusterName, URL urlForConfigFile)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addCoherenceConfigFileFromUrl";

        LOGGER.entering(CLASS, METHOD, clusterName, urlForConfigFile);
        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonNullObject(urlForConfigFile, "urlForConfigFile", METHOD);
        String newName = addUrlToZip(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, urlForConfigFile,
                COHERENCE_CONFIG_FILE_EXTENSION, true);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the name of the persistence directory as an archive path. This does not reconcile duplicates or other
     * items deeper in the zip file logic.
     * @param clusterName name of cluster specific to path
     * @param directoryType type of persistence directory
     * @return Archive style path for directory
     */
    public String getCoherencePersistArchivePath(String clusterName, String directoryType){
        return getArchiveName(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, directoryType);
    }

    /**
     * Add an empty directory to the archive file for the coherence cluster using the persistence directory type value.
     * The directory type is stored under the unique coherence cluster name.
     *
     * @param clusterName   name of the coherence cluster to which the persistence directory belongs
     * @param directoryType type of the coherence cluster persistence directory
     * @return unique directory name
     * @throws WLSDeployArchiveIOException unexpected exception adding the directory name to the archive file
     */
    public String addCoherencePersistenceDirectory(String clusterName, String directoryType)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addCoherencePersistenceDirectory";
        LOGGER.entering(CLASS, METHOD, clusterName, directoryType);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(directoryType, "fileStoreName", METHOD);
        String newName = addEmptyDirectoryToZip(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName,
            directoryType);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    public String getFileStoreArchivePath(String fileStoreName) {
        return getArchiveName(ARCHIVE_FILE_STORE_TARGET_DIR, fileStoreName);
    }

    /**
     * Add an empty directory to the archive file using the File Store name.
     *
     * @param fileStoreName name of the File Store
     * @return unique directory name created using the file store name
     * @throws WLSDeployArchiveIOException unexpected exception adding the directory name to the archive file
     */
    public String addFileStoreDirectory(String fileStoreName) throws WLSDeployArchiveIOException {
        final String METHOD = "addFileStoreDirectory";
        LOGGER.entering(CLASS, METHOD, fileStoreName);
        validateNonEmptyString(fileStoreName, "fileStoreName", METHOD);
        String newName = addEmptyDirectoryToZip(ARCHIVE_FILE_STORE_TARGET_DIR, fileStoreName);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Get the archive path to Node Manager Identity Key Store file. This does not reconcile duplicate names or
     * other items that the archive file does when adding to the archive.
     * @param keystoreFile file name of the key store file
     * @return archive file path for the model
     */
    public String getNodeManagerKeyStoreArchivePath(String keystoreFile) {
        return getArchiveName(ARCHIVE_NODE_MANAGER_TARGET_DIR, keystoreFile);
    }

    /**
     * Add a Node Manager Identity Key Store file to the node manager directory in the archive.
     *
     * @param keystoreFile the file to add
     * @return the new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the file does not exist
     */
    public String addNodeManagerKeyStoreFile(String keystoreFile) throws WLSDeployArchiveIOException {
        final String METHOD = "addNodeManagerKeyStoreFile";

        LOGGER.entering(CLASS, METHOD, keystoreFile);
        File filePath = new File(keystoreFile);
        validateExistingFile(filePath, "keyStoreFile", getArchiveFileName(), METHOD);
        String newName = addItemToZip(ARCHIVE_NODE_MANAGER_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Return the manifest for the specified path in the archive, if present.
     * The path may refer to a packaged EAR/JAR/WAR, or an exploded entry.
     * @param sourcePath the path to be checked
     * @return the Manifest object, or null
     * @throws WLSDeployArchiveIOException if there is a problem reading the archive, or the manifest
     */
    public Manifest getManifest(String sourcePath) throws WLSDeployArchiveIOException {
        try {
            if(containsFile(sourcePath)) {
                // a jarred app or library in the archive.
                try(ZipInputStream zipStream = new ZipInputStream(getZipFile().getZipEntry(sourcePath))) {
                    // JarInputStream.getManifest() has problems if MANIFEST.MF is not the first entry,
                    // so use ZipInputStream and search for the specific entry.
                    ZipEntry zipEntry;
                    while((zipEntry = zipStream.getNextEntry()) != null) {
                        if(JarFile.MANIFEST_NAME.equals(zipEntry.getName())) {
                            Manifest manifest = new Manifest(zipStream);
                            zipStream.closeEntry();
                            return manifest;
                        }
                        zipStream.closeEntry();
                    }
                }
            } else if(containsPath(sourcePath)) {
                // an exploded app or library in the archive.
                String manifestPath = sourcePath + "/" + JarFile.MANIFEST_NAME;
                if (containsFile(manifestPath)) {
                    try (InputStream inStream = getZipFile().getZipEntry(manifestPath)) {
                        return new Manifest(inStream);
                    }
                }
            }
        } catch(IOException e) {
            WLSDeployArchiveIOException aioe = new WLSDeployArchiveIOException("WLSDPLY-01426", sourcePath,
                    getArchiveFileName(), e.getLocalizedMessage());
            LOGGER.throwing(aioe);
            throw aioe;
        }
        return null;
    }

    /**
     * This method removes all binaries from the archive.  This method is intended to
     * be invoked by discovery to remove binaries from a previous run that might
     * exist in the archive to make it possible for discovery to be truly idempotent.
     *
     * @throws WLSDeployArchiveIOException if an error is encountered removing the binaries
     */
    public void removeAllBinaries() throws WLSDeployArchiveIOException {
        getZipFile().removeZipEntries(WLSDPLY_ARCHIVE_BINARY_DIR + ZIP_SEP);
    }

    /**
     * Closes the underlying zip file and any open streams.
     */
    public void close() {
        if (getZipFile() != null) {
            getZipFile().close();
        }
    }

    ///////////////////////////////////////////////////////////////////////////////////////////
    // Protected Helper methods                                                              //
    ///////////////////////////////////////////////////////////////////////////////////////////

    protected WLSDeployZipFile getZipFile() {
        return zipFile;
    }

    protected void setZipFile(WLSDeployZipFile zipFile) {
        this.zipFile = zipFile;
    }

    protected String addEmptyDirectoryToZip(String zipPathPrefix, String directoryNameToAdd)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addEmptyDirectoryToZip";

        LOGGER.entering(CLASS, METHOD, zipPathPrefix, directoryNameToAdd);
        String newName = zipPathPrefix;
        if (!newName.endsWith(ZIP_SEP)) {
            newName += ZIP_SEP;
        }
        newName += directoryNameToAdd;
        newName = getZipFile().addZipDirectoryEntry(newName, true);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    protected String getArchiveName(String zipPathPrefix, String itemToAdd) {
        return getArchiveName(zipPathPrefix, itemToAdd, true);
    }

    protected String getArchiveName(String zipPathPrefix, String itemToAdd, boolean useFileNameInEntryPath) {
        String newName = zipPathPrefix;
        if (useFileNameInEntryPath) {
            if (!newName.endsWith(ZIP_SEP)) {
                newName += ZIP_SEP;
            }
            newName += new File(itemToAdd).getName();
        }
        return newName;
    }
    protected String addItemToZip(String zipPathPrefix, File itemToAdd) throws WLSDeployArchiveIOException {
        return addItemToZip(zipPathPrefix, itemToAdd, true);
    }

    protected String addItemToZip(String zipPathPrefix, File itemToAdd, boolean useFileNameInEntryPath)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addItemToZip";

        LOGGER.entering(CLASS, METHOD, zipPathPrefix, itemToAdd.getAbsolutePath(), useFileNameInEntryPath);
        String newName = getArchiveName(zipPathPrefix, itemToAdd.getName(), useFileNameInEntryPath);
        if (itemToAdd.isDirectory()) {
            if (!newName.endsWith(ZIP_SEP)) {
                newName += ZIP_SEP;
            }
            LOGGER.finer("WLSDPLY-01408", newName, itemToAdd);
            newName = getZipFile().addDirectoryZipEntries(newName, itemToAdd);
            LOGGER.finer("WLSDPLY-01409", newName, itemToAdd);
        } else {
            newName = addSingleFileToZip(itemToAdd, newName, METHOD);
        }
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    protected String addItemToZip(String zipPathPrefix, File itemToAdd, String preferredFileName)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addItemToZip";

        LOGGER.entering(CLASS, METHOD, zipPathPrefix, itemToAdd.getAbsolutePath(), preferredFileName);
        String newName = zipPathPrefix;
        if (!newName.endsWith(ZIP_SEP)) {
            newName += ZIP_SEP;
        }
        newName += preferredFileName;
        newName = addSingleFileToZip(itemToAdd, newName, METHOD);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    protected String getURLArchiveName(String zipPathPrefix, URL url, boolean useFileNameInEntryPath) {
        String newName = zipPathPrefix;
        String urlFileName = new File(url.getFile()).getName();
        if (useFileNameInEntryPath) {
            if (!newName.endsWith(ZIP_SEP)) {
                newName += ZIP_SEP;
            }
            newName += urlFileName;
        }
        return newName;
    }

    protected String addUrlToZip(String zipPathPrefix, URL url, String extension, boolean useFileNameInEntryPath)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addUrlToZip";

        LOGGER.entering(CLASS, METHOD, zipPathPrefix, extension, useFileNameInEntryPath);
        HttpURLConnection connection = null;
        InputStream is = null;
        File tmpFile = null;
        String newName = null;
        FileOutputStream fos = null;
        String urlFileName = getURLArchiveName(zipPathPrefix, url, useFileNameInEntryPath);
        File findDir = new File(getArchiveFileName()).getParentFile();
        try {
            connection = (HttpURLConnection) url.openConnection();
            connection.setDoInput(true);
            connection.setDoOutput(false);
            is = connection.getInputStream();
            int rc = connection.getResponseCode();
            if (!(rc == HTTP_OK || rc == HTTP_CREATED)) {
                WLSDeployArchiveIOException aioe = new WLSDeployArchiveIOException("WLSDPLY-01410", url, rc);
                LOGGER.throwing(aioe);
                throw aioe;
            }
            tmpFile = File.createTempFile(urlFileName, extension, findDir);

            fos = new FileOutputStream(tmpFile);
            copyFile(is, fos);
            newName = addSingleFileToZip(tmpFile, newName, METHOD);
        } catch (IOException ioe) {
            WLSDeployArchiveIOException aioe =
                    new WLSDeployArchiveIOException("WLSDPLY-01410", ioe, url, ioe.getLocalizedMessage());
            LOGGER.throwing(aioe);
            throw aioe;
        } catch (SecurityException se) {
            WLSDeployArchiveIOException aioe =
                new WLSDeployArchiveIOException("WLSDPLY-01411", se, url, se.getLocalizedMessage());
            LOGGER.throwing(aioe);
            throw aioe;
        } finally {
            if (fos != null) {
                try {
                    fos.close();
                } catch (IOException e) {
                    LOGGER.warning("WLSDPLY-01413", e, getArchiveFileName(), e.getLocalizedMessage());
                }
            }
            if (connection != null) {
                connection.disconnect();
            }
            if (is != null) {
                try {
                    is.close();
                } catch (IOException e) {
                    LOGGER.warning("WLSDPLY-01412", e, url, e.getLocalizedMessage());
                }
            }
            if (tmpFile != null && !tmpFile.delete()) {
                tmpFile.deleteOnExit();
            }
        }
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    protected void extractDirectoryFromZip(String directoryName, File extractToLocation)
        throws WLSDeployArchiveIOException {
        extractDirectoryFromZip(directoryName, directoryName, extractToLocation);
    }

    protected void extractDirectoryFromZip(String fromDirectoryName, String toDirectoryName, File extractToLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractDirectoryFromZip";

        LOGGER.entering(CLASS, METHOD, fromDirectoryName, toDirectoryName, extractToLocation.getAbsolutePath());
        String dirName = fromDirectoryName;
        if (!dirName.endsWith(ZIP_SEP)) {
            dirName += ZIP_SEP;
        }
        Map<String, InputStream> zipEntries = getZipFile().getZipEntries(dirName);
        FileOutputStream outputStream;
        File targetFile = null;
        try {
            if (zipEntries != null && !zipEntries.isEmpty()) {
                for (Map.Entry<String, InputStream> zipEntry : zipEntries.entrySet()) {
                    String entryName = zipEntry.getKey();
                    String targetFileName = entryName.replace(fromDirectoryName + ZIP_SEP, toDirectoryName + SEP);
                    targetFile = new File(extractToLocation, targetFileName);
                    File targetDirectory;
                    if (entryName.endsWith(ZIP_SEP)) {
                        targetDirectory = targetFile;
                    } else {
                        targetDirectory = targetFile.getParentFile();
                    }
                    if (!targetDirectory.exists() && !targetDirectory.mkdirs()) {
                        WLSDeployArchiveIOException wdaioe =
                            new WLSDeployArchiveIOException("WLSDPLY-01414", getArchiveFileName(),
                                targetDirectory.getAbsolutePath());
                        LOGGER.throwing(CLASS, METHOD, wdaioe);
                        throw wdaioe;
                    }

                    // no need to copy a directory entry
                    //
                    if (!entryName.endsWith(ZIP_SEP)) {
                        InputStream inputStream = zipEntry.getValue();
                        // overwrite any existing file
                        outputStream = new FileOutputStream(targetFile, false);
                        copyFile(inputStream, outputStream);
                        outputStream.close();
                    }
                }
            }
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe =
                new WLSDeployArchiveIOException("WLSDPLY-01415", ioe, getArchiveFileName(),
                    targetFile.getAbsolutePath(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        } finally {
            closeMapInputStreams(zipEntries);
            getZipFile().close();
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    protected void extractFileFromZip(String itemToExtract, File extractToLocation) throws WLSDeployArchiveIOException {
        extractFileFromZip(itemToExtract, null, null, extractToLocation);
    }

    protected void extractFileFromZip(String itemToExtract, String fromDir, String toDir, File extractToLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractFileFromZip";

        LOGGER.entering(CLASS, METHOD, itemToExtract, fromDir, toDir, extractToLocation);
        InputStream inputStream = getZipFile().getZipEntry(itemToExtract);
        if (inputStream == null) {
            WLSDeployArchiveIOException wdaioe =
                new WLSDeployArchiveIOException("WLSDPLY-01416", getArchiveFileName(), itemToExtract);
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        }

        String targetFileName = itemToExtract.replace(fromDir + ZIP_SEP, toDir + SEP);
        File targetFile = new File(extractToLocation, targetFileName);
        File targetDirectory = targetFile.getParentFile();
        if (!targetDirectory.exists() && !targetDirectory.mkdirs()) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01414", getArchiveFileName(),
                targetDirectory.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        }
        // overwrite any existing file
        try (FileOutputStream outputStream = new FileOutputStream(targetFile, false)) {
            copyFile(inputStream, outputStream);
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe =
                new WLSDeployArchiveIOException("WLSDPLY-01415", ioe, getArchiveFileName(),
                    targetFile.getAbsolutePath(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        } finally {
            try {
                inputStream.close();
            } catch (IOException ignore) {
                LOGGER.warning("WLSDPLY-01417", ignore, itemToExtract, ignore.getLocalizedMessage());
            }
            getZipFile().close();
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private Helper methods used by the protected methods above...         //
    ///////////////////////////////////////////////////////////////////////////

    private static boolean zipListContainsPath(List<String> entries, String path) {
        boolean foundInList = false;
        if (path != null && entries != null) {
            for (String entry : entries) {
                if (entry.startsWith(path)) {
                    foundInList = true;
                    break;
                }
            }
        }
        return foundInList;
    }

    private static void copyFile(InputStream input, FileOutputStream output) throws IOException {
        byte[] readBuffer = new byte[READ_BUFFER_SIZE];

        int bytesRead;
        while (true) {
            bytesRead = input.read(readBuffer);
            if (bytesRead < 0) {
                break;
            }
            output.write(readBuffer, 0, bytesRead);
        }
    }

    private static void closeMapInputStreams(Map<String, InputStream> map) {
        if (map != null) {
            for (Map.Entry<String, InputStream> entry : map.entrySet()) {
                InputStream stream = entry.getValue();
                try {
                    if (stream != null) {
                        stream.close();
                    }
                } catch (IOException ignore) {
                    // we are just trying to cleanup so ignore this error
                    LOGGER.warning("WLSDPLY-01417", ignore, entry.getKey(), ignore.getLocalizedMessage());
                }
            }
        }
    }

    private String addSingleFileToZip(File itemToAdd, String preferredName, String callingMethod)
        throws WLSDeployArchiveIOException {

        String newName = null;
        FileInputStream inputStream = null;
        try {
            inputStream = getFileInputStream(itemToAdd, preferredName, getArchiveFileName(), callingMethod);
            LOGGER.finer("WLSDPLY-01418", preferredName, itemToAdd);
            newName = getZipFile().addZipEntry(preferredName, inputStream, true);
            LOGGER.finer("WLSDPLY-01419", newName, itemToAdd);
        } finally {
            if (inputStream != null) {
                try {
                    inputStream.close();
                } catch (IOException ignore) {
                    LOGGER.warning("WLSDPLY-01420", ignore, itemToAdd.getPath(), ignore.getLocalizedMessage());
                }
            }
        }
        return newName;
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private Static Helper Methods                                         //
    ///////////////////////////////////////////////////////////////////////////

    private static void validateExistingFile(File file, String argName, String fileName, String callingMethod) {
        validateExistingFile(file, argName, fileName, callingMethod, false);
    }

    private static void validateExistingFile(File file, String argName, String fileName, String callingMethod,
        boolean allowDirectories) {
        final String METHOD = "validateExistingFile";

        LOGGER.entering(CLASS, METHOD, file, argName, fileName, callingMethod, allowDirectories);
        if (file == null) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01104", callingMethod, CLASS, argName);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!file.exists()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01421", fileName, file);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!allowDirectories && file.isDirectory()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01422", fileName, file);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static void validateExistingDirectory(File directory, String argName, String fileName,
        String callingMethod) {
        final String METHOD = "validateExistingDirectory";

        LOGGER.entering(CLASS, METHOD, directory, argName, fileName, callingMethod);
        if (directory == null) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01104", callingMethod, CLASS, argName);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!directory.exists()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01423", fileName, directory);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        } else if (!directory.isDirectory()) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01424", fileName, directory);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static void validateNonEmptyString(String argValue, String argName, String callingMethod) {
        final String METHOD = "validateNonEmptyString";

        LOGGER.entering(CLASS, METHOD, argValue, argName, callingMethod);
        if (StringUtils.isEmpty(argValue)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01104", callingMethod, CLASS, argName);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static void validateNonNullObject(Object argValue, String argName, String callingMethod) {
        final String METHOD = "validateNonNullObject";

        LOGGER.entering(CLASS, METHOD, argValue, argName, callingMethod);
        if (argValue == null) {
            String message = ExceptionHelper.getMessage("WLSDPLY-01104", callingMethod, CLASS, argName);
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static FileInputStream getFileInputStream(File f, String itemName, String archiveName, String callingMethod)
        throws WLSDeployArchiveIOException {
        FileInputStream inputStream;
        try {
            inputStream = new FileInputStream(f);
        } catch (IOException ioe) {
            WLSDeployArchiveIOException wdaioe =
                new WLSDeployArchiveIOException("WLSDPLY-01425", ioe, archiveName, f.getAbsolutePath(), itemName,
                    ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, callingMethod, wdaioe);
            throw wdaioe;
        }
        return inputStream;
    }

    private String walkDownFolders(String zipPrefix, File zipPath) throws WLSDeployArchiveIOException {
        String newSourceName = null;
        if (zipPath != null) {
            File[] fileList = zipPath.listFiles();
            if (fileList != null) {
                for (File item : fileList) {
                    newSourceName = addItemToZip(zipPrefix, item);
                }
            }
        }
        return newSourceName;
    }

}
