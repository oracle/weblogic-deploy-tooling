/*
 * Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.
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
import java.nio.file.Files;
import java.security.NoSuchAlgorithmException;
import java.util.List;
import java.util.ListIterator;
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

    public static final String ZIP_SEP = "/";

    public static final String WLSDPLY_ARCHIVE_BINARY_DIR = "wlsdeploy";

    /**
     * Top-level archive subdirectory where the config will be extracted.
     */
    public static final String ARCHIVE_CONFIG_TARGET_DIR = WLSDPLY_ARCHIVE_BINARY_DIR + "/config";

    // Deprecated top-level archive subdirectory where the atp wallet is stored.
    public static final String OLD_ARCHIVE_ATP_WALLET_PATH = "atpwallet";

    // Deprecated top-level archive subdirectory where the opss wallet is stored.
    public static final String OLD_ARCHIVE_OPSS_WALLET_PATH = "opsswallet";

    /**
     * The archive subdirectory name where all database wallets are stored.
     */
    public static final String DB_WALLETS_DIR_NAME = "dbWallets";

    /**
     * The archive subdirectory name used by default for the database wallet for the RCU database.
     */
    public static final String DEFAULT_RCU_WALLET_NAME = "rcu";

    /**
     * Top-level archive subdirectory where all database wallets are stored in subdirectories.
     */
    public static final String ARCHIVE_DB_WALLETS_DIR =
        String.format("%s/%s", WLSDPLY_ARCHIVE_BINARY_DIR, DB_WALLETS_DIR_NAME);

    /**
     * Default, top-level archive subdirectory where the database wallet for the RCU database is stored.
     */
    public static final String DEFAULT_RCU_WALLET_PATH = ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + DEFAULT_RCU_WALLET_NAME;

    /**
     * Top-level archive subdirectory where the opss wallet is stored.
     */
    public static final String ARCHIVE_OPSS_WALLET_PATH = WLSDPLY_ARCHIVE_BINARY_DIR + "/opsswallet";

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

    public enum ArchiveEntryType {
        STRUCTURED_APPLICATION,
        SHARED_LIBRARY,
        APPLICATION,
        APPLICATION_PLAN,
        SHLIB_PLAN,
        DOMAIN_LIB,
        DOMAIN_BIN,
        CLASSPATH_LIB,
        SCRIPT,
        SERVER_KEYSTORE,
        MIME_MAPPING,
        COHERENCE,
        JMS_FOREIGN_SERVER,
        COHERENCE_CONFIG,
        COHERENCE_PERSISTENCE_DIR,
        FILE_STORE,
        NODE_MANAGER_KEY_STORE,
        DB_WALLET,
        RCU_WALLET,
        OPSS_WALLET,
        CUSTOM
    }

    private enum FileOrDirectoryType {
        EITHER,
        FILE_ONLY,
        DIRECTORY_ONLY
    }

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

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                            public static utility methods                                  //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Determine if the specified path string is a valid archive location.
     *
     * @param path the path
     * @return true if the path is relative and starts with the expected directory name, false otherwise
     */
    public static boolean isPathIntoArchive(String path) {
        final String METHOD = "isPathIntoArchive";

        LOGGER.entering(CLASS, METHOD, path);
        boolean result = false;
        if (!StringUtils.isEmpty(path)) {
            result = path.startsWith(WLSDPLY_ARCHIVE_BINARY_DIR + ZIP_SEP)
                || path.startsWith(OLD_ARCHIVE_ATP_WALLET_PATH + ZIP_SEP)
                || path.startsWith(OLD_ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
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

    public static String getPathForType(ArchiveEntryType type) {
        final String METHOD = "getPathForType";
        LOGGER.entering(CLASS, METHOD, type);

        String pathPrefix = null;
        switch(type) {
            case APPLICATION:
            case APPLICATION_PLAN:
                pathPrefix = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP;
                break;

            case SHARED_LIBRARY:
            case SHLIB_PLAN:
                pathPrefix = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP;
                break;

            case STRUCTURED_APPLICATION:
                pathPrefix = ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP;
                break;

            case DOMAIN_LIB:
                pathPrefix = ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP;
                break;

            case DOMAIN_BIN:
                pathPrefix = ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP;
                break;

            case CLASSPATH_LIB:
                pathPrefix = ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP;
                break;

            case SCRIPT:
                pathPrefix = ARCHIVE_SCRIPTS_DIR + ZIP_SEP;
                break;

            case SERVER_KEYSTORE:
                pathPrefix = ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP;
                break;

            case MIME_MAPPING:
                pathPrefix = ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP;
                break;

            case COHERENCE:
            case COHERENCE_CONFIG:
            case COHERENCE_PERSISTENCE_DIR:
                pathPrefix = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP;
                break;

            case JMS_FOREIGN_SERVER:
                pathPrefix = ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP;
                break;

            case FILE_STORE:
                pathPrefix = ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP;
                break;

            case NODE_MANAGER_KEY_STORE:
                pathPrefix = ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP;
                break;

            case DB_WALLET:
                pathPrefix = ARCHIVE_DB_WALLETS_DIR + ZIP_SEP;
                break;

            case RCU_WALLET:
                pathPrefix = DEFAULT_RCU_WALLET_PATH + ZIP_SEP;
                break;

            case OPSS_WALLET:
                pathPrefix = ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP;
                break;

            case CUSTOM:
                pathPrefix = ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP;
                break;

            default:
                LOGGER.warning("WLSDPLY-01438", type.name());
                break;
        }

        LOGGER.exiting(CLASS, METHOD, pathPrefix);
        return pathPrefix;
    }

    public static String getPathForSegregationType(ArchiveEntryType type, String segregationName) {
        final String METHOD = "getPathForSegregationType";
        LOGGER.entering(CLASS, METHOD, type, segregationName);

        validateNonEmptyString(segregationName, "segregationName", METHOD);

        String pathPrefix = getPathForType(type);
        if (!StringUtils.isEmpty(pathPrefix)) {
            pathPrefix += segregationName + ZIP_SEP;
        }

        LOGGER.exiting(CLASS, METHOD, pathPrefix);
        return pathPrefix;
    }

    /**
      * Get archive path for the application name for use in the model.
      *
      * @param appPath name of the application
      * @return archive path for use in the model
      */
    public static String getApplicationArchivePath(String appPath) {
        return getArchiveName(ARCHIVE_APPS_TARGET_DIR, appPath);
    }

    /**
     * Get the archive path for the domain/bin scripts
     *
     * @param domainBinPath domain/bin
     * @return Archive path for domain/bin in the model
     */
    public static String getDomainBinScriptArchivePath(String domainBinPath) {
        return getArchiveName(ARCHIVE_DOM_BIN_TARGET_DIR, domainBinPath);
    }

    /**
     * Get the archive path for the application in a well-formed application directory
     *
     * @param appPath name of the application path
     * @return archive path for use in the model
     */
    public static String getApplicationDirectoryArchivePath(String appName, String appPath) {
        File zipAppPath = new File(appPath).getParentFile();
        File zipAppFile = new File(appPath);
        return ARCHIVE_STRUCT_APPS_TARGET_DIR + "/" + appName + "/" + zipAppPath.getName() + "/" + zipAppFile.getName();
    }

    /**
     * Get the archive path for the classpath library for use in the model.
     *
     * @param libPath to get the archive path for
     * @return Archive path for the classpath library for use in the model
     */
    public static String getClasspathArchivePath(String libPath) {
        return getArchiveName(ARCHIVE_CPLIB_TARGET_DIR, libPath);
    }

    /**
     * Get the archive path of the application deployment plan.
     *
     * @param planFile The deployment plan file name
     * @return Archive path for use in the model
     */
    public static String getApplicationPlanArchivePath(String planFile) {
        return getArchiveName(ARCHIVE_APPS_TARGET_DIR, planFile);
    }

    /**
     * Get the archive path of a well-formed plan directory in app directory,
     *
     * @param appName The application name of the app directory
     * @param planDir The deployment plan file directory
     * @return Archive path for use in the model
     */
    public static String getApplicationPlanDirArchivePath(String appName, String planDir) {
        File zipPath = new File(planDir);
        return ARCHIVE_STRUCT_APPS_TARGET_DIR + "/" + appName + "/" + zipPath.getName();
    }

    /**
     * Get the Archive Path for the Shared Library Plan
     *
     * @param planFile Shared Library Deployment Plan file name
     * @return Archive path for the plan file for use in the model
     */
    public static String getShlibPlanArchivePath(String planFile) {
        return getArchiveName(ARCHIVE_SHLIBS_TARGET_DIR, planFile);
    }

    /**
     * Get the archive path for the scriptfile name.
     *
     * @param scriptFile the script file to get the path name
     * @return The name of the file in the archive for use in the model
     */
    public static String getScriptArchivePath(String scriptFile) {
        return getArchiveName(ARCHIVE_SCRIPTS_DIR, scriptFile);
    }

    /**
     * Get the archive path for the servr identity key store file for use in the model
     *
     * @param serverName   name of the server used to separate paths
     * @param keystoreFile the file to get the archive path name
     * @return Archive path name for the server key store file
     */
    public static String getServerKeyStoreArchivePath(String serverName, String keystoreFile) {
        return getArchiveName(ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + serverName, keystoreFile);
    }

    /**
     * Get the archive path name for the WebAppContainer mime mapping file.
     *
     * @param mimeMappingFile the path name of the file to use
     * @return The archive path of the mimeMappingFile for the model
     */
    public static String getMimeMappingArchivePath(String mimeMappingFile) {
        return getArchiveName(ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP, mimeMappingFile);
    }

    /**
     * Get the Coherence configuration file name in the archive to use in the model.
     *
     * @param clusterName The Coherence cluster name used to segregate the directories
     * @param configFile  the file name of the config file
     * @return Archive name for use in the model
     */
    public static String getCoherenceConfigArchivePath(String clusterName, String configFile) {
        return getArchiveName(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, configFile);
    }

    /**
     * Get the archive name for the foreign server binding file.
     *
     * @param foreignServer The foreign server name used to segregate the directories
     * @param configFile    The file name to add
     * @return The location of the file in the archive to use in the model
     */
    public static String getForeignServerArchivePath(String foreignServer, String configFile) {
        return getArchiveName(ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServer, configFile);
    }

    public static String getCoherenceURLArchivePath(String clusterName, URL urlForConfigFile) {
        return getURLArchiveName(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, urlForConfigFile,
            true);
    }

    public static String getFileStoreArchivePath(String fileStoreName) {
        return getArchiveName(ARCHIVE_FILE_STORE_TARGET_DIR, fileStoreName);
    }

    /**
     * Get the name of the persistence directory as an archive path. This does not reconcile duplicates or other
     * items deeper in the zip file logic.
     *
     * @param clusterName   name of cluster specific to path
     * @param directoryType type of persistence directory
     * @return Archive style path for directory
     */
    public static String getCoherencePersistArchivePath(String clusterName, String directoryType) {
        return getArchiveName(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName, directoryType);
    }

    /**
     * Get the archive path to Node Manager Identity Key Store file. This does not reconcile duplicate names or
     * other items that the archive file does when adding to the archive.
     *
     * @param keystoreFile file name of the key store file
     * @return archive file path for the model
     */
    public static String getNodeManagerKeyStoreArchivePath(String keystoreFile) {
        return getArchiveName(ARCHIVE_NODE_MANAGER_TARGET_DIR, keystoreFile);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               public utility methods                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Get the current file name for the JCSLifecycleArchive file.
     *
     * @return the file name
     */
    public String getArchiveFileName() {
        return getZipFile().getFileName();
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

    public List<String> getArchiveEntries(ArchiveEntryType type) throws WLSDeployArchiveIOException {
        final String METHOD = "getArchiveEntries";
        LOGGER.entering(CLASS, METHOD, type);

        String pathPrefix = getPathForType(type);
        List<String> entries = getZipFile().listZipEntries(pathPrefix);

        LOGGER.exiting(CLASS, METHOD, entries);
        return entries;
    }

    public List<String> getArchiveEntries(ArchiveEntryType type, String name) throws WLSDeployArchiveIOException {
        final String METHOD = "getArchiveEntries";
        LOGGER.entering(CLASS, METHOD, type, name);

        String pathPrefix = getPathForType(type);
        FileOrDirectoryType allowedFileType = getFileType(type);
        List<String> entries = getZipListEntries(pathPrefix, name, allowedFileType);

        LOGGER.exiting(CLASS, METHOD, entries);
        return entries;
    }

    public List<String> getSegregatedArchiveEntries(ArchiveEntryType type, String segregationName)
        throws WLSDeployArchiveIOException {
        final String METHOD = "getSegregatedArchiveEntries";
        LOGGER.entering(CLASS, METHOD, type, segregationName);

        String pathPrefix = getPathForSegregationType(type, segregationName);
        List<String> entries = getZipFile().listZipEntries(pathPrefix);

        LOGGER.exiting(CLASS, METHOD, entries);
        return entries;
    }

    public List<String> getSegregatedArchiveEntries(ArchiveEntryType type, String segregationName, String name)
        throws WLSDeployArchiveIOException {
        final String METHOD = "getSegregatedArchiveEntries";
        LOGGER.entering(CLASS, METHOD, type, segregationName, name);

        String pathPrefix = getPathForSegregationType(type, segregationName);
        FileOrDirectoryType allowedFileType = getFileType(type);
        List<String> entries = getZipListEntries(pathPrefix, name, allowedFileType);

        LOGGER.exiting(CLASS, METHOD, entries);
        return entries;
    }

    /**
     * Determines whether the archive contains the specified file or directory.
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
     * Determines whether the provided path is a directory in the archive file.
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
     * Determines whether the provided path is a directory or a file in a directory
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
     * @param stripLeadingPathDirectories whether to strip the leading directories
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
     * Return the manifest for the specified path in the archive, if present.
     * The path may refer to a packaged EAR/JAR/WAR, or an exploded entry.
     *
     * @param sourcePath the path to be checked
     * @return the Manifest object, or null
     * @throws WLSDeployArchiveIOException if there is a problem reading the archive, or the manifest
     */
    public Manifest getManifest(String sourcePath) throws WLSDeployArchiveIOException {
        try {
            if (containsFile(sourcePath)) {
                // a jarred app or library in the archive.
                try (ZipInputStream zipStream = new ZipInputStream(getZipFile().getZipEntry(sourcePath))) {
                    // JarInputStream.getManifest() has problems if MANIFEST.MF is not the first entry,
                    // so use ZipInputStream and search for the specific entry.
                    ZipEntry zipEntry;
                    while ((zipEntry = zipStream.getNextEntry()) != null) {
                        if (JarFile.MANIFEST_NAME.equals(zipEntry.getName())) {
                            Manifest manifest = new Manifest(zipStream);
                            zipStream.closeEntry();
                            return manifest;
                        }
                        zipStream.closeEntry();
                    }
                }
            } else if (containsPath(sourcePath)) {
                // an exploded app or library in the archive.
                String manifestPath = sourcePath + "/" + JarFile.MANIFEST_NAME;
                if (containsFile(manifestPath)) {
                    try (InputStream inStream = getZipFile().getZipEntry(manifestPath)) {
                        return new Manifest(inStream);
                    }
                }
            }
        } catch (IOException e) {
            WLSDeployArchiveIOException aioe = new WLSDeployArchiveIOException("WLSDPLY-01426", sourcePath,
                getArchiveFileName(), e.getLocalizedMessage());
            LOGGER.throwing(aioe);
            throw aioe;
        }
        return null;
    }

    /**
     * Extract the entire contents of the archive file to the domain home.
     *
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an error occurs reading the archive or writing the files.
     * @throws IllegalArgumentException    if the domainHome directory does not exist
     */
    public void extractAll(File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractAll";
        LOGGER.entering(CLASS, METHOD, domainHome);

        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        extractDirectoryFromZip(WLSDPLY_ARCHIVE_BINARY_DIR + ZIP_SEP, domainHome);

        LOGGER.exiting(CLASS, METHOD);
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

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  application methods                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

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

    /**
     * Replace an existing application in the archive file.
     *
     * @param appPath  the app name or the path within the archive of the app to replace
     * @param sourceLocation the file system location of the new app to replace the existing one
     * @return the archive path of the new application
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceApplication(String appPath, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceApplication";
        LOGGER.entering(CLASS, METHOD, appPath, sourceLocation);

        String archivePath;
        if (appPath.startsWith(ARCHIVE_APPS_TARGET_DIR + ZIP_SEP)) {
            archivePath = appPath;
        } else {
            archivePath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + appPath;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addApplication(sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
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
     * Extract the named application from the archive to the domain home directory.
     *
     * @param appPath     the application path into the archive file
     * @param domainHome  the domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the appPath is empty
     */
    public void extractApplication(String appPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractApplication";
        LOGGER.entering(CLASS, METHOD, appPath);

        validateNonEmptyString(appPath, "appPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = appPath;
        if (!appPath.startsWith(ARCHIVE_APPS_TARGET_DIR)) {
            archivePath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + appPath;
        }

        archivePath = fixupPathForDirectories(archivePath);
        if (archivePath.endsWith(ZIP_SEP)) {
            extractDirectoryFromZip(archivePath, domainHome);
        } else {
            extractFileFromZip(archivePath, domainHome);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named application from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param appPath The application name (e.g., foo.ear) or the archive path
     *                to it (e.g., wlsdeploy/applications/foo.ear)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the app is not present or an IOException occurred while
     *                                      reading the archive or writing the file
     * @throws IllegalArgumentException     if the appPath is null or empty
     */
    public int removeApplication(String appPath) throws WLSDeployArchiveIOException {
        return removeApplication(appPath, false);
    }

    /**
     * Remove the named application from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param appPath The application name (e.g., foo.ear) or the archive path
     *                to it (e.g., wlsdeploy/applications/foo.ear)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the app is not present (and silent = false) or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the appPath is null or empty
     */
    public int removeApplication(String appPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeApplication";
        LOGGER.entering(CLASS, METHOD, appPath, silent);

        validateNonEmptyString(appPath, "appPath", METHOD);

        String archivePath;
        String appName;
        if (appPath.startsWith(ARCHIVE_APPS_TARGET_DIR + ZIP_SEP)) {
            archivePath = appPath;
            appName = getNameFromPath(archivePath, ARCHIVE_APPS_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + appPath;
            appName = appPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.APPLICATION, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01440", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.APPLICATION, ARCHIVE_APPS_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               application plan methods                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Adds an application's deployment plan file to the archive.
     *
     * @param planFile      the deployment plan file name
     * @param preferredName the preferred name of the file to add
     * @return the actual name of the file in the archive
     * @throws WLSDeployArchiveIOException if an error occurs adding the file
     * @throws IllegalArgumentException    if the file does not exist or the preferredName was empty or null
     */
    public String addApplicationDeploymentPlan(String planFile, String preferredName)
        throws WLSDeployArchiveIOException {
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
     * Replace an application deployment plan file in the archive.
     *
     * @param planPath       the application deployment plan name or path within the archive
     * @param sourceLocation the file system location of the new application deployment plan to replace the existing one
     * @return the archive path of the new application deployment plan
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceApplicationDeploymentPlan(String planPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceApplicationDeploymentPlan";
        LOGGER.entering(CLASS, METHOD, planPath, sourceLocation);

        String archivePath;
        String preferredName;
        if (planPath.startsWith(ARCHIVE_APPS_TARGET_DIR + ZIP_SEP)) {
            archivePath = planPath;
            preferredName = planPath.substring(planPath.lastIndexOf(ZIP_SEP) + 1);
        } else {
            archivePath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + planPath;
            preferredName = planPath;
        }

        getZipFile().removeZipEntry(archivePath);
        String newName = addApplicationDeploymentPlan(sourceLocation, preferredName);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extracts the named application deployment plan from the archive into the domain home directory,
     * preserving the archive directory structure.
     *
     * @param planPath    the name of the application deployment plan file in the archive.
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the planPath is empty
     */
    public void extractApplicationPlan(String planPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractApplicationPlan";
        LOGGER.entering(CLASS, METHOD, planPath);

        validateNonEmptyString(planPath, "planPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = planPath;
        if (!planPath.startsWith(ARCHIVE_APPS_TARGET_DIR)) {
            archivePath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + planPath;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named application deployment plan from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param planPath The application deployment plan name (e.g., foo.xml) or the archive path
     *                 to it (e.g., wlsdeploy/applications/foo.xml)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the app deployment plan is not present or an IOException occurred while
     *                                      reading the archive or writing the file
     * @throws IllegalArgumentException     if the planPath is null or empty
     */
    public int removeApplicationDeploymentPlan(String planPath) throws WLSDeployArchiveIOException {
        return removeApplicationDeploymentPlan(planPath, false);
    }

    /**
     * Remove the named application deployment plan from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param planPath The application deployment plan name (e.g., foo.xml) or the archive path
     *                 to it (e.g., wlsdeploy/applications/foo.xml)
     * @param silent   If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the app deployment plan is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the appPath is null or empty
     */
    public int removeApplicationDeploymentPlan(String planPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeApplicationDeploymentPlan";
        LOGGER.entering(CLASS, METHOD, planPath, silent);

        validateNonEmptyString(planPath, "planPath", METHOD);

        String archivePath;
        String planName;
        if (planPath.startsWith(ARCHIVE_APPS_TARGET_DIR + ZIP_SEP)) {
            archivePath = planPath;
            planName = getNameFromPath(archivePath, ARCHIVE_APPS_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_APPS_TARGET_DIR + ZIP_SEP + planPath;
            planName = planPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.APPLICATION_PLAN, planName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01441", planName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.APPLICATION_PLAN, ARCHIVE_APPS_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                            structured application methods                                 //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a structured application installation directory to the archive file.
     *
     * @param installRoot the path to the installation directory
     * @return the archive path of the new structured application installation directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the directory passed or its app subdirectory does not exist
     */
    public String addStructuredApplication(String installRoot) throws WLSDeployArchiveIOException {
        final String METHOD = "addApplicationFolder";
        LOGGER.entering(CLASS, METHOD, installRoot);

        File filePath = FileUtils.getCanonicalFile(installRoot);
        File appDir = new File(filePath, "app");
        validateExistingDirectory(filePath, "installRoot", getArchiveFileName(), METHOD);
        validateExistingDirectory(appDir, "appDir", getArchiveFileName(), METHOD);

        String newName = addItemToZip(ARCHIVE_STRUCT_APPS_TARGET_DIR, filePath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace an existing structured application installation directory in the archive file.
     *
     * @param appPath           the app name or the path within the archive of the structured application
     *                          installation directory to replace
     * @param sourceInstallRoot the file system location of the new structured application installation directory
     *                          to replace the existing one
     * @return the archive path of the new structured application installation directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the directory passed or its app subdirectory does not exist
     */
    public String replaceStructuredApplication(String appPath, String sourceInstallRoot)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceStructuredApplication";
        LOGGER.entering(CLASS, METHOD, appPath, sourceInstallRoot);

        String archivePath;
        if (appPath.startsWith(ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP)) {
            archivePath = appPath;
        } else {
            archivePath = ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP + appPath;
        }
        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addStructuredApplication(sourceInstallRoot);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extracts the named structured application installation directory from the archive into the domain home directory,
     * preserving the archive directory structure.
     *
     * @param appPath     the name of the application installation directory in the archive.
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the appPath is empty
     */
    public void extractStructuredApplication(String appPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractApplicationPlan";
        LOGGER.entering(CLASS, METHOD, appPath);

        validateNonEmptyString(appPath, "appPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = appPath;
        if (!appPath.startsWith(ARCHIVE_STRUCT_APPS_TARGET_DIR)) {
            archivePath = ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP + appPath;
        }
        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }

        extractDirectoryFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    // TODO - Need to verify that discovery produces an archive that is consistent with the add/replace methods above.
    //        Once verified, change method name to be consistent and add javadoc.
    public String addApplicationFolder(String appName, String appPath)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addApplicationFolder";
        LOGGER.entering(CLASS, METHOD, appName, appPath);
        File zipPath = new File(appPath);
        if (zipPath.getParentFile() != null) {
            zipPath = zipPath.getParentFile();
        }
        String firstPrefix = ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP + appName + ZIP_SEP + zipPath.getName();
        String newName = walkDownFolders(firstPrefix, zipPath);
        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    // TODO - Need to verify that discovery produces an archive that is consistent with the add/replace methods above.
    //        Once verified, change method name to be consistent and add javadoc.
    public String addApplicationPlanFolder(String appName, String planDir)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addApplicationPathFolder";
        LOGGER.entering(CLASS, METHOD, appName, planDir);
        File zipPlan = new File(planDir);
        String zipPrefix = ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP + appName + ZIP_SEP + zipPlan.getName();
        String newName = walkDownFolders(zipPrefix, zipPlan);

        LOGGER.exiting(CLASS, METHOD, newName);
        return zipPrefix;
    }

    /**
     * Remove the named structured application from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param appPath The structured application name (e.g., foo) or the archive path
     *                to it (e.g., wlsdeploy/structuredApplications/foo)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the structured app is not present or an IOException occurred while
     *                                      reading the archive or writing the file
     * @throws IllegalArgumentException     if the appPath is null or empty
     */
    public int removeStructuredApplication(String appPath) throws WLSDeployArchiveIOException {
        return removeStructuredApplication(appPath, false);
    }

    /**
     * Remove the named structured application from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param appPath The structured application name (e.g., foo) or the archive path
     *                to it (e.g., wlsdeploy/structuredApplications/foo)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the structured app is not present (and silent = false) or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the appPath is null or empty
     */
    public int removeStructuredApplication(String appPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeStructuredApplication";
        LOGGER.entering(CLASS, METHOD, appPath, silent);

        validateNonEmptyString(appPath, "appPath", METHOD);

        String archivePath;
        String appName;
        if (appPath.startsWith(ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP)) {
            archivePath = appPath;
            appName = getNameFromPath(archivePath, ARCHIVE_STRUCT_APPS_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP + appPath;
            appName = appPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.STRUCTURED_APPLICATION, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01442", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.STRUCTURED_APPLICATION,
            ARCHIVE_STRUCT_APPS_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                shared library methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Get the best guess of the name of the shared library as if it is in the archive file.
     * This does not reconcile duplicate names and other items that require the archive file
     * and is only used with discoverDomain -remote to give the user an archive path.
     *
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
        LOGGER.entering(CLASS, METHOD, shlibPath);

        File filePath = FileUtils.getCanonicalFile(shlibPath);
        validateExistingFile(filePath, "shlibPath", getArchiveFileName(), METHOD, true);

        String newName = addItemToZip(ARCHIVE_SHLIBS_TARGET_DIR, filePath);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace an existing application in the archive file.
     *
     * @param shlibPath      the shared library name or the path within the archive to replace
     * @param sourceLocation the file system location of the new shared library to replace the existing one
     * @return the archive path of the new shared library
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceSharedLibrary(String shlibPath, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceSharedLibrary";
        LOGGER.entering(CLASS, METHOD, shlibPath, sourceLocation);

        String archivePath;
        if (shlibPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP)) {
            archivePath = shlibPath;
        } else {
            archivePath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + shlibPath;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addSharedLibrary(sourceLocation);

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
     * Extracts the named shared library from the archive into the domain home directory,
     * preserving the archive directory structure.
     *
     * @param libPath     the name of the shared library file/directory in the archive
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the libPath is empty
     */
    public void extractSharedLibrary(String libPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractSharedLibrary";
        LOGGER.entering(CLASS, METHOD, libPath);

        validateNonEmptyString(libPath, "libPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = libPath;
        if (!libPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR)) {
            archivePath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + libPath;
        }

        archivePath = fixupPathForDirectories(archivePath);
        if (archivePath.endsWith(ZIP_SEP)) {
            extractDirectoryFromZip(archivePath, domainHome);
        } else {
            extractFileFromZip(archivePath, domainHome);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named shared library from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param libPath The shared library name (e.g., foo.war) or the archive path
     *                to it (e.g., wlsdeploy/sharedLibraries/foo.war)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the shared library is not present or an IOException occurred while
     *                                      reading the archive or writing the file
     * @throws IllegalArgumentException     if the libPath is null or empty
     */
    public int removeSharedLibrary(String libPath) throws WLSDeployArchiveIOException {
        return removeSharedLibrary(libPath, false);
    }

    /**
     * Remove the named shared library from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param libPath The shared library name (e.g., foo.war) or the archive path
     *                to it (e.g., wlsdeploy/sharedLibraries/foo.war)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the shared library is not present (and silent = false) or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the libPath is null or empty
     */
    public int removeSharedLibrary(String libPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeSharedLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, silent);

        validateNonEmptyString(libPath, "libPath", METHOD);

        String archivePath;
        String appName;
        if (libPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP)) {
            archivePath = libPath;
            appName = getNameFromPath(archivePath, ARCHIVE_SHLIBS_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + libPath;
            appName = libPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.SHARED_LIBRARY, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01443", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.SHARED_LIBRARY,ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              shared library plan methods                                  //
    ///////////////////////////////////////////////////////////////////////////////////////////////

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
     * Replace a shared library deployment plan file in the archive.
     *
     * @param planPath       the shared library deployment plan name or path within the archive
     * @param sourceLocation the file system location of the new shared library deployment plan
     *                       to replace the existing one
     * @return the archive path of the new shared library deployment plan
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceSharedLibraryDeploymentPlan(String planPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceSharedLibraryDeploymentPlan";
        LOGGER.entering(CLASS, METHOD, planPath, sourceLocation);

        String archivePath;
        String preferredName;
        if (planPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP)) {
            archivePath = planPath;
            preferredName = planPath.substring(planPath.lastIndexOf(ZIP_SEP) + 1);
        } else {
            archivePath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + planPath;
            preferredName = planPath;
        }

        getZipFile().removeZipEntry(archivePath);
        String newName = addSharedLibraryDeploymentPlan(sourceLocation, preferredName);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extracts the named shared library deployment plan from the archive into the domain home directory,
     * preserving the archive directory structure.
     *
     * @param planPath    the name of the shared library deployment plan file in the archive.
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the planPath is empty
     */
    public void extractSharedLibraryPlan(String planPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractSharedLibraryPlan";
        LOGGER.entering(CLASS, METHOD, planPath);

        validateNonEmptyString(planPath, "planPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = planPath;
        if (!planPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR)) {
            archivePath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + planPath;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named shared library deployment plan from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param planPath The shared library deployment plan name (e.g., foo.xml) or the archive path
     *                 to it (e.g., wlsdeploy/sharedLibraries/foo.xml)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the shared library deployment plan is not present or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the planPath is null or empty
     */
    public int removeSharedLibraryDeploymentPlan(String planPath) throws WLSDeployArchiveIOException {
        return removeSharedLibraryDeploymentPlan(planPath, false);
    }

    /**
     * Remove the named shared library deployment plan from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param planPath The shared library deployment plan name (e.g., foo.xml) or the archive path
     *                 to it (e.g., wlsdeploy/sharedLibraries/foo.xml)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the shared library deployment plan is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the planPath is null or empty
     */
    public int removeSharedLibraryDeploymentPlan(String planPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeSharedLibraryDeploymentPlan";
        LOGGER.entering(CLASS, METHOD, planPath, silent);

        validateNonEmptyString(planPath, "planPath", METHOD);

        String archivePath;
        String appName;
        if (planPath.startsWith(ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP)) {
            archivePath = planPath;
            appName = getNameFromPath(archivePath, ARCHIVE_SHLIBS_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP + planPath;
            appName = planPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.SHLIB_PLAN, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01444", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.SHLIB_PLAN,ARCHIVE_SHLIBS_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                domain library methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Get the archive file name for the Domain library file. This does not reconcile duplicate names or other
     * items that require the archive file.
     *
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
     * @param domainLibPath - File name representing the actual path of the archive or directory in
     *                        the local or remote file system
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
     * Replace a $DOMAIN_HOME/lib library in the archive.
     *
     * @param domainLibPath  the $DOMAIN_HOME/lib library name or the path within the archive to replace
     * @param sourceLocation the file system location of the new $DOMAIN_HOME/lib library to replace the existing one
     * @return the archive path of the new $DOMAIN_HOME/lib library
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceDomainLibLibrary(String domainLibPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceDomainLibLibrary";
        LOGGER.entering(CLASS, METHOD, domainLibPath, sourceLocation);

        String archivePath;
        if (domainLibPath.startsWith(ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP)) {
            archivePath = domainLibPath;
        } else {
            archivePath = ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP + domainLibPath;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addDomainLibLibrary(sourceLocation);

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
     * @param libPath           the name of the $DOMAIN_HOME/lib library within the archive
     * @param extractToLocation the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the extractToLocation directory does not exist or the libPath is empty
     */
    public void extractDomainLibLibrary(String libPath, File extractToLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "extractDomainLibLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, extractToLocation);

        extractDomainLibLibrary(libPath, extractToLocation, false);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Extract the named $DOMAIN_HOME/lib library to the domain home location.
     *
     * @param libPath                         the name of the $DOMAIN_HOME/lib library within the archive
     * @param domainHome                      the existing directory location to write the file
     * @param preserveIntermediateDirectories if true, file is extracted with intermediate directory structure
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the libPath is empty
     */
    public void extractDomainLibLibrary(String libPath, File domainHome, boolean preserveIntermediateDirectories)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractDomainLibLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, domainHome, preserveIntermediateDirectories);

        validateNonEmptyString(libPath, "libPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        if (preserveIntermediateDirectories) {
            String archivePath = libPath;
            if (!libPath.startsWith(ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP)) {
                archivePath = ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP + libPath;
            }

            extractFileFromZip(archivePath, domainHome);
        } else {
            extractFileFromZip(libPath, ARCHIVE_DOMLIB_TARGET_DIR, "", domainHome);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named domain library from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param libPath The domain library name (e.g., foo.jar) or the archive path
     *                to it (e.g., wlsdeploy/domainLibraries/foo.jar)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the domain library is not present or an IOException occurred while
     *                                      reading the archive or writing the file
     * @throws IllegalArgumentException     if the libPath is null or empty
     */
    public int removeDomainLibLibrary(String libPath) throws WLSDeployArchiveIOException {
        return removeDomainLibLibrary(libPath, false);
    }

    /**
     * Remove the named domain library from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param libPath The domain library name (e.g., foo.jar) or the archive path
     *                to it (e.g., wlsdeploy/domainLibraries/foo.jar)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the domain library is not present (and silent = false) or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the libPath is null or empty
     */
    public int removeDomainLibLibrary(String libPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeDomainLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, silent);

        validateNonEmptyString(libPath, "libPath", METHOD);

        String archivePath;
        String appName;
        if (libPath.startsWith(ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP)) {
            archivePath = libPath;
            appName = getNameFromPath(archivePath, ARCHIVE_DOMLIB_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP + libPath;
            appName = libPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.DOMAIN_LIB, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01445", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.DOMAIN_LIB,ARCHIVE_DOMLIB_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 classpath lib methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

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
     * Replace a classpath library in the archive.
     *
     * @param libPath        the classpath library name or the path within the archive to replace
     * @param sourceLocation the file system location of the new classpath library to replace the existing one
     * @return the archive path of the new classpath library
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceClasspathLibrary(String libPath, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceClasspathLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, sourceLocation);

        String archivePath;
        if (libPath.startsWith(ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP)) {
            archivePath = libPath;
        } else {
            archivePath = ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP + libPath;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addClasspathLibrary(sourceLocation);

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
     * Extract the named classpath library from the archive into the domain home directory,
     * preserving the archive directory structure.
     *
     * @param libPath     the name of the classpath library file/directory in the archive.
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the libPath is empty
     */
    public void extractClasspathLibrary(String libPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractClasspathLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, domainHome);

        validateNonEmptyString(libPath, "libPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = libPath;
        if (!libPath.startsWith(ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP + libPath;
        }
        archivePath = fixupPathForDirectories(archivePath);

        if (archivePath.endsWith(ZIP_SEP)) {
            extractDirectoryFromZip(archivePath, domainHome);
        } else {
            extractFileFromZip(archivePath, domainHome);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named classpath library from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param libPath The classpath library name (e.g., foo.jar) or the archive path
     *                to it (e.g., wlsdeploy/classpathLibraries/foo.jar)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the classpath library is not present or an IOException occurred while
     *                                      reading the archive or writing the file
     * @throws IllegalArgumentException     if the libPath is null or empty
     */
    public int removeClasspathLibrary(String libPath) throws WLSDeployArchiveIOException {
        return removeClasspathLibrary(libPath, false);
    }

    /**
     * Remove the named classpath library from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param libPath The classpath library name (e.g., foo.jar) or the archive path
     *                to it (e.g., wlsdeploy/classpathLibraries/foo.jar)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the classpath library is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the libPath is null or empty
     */
    public int removeClasspathLibrary(String libPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeClasspathLibrary";
        LOGGER.entering(CLASS, METHOD, libPath, silent);

        validateNonEmptyString(libPath, "libPath", METHOD);

        String archivePath;
        String appName;
        if (libPath.startsWith(ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP)) {
            archivePath = libPath;
            appName = getNameFromPath(archivePath, ARCHIVE_CPLIB_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP + libPath;
            appName = libPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.CLASSPATH_LIB, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01446", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.CLASSPATH_LIB,ARCHIVE_CPLIB_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  domain bin methods                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

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
     * Replace a $DOMAIN_HOME/bin script in the archive.
     *
     * @param domainBinPath  the $DOMAIN_HOME/bin script name or the path within the archive to replace
     * @param sourceLocation the file system location of the new $DOMAIN_HOME/bin script to replace the existing one
     * @return the archive path of the new $DOMAIN_HOME/bin script
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceDomainBinScript(String domainBinPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceDomainBinScript";
        LOGGER.entering(CLASS, METHOD, domainBinPath, sourceLocation);

        String archivePath;
        if (domainBinPath.startsWith(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP)) {
            archivePath = domainBinPath;
        } else {
            archivePath = ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP + domainBinPath;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addDomainBinScript(sourceLocation);

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
     * @param scriptPath                      the name of the $DOMAIN_HOME/bin script within the archive
     * @param extractToLocation               the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the extractToLocation directory does not exist or the scriptPath is empty
     */
    public void extractDomainBinScript(String scriptPath, File extractToLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "extractDomainBinScript";
        LOGGER.entering(CLASS, METHOD, scriptPath, extractToLocation);

        extractDomainBinScript(scriptPath, extractToLocation, false);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Extract the named $DOMAIN_HOME/bin script to the domain home location.
     *
     * @param scriptPath                      the name of the $DOMAIN_HOME/bin script within the archive
     * @param domainHome                      the existing directory location to write the file
     * @param preserveIntermediateDirectories if true, file is extracted with intermediate directory structure
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the scriptPath is empty
     */
    public void extractDomainBinScript(String scriptPath, File domainHome, boolean preserveIntermediateDirectories)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractDomainBinScript";
        LOGGER.entering(CLASS, METHOD, scriptPath, domainHome, preserveIntermediateDirectories);

        validateNonEmptyString(scriptPath, "scriptPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        if (preserveIntermediateDirectories) {
            String archivePath = scriptPath;
            if (!scriptPath.startsWith(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP)) {
                archivePath = ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP + scriptPath;
            }

            extractFileFromZip(archivePath, domainHome);
        } else {
            extractFileFromZip(scriptPath, ARCHIVE_DOM_BIN_TARGET_DIR, "", domainHome);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    public void removeDomainBinScripts() throws WLSDeployArchiveIOException {
        final String METHOD = "removeDomainBinScripts";

        LOGGER.entering(CLASS, METHOD);
        getZipFile().removeZipEntries(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named $DOMAIN_HOME/bin script from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param scriptPath The $DOMAIN_HOME/bin script name (e.g., foo.sh) or the archive path
     *                   to it (e.g., wlsdeploy/domainBin/foo.sh)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the $DOMAIN_HOME/bin script is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the scriptPath is null or empty
     */
    public int removeDomainBinScript(String scriptPath) throws WLSDeployArchiveIOException {
        return removeDomainBinScript(scriptPath, false);
    }

    /**
     * Remove the named $DOMAIN_HOME/bin script from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param scriptPath The $DOMAIN_HOME/bin script name (e.g., foo.sh) or the archive path
     *                   to it (e.g., wlsdeploy/domainBin/foo.sh)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the $DOMAIN_HOME/bin script is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the scriptPath is null or empty
     */
    public int removeDomainBinScript(String scriptPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeDomainBinScript";
        LOGGER.entering(CLASS, METHOD, scriptPath, silent);

        validateNonEmptyString(scriptPath, "scriptPath", METHOD);

        String archivePath;
        String appName;
        if (scriptPath.startsWith(ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP)) {
            archivePath = scriptPath;
            appName = getNameFromPath(archivePath, ARCHIVE_DOM_BIN_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP + scriptPath;
            appName = scriptPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.DOMAIN_BIN, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01447", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.DOMAIN_BIN,ARCHIVE_DOM_BIN_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    custom methods                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a custom file or directory to the archive.
     *
     * @param customEntryPath the file system path to the custom file/directory to add
     * @param relativePath    the relative archive path name to prepend to the file or directory being added, if any
     * @return the relative path where the custom file/directory is stored within the archive
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String addCustomEntry(String customEntryPath, String relativePath) throws WLSDeployArchiveIOException {
        final String METHOD = "addCustomEntry";
        LOGGER.entering(CLASS, METHOD, customEntryPath, relativePath);

        File filePath = new File(customEntryPath);
        validateExistingFile(filePath, "customEntryPath", getArchiveFileName(), METHOD, true);

        String newName = addItemToZip(getCustomArchivePath(relativePath), filePath);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace a custom file/directory in the archive.
     *
     * @param customEntryPath the custom file/directory name or the path within the archive to replace
     * @param sourceLocation  the file system location of the new custom file/directory to replace the existing one
     * @return the archive path of the new custom file/directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceCustomEntry(String customEntryPath, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceCustomEntry";
        LOGGER.entering(CLASS, METHOD, customEntryPath, sourceLocation);

        String archivePath;
        if (customEntryPath.startsWith(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP)) {
            archivePath = customEntryPath;
        } else {
            archivePath = ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP + customEntryPath;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addCustomEntry(sourceLocation, getCustomArchivePathForReplace(customEntryPath));

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
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
     * Extract the named custom file/directory from the archive into the domain home directory,
     * preserving the archive directory structure.
     *
     * @param entryPath   the name of the custom file/directory in the archive.
     * @param domainHome  the existing domain home directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the entryPath is empty
     */
    public void extractCustomEntry(String entryPath, File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractCustomEntry";
        LOGGER.entering(CLASS, METHOD, entryPath, domainHome);

        validateNonEmptyString(entryPath, "entryPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = entryPath;
        if (!entryPath.startsWith(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP + entryPath;
        }
        archivePath = fixupPathForDirectories(archivePath);

        if (archivePath.endsWith(ZIP_SEP)) {
            extractDirectoryFromZip(archivePath, domainHome);
        } else {
            extractFileFromZip(archivePath, domainHome);
        }

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named custom file/directory from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param entryPath The custom file/directory name (e.g., mydir/foo.properties) or the archive path
     *                  to it (e.g., wlsdeploy/custom/mydir/foo.properties)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the custom file/directory is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the entryPath is null or empty
     */
    public int removeCustomEntry(String entryPath) throws WLSDeployArchiveIOException {
        return removeCustomEntry(entryPath, false);
    }

    /**
     * Remove the named custom file/directory from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param entryPath The custom file/directory name (e.g., mydir/foo.properties) or the archive path
     *                  to it (e.g., wlsdeploy/custom/mydir/foo.properties)
     * @param silent    If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the custom file/directory is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the entryPath is null or empty
     */
    @SuppressWarnings("java:S2259")
    public int removeCustomEntry(String entryPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeCustomEntry";
        LOGGER.entering(CLASS, METHOD, entryPath, silent);

        validateNonEmptyString(entryPath, "entryPath", METHOD);

        String archivePath;
        String appName;
        if (entryPath.startsWith(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP)) {
            archivePath = entryPath;
            appName = getNameFromPath(archivePath, ARCHIVE_CUSTOM_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP + entryPath;
            appName = entryPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.CUSTOM, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01448", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = 0;
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
            result++;
        }

        String parentDir = getCustomArchivePathParentDir(appName);
        if (!StringUtils.isEmpty(parentDir)) {
            // Suppressing Sonar false positive...
            result += removeEmptyDirs(parentDir);
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   scripts methods                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

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
     * Replace a script file in the archive.
     *
     * @param scriptPath     the script name or the path within the archive to replace
     * @param sourceLocation the file system location of the new script file to replace the existing one
     * @return the archive path of the new script file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceScript(String scriptPath, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceScript";
        LOGGER.entering(CLASS, METHOD, scriptPath, sourceLocation);

        String archivePath;
        if (scriptPath.startsWith(ARCHIVE_SCRIPTS_DIR + ZIP_SEP)) {
            archivePath = scriptPath;
        } else {
            archivePath = ARCHIVE_SCRIPTS_DIR + ZIP_SEP + scriptPath;
        }

        getZipFile().removeZipEntry(archivePath);
        String newName = addScript(sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named script to the domain home location.
     *
     * @param scriptPath                      the name of the script within the archive
     * @param domainHome                      the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the scriptPath is empty
     */
    public void extractScript(String scriptPath, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractScript";
        LOGGER.entering(CLASS, METHOD, scriptPath, domainHome);

        validateNonEmptyString(scriptPath, "scriptPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = scriptPath;
        if (!scriptPath.startsWith(ARCHIVE_SCRIPTS_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_SCRIPTS_DIR + ZIP_SEP + scriptPath;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named script from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param scriptPath The script name (e.g., foo.sh) or the archive path
     *                   to it (e.g., wlsdeploy/scripts/foo.sh)
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the script is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the scriptPath is null or empty
     */
    public int removeScript(String scriptPath) throws WLSDeployArchiveIOException {
        return removeScript(scriptPath, false);
    }

    /**
     * Remove the named script from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param scriptPath The script name (e.g., foo.sh) or the archive path
     *                   to it (e.g., wlsdeploy/scripts/foo.sh)
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the script is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the scriptPath is null or empty
     */
    public int removeScript(String scriptPath, boolean silent) throws WLSDeployArchiveIOException {
        final String METHOD = "removeScript";
        LOGGER.entering(CLASS, METHOD, scriptPath, silent);

        validateNonEmptyString(scriptPath, "scriptPath", METHOD);

        String archivePath;
        String appName;
        if (scriptPath.startsWith(ARCHIVE_SCRIPTS_DIR + ZIP_SEP)) {
            archivePath = scriptPath;
            appName = getNameFromPath(archivePath, ARCHIVE_SCRIPTS_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_SCRIPTS_DIR + ZIP_SEP + scriptPath;
            appName = scriptPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.SCRIPT, appName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01449", appName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.SCRIPT,ARCHIVE_SCRIPTS_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              server keystore methods                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a Server keystore file to the server's directory in the archive.
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
     * Replace a Server keystore in the archive.
     *
     * @param serverName      the server name used to segregate directories, or null if the keystorePath
     *                        is includes the server name already (e.g., myserver/keystore.jks or
     *                        wlsdeploy/servers/myserver/keystore.jks)
     * @param keystorePath    the keystore name (e.g., keystore.jks) or an archive path
     *                        (e.g., myserver/keystore.jks or wlsdeploy/servers/myserver/keystore.jks)
     * @param sourceLocation  the file system location of the new keystore file to replace the existing one
     * @return the archive path of the new server keystore file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceServerKeyStoreFile(String serverName, String keystorePath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceServerKeyStoreFile";
        LOGGER.entering(CLASS, METHOD, serverName, keystorePath, sourceLocation);

        String archivePath = null;
        String computedServerName = serverName;
        if (keystorePath.startsWith(ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP)) {
            archivePath = keystorePath;
            computedServerName = getSegregationNameFromSegregatedArchivePath(serverName, keystorePath);
        } else if (!StringUtils.isEmpty(serverName)) {
            if (keystorePath.startsWith(serverName + ZIP_SEP)) {
                archivePath = ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + keystorePath;
            } else {
                archivePath = ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + serverName + ZIP_SEP + keystorePath;
            }
        }

        if (StringUtils.isEmpty(computedServerName)) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01434", keystorePath, sourceLocation);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        // If we get here, archivePath should never be null!
        //
        getZipFile().removeZipEntry(archivePath);
        String newName = addServerKeyStoreFile(computedServerName, sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named server's keystore file to the domain home location.
     *
     * @param serverName                   the name of the server used to segregate the keystore
     * @param keystoreName                 the name of the keystore file
     * @param domainHome                   the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or
     *                                     the serverName or keystoreName is empty
     */
    public void extractServerKeystore(String serverName, String keystoreName, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractServerKeystore";
        LOGGER.entering(CLASS, METHOD, serverName, keystoreName, domainHome);

        validateNonEmptyString(serverName, "serverName", METHOD);
        validateNonEmptyString(keystoreName, "keystoreName", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath;
        if (keystoreName.startsWith(ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP)) {
            archivePath = keystoreName;
        } else if (keystoreName.startsWith(serverName + ZIP_SEP)) {
            archivePath = ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + keystoreName;
        } else {
            archivePath = ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + serverName + ZIP_SEP + keystoreName;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named server's keystore file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param serverName    the name of the server used to segregate the keystore
     * @param keystoreName  the name of the keystore file
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the server's keystore file is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the serverName or keystoreName is null or empty
     */
    public int removeServerKeystore(String serverName, String keystoreName) throws WLSDeployArchiveIOException {
        return removeServerKeystore(serverName, keystoreName, false);
    }

    /**
     * Remove the named server's keystore file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param serverName    the name of the server used to segregate the keystore
     * @param keystoreName  the name of the keystore file
     * @param silent  If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the server's keystore file is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the serverName or keystoreName is null or empty
     */
    public int removeServerKeystore(String serverName, String keystoreName, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeServerKeystore";
        LOGGER.entering(CLASS, METHOD, serverName, keystoreName, silent);

        validateNonEmptyString(serverName, "serverName", METHOD);
        validateNonEmptyString(keystoreName, "keystoreName", METHOD);

        String parentDir = ARCHIVE_SERVER_TARGET_DIR + ZIP_SEP + serverName;
        String archivePath = parentDir + ZIP_SEP + keystoreName;

        List<String> zipEntries =
            getSegregatedArchiveEntries(ArchiveEntryType.SERVER_KEYSTORE, serverName, keystoreName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01450", serverName, keystoreName,
                getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyDirs(parentDir);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                           node manager keystore methods                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a Node Manager keystore file to the node manager directory in the archive.
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
     * Replace a Node Manager keystore file in the archive.
     *
     * @param keystorePath   the keystore name or the path within the archive to replace
     * @param sourceLocation the file system location of the new keystore file to replace the existing one
     * @return the archive path of the new node manager keystore file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceNodeManagerKeyStoreFile(String keystorePath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceNodeManagerKeyStoreFile";
        LOGGER.entering(CLASS, METHOD, keystorePath, sourceLocation);

        String archivePath;
        if (keystorePath.startsWith(ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP)) {
            archivePath = keystorePath;
        } else {
            archivePath = ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP + keystorePath;
        }

        getZipFile().removeZipEntry(archivePath);
        String newName = addNodeManagerKeyStoreFile(sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named node manager keystore file to the domain home location.
     *
     * @param keystoreName                 the name of the keystore file
     * @param domainHome                   the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the keystoreName is empty
     */
    public void extractNodeManagerKeystore(String keystoreName, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractNodeManagerKeystore";
        LOGGER.entering(CLASS, METHOD, keystoreName, domainHome);

        validateNonEmptyString(keystoreName, "keystoreName", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = keystoreName;
        if (!keystoreName.startsWith(ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP + keystoreName;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named node manager's keystore file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param keystoreName  the name of the keystore file
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the server's keystore file is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the keystoreName is null or empty
     */
    public int removeNodeManagerKeystore(String keystoreName) throws WLSDeployArchiveIOException {
        return removeNodeManagerKeystore(keystoreName, false);
    }

    /**
     * Remove the named node manager's keystore file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param keystorePath  the name of the keystore file
     * @param silent        If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the server's keystore file is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the keystorePath is null or empty
     */
    public int removeNodeManagerKeystore(String keystorePath, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeNodeManagerKeystore";
        LOGGER.entering(CLASS, METHOD, keystorePath, silent);

        validateNonEmptyString(keystorePath, "keystorePath", METHOD);

        String archivePath;
        String keystoreName;
        if (keystorePath.startsWith(ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP)) {
            archivePath = keystorePath;
            keystoreName = getNameFromPath(keystorePath, ARCHIVE_NODE_MANAGER_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP + keystorePath;
            keystoreName = keystorePath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.NODE_MANAGER_KEY_STORE, keystoreName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01451", keystorePath,
                getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.NODE_MANAGER_KEY_STORE,
            ARCHIVE_NODE_MANAGER_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                           MIME mapping keystore methods                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a WebAppContainer MIME mapping file to the archive.
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
     * Replace a WebAppContainer MIME mapping file in the archive.
     *
     * @param mimeMappingPath the MIME mapping name or the path within the archive to replace
     * @param sourceLocation  the file system location of the new MIME mapping file to replace the existing one
     * @return the archive path of the new MIME mapping file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceMimeMappingFile(String mimeMappingPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceMimeMappingFile";
        LOGGER.entering(CLASS, METHOD, mimeMappingPath, sourceLocation);

        String archivePath;
        if (mimeMappingPath.startsWith(ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP)) {
            archivePath = mimeMappingPath;
        } else {
            archivePath = ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP + mimeMappingPath;
        }

        getZipFile().removeZipEntry(archivePath);
        String newName = addMimeMappingFile(sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named MIME mapping file to the domain home location.
     *
     * @param mappingPath                  the name of the MIME mapping file
     * @param domainHome                   the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the mappingPath is empty
     */
    public void extractMimeMappingFile(String mappingPath, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractMimeMappingFile";
        LOGGER.entering(CLASS, METHOD, mappingPath, domainHome);

        validateNonEmptyString(mappingPath, "mappingPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = mappingPath;
        if (!mappingPath.startsWith(ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP + mappingPath;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named MIME mapping file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param mimeMappingPath  the name of the MIME mapping file
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the MIME mapping file is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the mimeMappingPath is null or empty
     */
    public int removeMimeMappingFile(String mimeMappingPath) throws WLSDeployArchiveIOException {
        return removeMimeMappingFile(mimeMappingPath, false);
    }

    /**
     * Remove the named MIME mapping file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param mimeMappingPath  the name of the MIME mapping file
     * @param silent           If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the MIME mapping file is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the mimeMappingPath is null or empty
     */
    public int removeMimeMappingFile(String mimeMappingPath, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeMimeMappingFile";
        LOGGER.entering(CLASS, METHOD, mimeMappingPath, silent);

        validateNonEmptyString(mimeMappingPath, "mimeMappingPath", METHOD);

        String archivePath;
        String keystoreName;
        if (mimeMappingPath.startsWith(ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP)) {
            archivePath = mimeMappingPath;
            keystoreName = getNameFromPath(mimeMappingPath, ARCHIVE_CONFIG_TARGET_DIR.length() + 2);
        } else {
            archivePath = ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP + mimeMappingPath;
            keystoreName = mimeMappingPath;
        }

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.MIME_MAPPING, keystoreName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01452", mimeMappingPath,
                getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.MIME_MAPPING,
            ARCHIVE_CONFIG_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                           Coherence config file methods                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

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
     * Replace a Coherence configuration file in the archive.
     *
     * @param clusterName     the Coherence cluster name used to segregate directories, or null if the configPath
     *                        is includes the cluster name already (e.g., mycluster/coherence-cache-config.xml or
     *                        wlsdeploy/coherence/mycluster/coherence-cache-config.xml)
     * @param configPath      the Coherence config name (e.g., coherence-cache-config.xml) or an archive path
     *                        (e.g., mycluster/coherence-cache-config.xml or
     *                        wlsdeploy/coherence/mycluster/coherence-cache-config.xml)
     * @param sourceLocation  the file system location of the new Coherence config file to replace the existing one
     * @return the archive path of the new Coherence config file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceCoherenceConfigFile(String clusterName, String configPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceCoherenceConfigFile";
        LOGGER.entering(CLASS, METHOD, clusterName, configPath, sourceLocation);

        String archivePath = null;
        String computedClusterName = clusterName;
        if (configPath.startsWith(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP)) {
            archivePath = configPath;
            computedClusterName = getSegregationNameFromSegregatedArchivePath(clusterName, configPath);
        } else if (!StringUtils.isEmpty(clusterName)) {
            if (configPath.startsWith(clusterName + ZIP_SEP)) {
                archivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + configPath;
            } else {
                archivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName + ZIP_SEP + configPath;
            }
        }

        if (StringUtils.isEmpty(computedClusterName)) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01435", configPath, sourceLocation);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        // If we get here, archivePath should never be null!
        //
        getZipFile().removeZipEntry(archivePath);
        String newName = addCoherenceConfigFile(computedClusterName, sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
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
     * Extract the named Coherence cluster's config file to the domain home location.
     *
     * @param clusterName                  the name of the server used to segregate the keystore
     * @param configPath                   the name of the keystore file
     * @param domainHome                   the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or
     *                                     the clusterName or configPath is empty
     */
    public void extractCoherenceConfigFile(String clusterName, String configPath, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractCoherenceConfigFile";
        LOGGER.entering(CLASS, METHOD, clusterName, configPath, domainHome);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(configPath, "configPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath;
        if (configPath.startsWith(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP)) {
            archivePath = configPath;
        } else if (configPath.startsWith(clusterName + ZIP_SEP)) {
            archivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + configPath;
        } else {
            archivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName + ZIP_SEP + configPath;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named Coherence config file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param clusterName     the name of the Coherence cluster used for segregating the config files
     * @param configFileName  the name of the Coherence config file
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the config file is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the clusterName or configFileName is null or empty
     */
    public int removeCoherenceConfigFile(String clusterName, String configFileName) throws WLSDeployArchiveIOException {
        return removeCoherenceConfigFile(clusterName, configFileName, false);
    }

    /**
     * Remove the named Coherence config file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param clusterName     the name of the Coherence cluster used for segregating the config files
     * @param configFileName  the name of the Coherence config file
     * @param silent          If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the config file is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the clusterName or configFileName is null or empty
     */
    public int removeCoherenceConfigFile(String clusterName, String configFileName, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeCoherenceConfigFile";
        LOGGER.entering(CLASS, METHOD, clusterName, configFileName, silent);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(configFileName, "configFileName", METHOD);

        String parentDir = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName;
        String archivePath = parentDir + ZIP_SEP + configFileName;

        List<String> zipEntries =
            getSegregatedArchiveEntries(ArchiveEntryType.COHERENCE_CONFIG, clusterName, configFileName);
        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01453", clusterName,
                configFileName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyDirs(parentDir);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                    Coherence persistence directory file methods                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add an empty directory to the archive file for the coherence cluster using the persistence directory type value.
     * The directory type is stored under the unique coherence cluster name.
     *
     * @param clusterName   name of the coherence cluster to which the persistence directory belongs
     * @param directoryType type of the coherence cluster persistence directory
     * @return unique directory name
     * @throws WLSDeployArchiveIOException unexpected exception adding the directory name to the archive file
     * @throws IllegalArgumentException    if the clusterName or directoryType is empty or null
     */
    public String addCoherencePersistenceDirectory(String clusterName, String directoryType)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addCoherencePersistenceDirectory";
        LOGGER.entering(CLASS, METHOD, clusterName, directoryType);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(directoryType, "directoryType", METHOD);

        String newName = addEmptyDirectoryToZip(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName,
            directoryType);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace an empty directory to the archive file for the coherence cluster using the persistence
     * directory type value.
     *
     * @param clusterName   name of the coherence cluster to which the persistence directory belongs
     * @param directoryType type of the coherence cluster persistence directory
     * @return the archive path to the new directory
     * @throws WLSDeployArchiveIOException unexpected exception adding the directory name to the archive file
     * @throws IllegalArgumentException    if the clusterName or directoryType is empty or null
     */
    public String replaceCoherencePersistenceDirectory(String clusterName, String directoryType)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceCoherencePersistenceDirectory";
        LOGGER.entering(CLASS, METHOD, clusterName, directoryType);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(directoryType, "directoryType", METHOD);

        String clusterArchivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName;
        getZipFile().removeZipEntries(clusterArchivePath + ZIP_SEP + directoryType + ZIP_SEP);
        String newName = addEmptyDirectoryToZip(clusterArchivePath, directoryType);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named Coherence cluster's persistence directory to the domain home location.
     *
     * @param clusterName                  the name of the Coherence cluster used to segregate the keystore
     * @param directoryType                the name of the persistence directory
     * @param domainHome                   the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or
     *                                     the clusterName or directoryType is empty
     */
    public void extractCoherencePersistenceDirectory(String clusterName, String directoryType, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractCoherencePersistenceDirectory";
        LOGGER.entering(CLASS, METHOD, clusterName, directoryType, domainHome);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(directoryType, "directoryType", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath;
        if (directoryType.startsWith(ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP)) {
            archivePath = directoryType;
        } else if (directoryType.startsWith(clusterName + ZIP_SEP)) {
            archivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + directoryType;
        } else {
            archivePath = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName + ZIP_SEP + directoryType;
        }

        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }

        extractDirectoryFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named Coherence persistence directory from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param clusterName           the name of the Coherence cluster used for segregating the persistence directories
     * @param persistenceDirectory  the name of the Coherence persistence directory
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the Coherence persistence directory is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the clusterName or persistenceDirectory is null or empty
     */
    public int removeCoherencePersistenceDirectory(String clusterName, String persistenceDirectory)
        throws WLSDeployArchiveIOException {
        return removeCoherencePersistenceDirectory(clusterName, persistenceDirectory, false);
    }

    /**
     * Remove the named Coherence persistence directory from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param clusterName           the name of the Coherence cluster used for segregating the config files
     * @param persistenceDirectory  the name of the Coherence persistence directory
     * @param silent                If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the Coherence persistence directory is not present (and silent = false)
     *                                      or an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the clusterName or persistenceDirectory is null or empty
     */
    public int removeCoherencePersistenceDirectory(String clusterName, String persistenceDirectory, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeCoherencePersistenceDirectory";
        LOGGER.entering(CLASS, METHOD, clusterName, persistenceDirectory, silent);

        validateNonEmptyString(clusterName, "clusterName", METHOD);
        validateNonEmptyString(persistenceDirectory, "persistenceDirectory", METHOD);

        String parentDir = ARCHIVE_COHERENCE_TARGET_DIR + ZIP_SEP + clusterName;
        String archivePath = parentDir + ZIP_SEP + persistenceDirectory;

        List<String> zipEntries =
            getSegregatedArchiveEntries(ArchiveEntryType.COHERENCE, clusterName, persistenceDirectory);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01454", clusterName,
                persistenceDirectory, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyDirs(parentDir);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                        JMS foreign server binding file methods                            //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a Foreign Server binding file to the archive.
     *
     * @param foreignServerName  the Foreign Server name used to segregate the directories
     * @param bindingPath        the file or directory to add
     * @return the new location of the file to use in the model
     * @throws WLSDeployArchiveIOException if an error occurs while archiving the file
     * @throws IllegalArgumentException    if the file does not exist or the foreignServerName is empty or null
     */
    public String addForeignServerFile(String foreignServerName, String bindingPath)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addForeignServerFile";
        LOGGER.entering(CLASS, METHOD, foreignServerName, bindingPath);

        validateNonEmptyString(foreignServerName, "foreignServerName", METHOD);
        File filePath = new File(bindingPath);
        validateExistingFile(filePath, "bindingPath", getArchiveFileName(), METHOD);

        String newName =
            addItemToZip(ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServerName, filePath);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace a Foreign Server binding file in the archive.
     *
     * @param foreignServerName the Foreign Server name used to segregate the directories
     * @param bindingPath       the Foreign Server binding file name or an archive path
     * @param sourceLocation the file system location of the new Foreign Server binding file to replace the existing one
     * @return the archive path of the new Foreign Server binding file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file passed in does not exist or the bindingPath is empty
     */
    public String replaceForeignServerFile(String foreignServerName, String bindingPath, String sourceLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "replaceForeignServerFile";
        LOGGER.entering(CLASS, METHOD, foreignServerName, bindingPath, sourceLocation);

        validateNonEmptyString(bindingPath, "bindingPath", METHOD);

        String archivePath = null;
        String computedForeignServerName = foreignServerName;
        if (bindingPath.startsWith(ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP)) {
            archivePath = bindingPath;
            computedForeignServerName = getSegregationNameFromSegregatedArchivePath(foreignServerName, bindingPath);
        } else if (!StringUtils.isEmpty(foreignServerName)) {
            if (bindingPath.startsWith(foreignServerName + ZIP_SEP)) {
                archivePath = ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + bindingPath;
            } else {
                archivePath = ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServerName + ZIP_SEP + bindingPath;
            }
        }

        if (StringUtils.isEmpty(computedForeignServerName)) {
            WLSDeployArchiveIOException ex =
                new WLSDeployArchiveIOException("WLSDPLY-01436", bindingPath, sourceLocation);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        // If we get here, archivePath should never be null!
        //
        getZipFile().removeZipEntry(archivePath);
        String newName = addForeignServerFile(computedForeignServerName, sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named Foreign Server binding file to the domain home location.
     *
     * @param foreignServerName            the name of the JMS Foreign Server used to segregate the bindings
     * @param bindingPath                  the name of the binding file
     * @param domainHome                   the existing directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or
     *                                     the foreignServerName or bindingPath is empty
     */
    public void extractForeignServerFile(String foreignServerName, String bindingPath, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractForeignServerFile";
        LOGGER.entering(CLASS, METHOD, foreignServerName, bindingPath, domainHome);

        validateNonEmptyString(foreignServerName, "foreignServerName", METHOD);
        validateNonEmptyString(bindingPath, "bindingPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath;
        if (bindingPath.startsWith(ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP)) {
            archivePath = bindingPath;
        } else if (bindingPath.startsWith(foreignServerName + ZIP_SEP)) {
            archivePath = ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + bindingPath;
        } else {
            archivePath = ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServerName + ZIP_SEP + bindingPath;
        }

        extractFileFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named JMS Foreign Server bindings file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param foreignServer     the name of the JMS Foreign Server used for segregating the bindings files
     * @param bindingsFileName  the name of the JMS Foreign Server bindings file
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the bindings file is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the foreignServer or bindingsFileName is null or empty
     */
    public int removeForeignServerFile(String foreignServer, String bindingsFileName)
        throws WLSDeployArchiveIOException {
        return removeForeignServerFile(foreignServer, bindingsFileName, false);
    }

    /**
     * Remove the named JMS Foreign Server bindings file from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param foreignServer     the name of the JMS Foreign Server used for segregating the bindings files
     * @param bindingsFileName  the name of the JMS Foreign Server bindings file
     * @param silent            If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the bindings file is not present (and silent = false) or
     *                                      an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the foreignServer or bindingsFileName is null or empty
     */
    public int removeForeignServerFile(String foreignServer, String bindingsFileName, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeForeignServerFile";
        LOGGER.entering(CLASS, METHOD, foreignServer, bindingsFileName, silent);

        validateNonEmptyString(foreignServer, "foreignServer", METHOD);
        validateNonEmptyString(bindingsFileName, "bindingsFileName", METHOD);

        String parentDir = ARCHIVE_JMS_FOREIGN_SERVER_DIR + ZIP_SEP + foreignServer;
        String archivePath = parentDir + ZIP_SEP + bindingsFileName;

        List<String> zipEntries =
            getSegregatedArchiveEntries(ArchiveEntryType.JMS_FOREIGN_SERVER, foreignServer, bindingsFileName);
        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01455", foreignServer,
                bindingsFileName, getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyDirs(parentDir);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    file store methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add an empty File Store directory to the archive file.
     *
     * @param fileStoreName name of the File Store
     * @return unique directory name created using the file store name
     * @throws WLSDeployArchiveIOException unexpected exception adding the directory name to the archive file
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
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
     * Replace an empty File Store directory in the archive file.
     *
     * @param fileStorePath the File Store name or path into the archive file to replace
     * @return the archive path to the new File Store directory.
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the file or directory passed in does not exist
     */
    public String replaceFileStoreDirectory(String fileStorePath) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceFileStoreDirectory";
        LOGGER.entering(CLASS, METHOD, fileStorePath);

        validateNonEmptyString(fileStorePath, "fileStorePath", METHOD);

        String archivePath;
        if (fileStorePath.startsWith(ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP)) {
            archivePath = fileStorePath;
        } else {
            archivePath = ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP + fileStorePath;
        }
        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }
        String computedFileStoreName = getFileStoreNameFromArchivePath(archivePath);

        getZipFile().removeZipEntries(archivePath);
        String newName = addEmptyDirectoryToZip(ARCHIVE_FILE_STORE_TARGET_DIR, computedFileStoreName);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named File Store directory to the domain home location.
     *
     * @param fileStorePath                the name of the File Store directory
     * @param domainHome                   the existing domain home directory location to write the file
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException    if the domainHome directory does not exist or the fileStorePath is empty
     */
    public void extractFileStoreDirectory(String fileStorePath, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractFileStoreDirectory";
        LOGGER.entering(CLASS, METHOD, fileStorePath, domainHome);

        validateNonEmptyString(fileStorePath, "fileStorePath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = fileStorePath;
        if (!fileStorePath.startsWith(ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP + fileStorePath;
        }

        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }

        extractDirectoryFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named File Store directory from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param fileStoreName the name of the File Store directory
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the File Store directory is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the fileStoreName is null or empty
     */
    public int removeFileStoreDirectory(String fileStoreName)
        throws WLSDeployArchiveIOException {
        return removeFileStoreDirectory(fileStoreName, false);
    }

    /**
     * Remove the named File Store directory from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param fileStoreName the name of the File Store directory
     * @param silent        If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the File Store directory is not present (and silent = false)
     *                                      or an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the fileStoreName is null or empty
     */
    public int removeFileStoreDirectory(String fileStoreName, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeFileStoreDirectory";
        LOGGER.entering(CLASS, METHOD, fileStoreName, silent);

        validateNonEmptyString(fileStoreName, "fileStoreName", METHOD);

        String archivePath = ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP + fileStoreName;

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.FILE_STORE, fileStoreName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01456", fileStoreName,
                getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.FILE_STORE, ARCHIVE_FILE_STORE_TARGET_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 database wallet methods                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add a database wallet to the archive.
     *
     * @param walletName     the name for this database wallet (used to segregate wallets)
     * @param sourceLocation the file system location for the wallet file (zip file or single file) or directory
     * @return the archive path to the wallet directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the wallet name if empty or the wallet file/directory does not exist
     */
    public String addDatabaseWallet(String walletName, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "addDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, walletName, sourceLocation);

        boolean verifyNotExists = DEFAULT_RCU_WALLET_NAME.equals(walletName);
        String newName = addDatabaseWallet(walletName, sourceLocation, verifyNotExists);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Add the RCU database wallet to the archive.
     *
     * @param sourceLocation the file system location for the wallet file (zip file or single file) or directory
     * @return the archive path to the wallet directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the wallet file/directory does not exist
     */
    public String addRCUDatabaseWallet(String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "addRCUDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, sourceLocation);

        String newName = addDatabaseWallet(DEFAULT_RCU_WALLET_NAME, sourceLocation, true);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace a database wallet in the archive.
     *
     * @param walletPath     the name of archive path of the database wallet directory
     * @param sourceLocation the file system location of the database wallet file/directory to replace the existing one
     * @return the archive path to the wallet directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the wallet name if empty or the wallet file/directory does not exist
     */
    public String replaceDatabaseWallet(String walletPath, String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, walletPath, sourceLocation);

        validateNonEmptyString(walletPath, "walletPath", METHOD);

        String archivePath;
        String computedWalletName;
        if (walletPath.startsWith(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP)) {
            archivePath = walletPath;
            computedWalletName = getDatabaseWalletNameFromArchivePath(walletPath);
        } else {
            archivePath = ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletPath;
            computedWalletName = walletPath;
        }
        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }

        getZipFile().removeZipEntries(archivePath);
        String newName = addDatabaseWallet(computedWalletName, sourceLocation, false);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace the RCU database wallet in the archive.
     *
     * @param sourceLocation the file system location of the database wallet file/directory to replace the existing one
     * @return the archive path to the wallet directory
     * @throws WLSDeployArchiveIOException if an IOException occurred while reading or writing changes
     * @throws IllegalArgumentException    if the wallet file/directory does not exist
     */
    public String replaceRCUDatabaseWallet(String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceRCUDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, sourceLocation);

        String newName = replaceDatabaseWallet(DEFAULT_RCU_WALLET_NAME, sourceLocation);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the named database wallet.  If the named database wallet is stored as a zip inside the archive,
     * this method will unzip that zip file so the result is always an expanded directory.
     *
     * @param domainHome the existing domain home directory
     * @param walletName the name of the database wallet to extract (e.g., rcu)
     * @return the full path to the directory containing the extracted wallet files or null, if no wallet was found
     * @throws WLSDeployArchiveIOException if an error occurs while reading or extracting the archive files
     * @throws IllegalArgumentException    if the wallet name if empty or the domain home directory does not exist
     * @see WLSDeployArchive#extractDatabaseWalletForArchiveHelper(String, File) 
     */
    public String extractDatabaseWallet(File domainHome, String walletName) throws WLSDeployArchiveIOException {
        final String METHOD = "extractDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, domainHome, walletName);

        validateNonEmptyString(walletName, "walletName", METHOD);

        String extractPath = null;
        if (DEFAULT_RCU_WALLET_NAME.equals(walletName)) {
            // handle archive files with deprecated path, as needed
            extractPath = extractRCUWallet(domainHome);
        } else {
            validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);
            List<String> zipEntries =
                getZipFile().listZipEntries(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletName + ZIP_SEP);
            zipEntries.remove(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletName + ZIP_SEP);
            if (!zipEntries.isEmpty()) {
                extractPath = ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletName + ZIP_SEP;
                extractWallet(domainHome, extractPath, zipEntries, null, null, null);
                extractPath = new File(domainHome, extractPath).getAbsolutePath();
            }
        }

        LOGGER.exiting(CLASS, METHOD, extractPath);
        return extractPath;
    }

    /**
     * Extract the RCU database wallet.  If the RCU database wallet is stored as a zip inside the archive,
     * this method will unzip that zip file so the result is always an expanded directory.
     *
     * @param domainHome the existing domain home directory
     * @return the full path to the directory containing the extracted wallet files or null, if no wallet was found
     * @throws WLSDeployArchiveIOException if an error occurs while reading or extracting the archive files
     * @throws IllegalArgumentException    if the domain home directory does not exist
     * @see WLSDeployArchive#extractRCUDatabaseWalletForArchiveHelper(File)
     */
    public String extractRCUDatabaseWallet(File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractRCUDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, domainHome);

        String extractPath = extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);

        LOGGER.exiting(CLASS, METHOD, extractPath);
        return extractPath;
    }

    /**
     * Extract the named database wallet.  Unlike extractDatabaseWallet(), this method will not
     * unzip the wallet if it is a zip file stored in the archive.  It also does not have any
     * handling of the old archive location for the rcu wallet.
     *
     * @param walletPath   the name of the database wallet to extract (e.g., rcu)
     * @param domainHome   the existing domain home directory
     * @throws WLSDeployArchiveIOException  if an error occurs while reading or extracting the archive files
     * @throws IllegalArgumentException     if the wallet name if empty or the domain home directory does not exist
     * @see WLSDeployArchive#extractDatabaseWallet(File, String) 
     */
    public void extractDatabaseWalletForArchiveHelper(String walletPath, File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractDatabaseWalletForArchiveHelper";
        LOGGER.entering(CLASS, METHOD, walletPath, domainHome);

        validateNonEmptyString(walletPath, "walletPath", METHOD);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = walletPath;
        if (!walletPath.startsWith(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + archivePath;
        }

        extractDirectoryFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Extract the RCU database wallet.  Unlike extractRCUDatabaseWallet(), this method will not
     * unzip the wallet if it is a zip file stored in the archive.  It also does not have any
     * handling of the old archive location for the rcu wallet.
     *
     * @param domainHome   the existing domain home directory
     * @throws WLSDeployArchiveIOException  if an error occurs while reading or extracting the archive files
     * @throws IllegalArgumentException     if the domain home directory does not exist
     * @see WLSDeployArchive#extractRCUDatabaseWallet(File)
     */
    public void extractRCUDatabaseWalletForArchiveHelper(File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractRCUDatabaseWalletForArchiveHelper";
        LOGGER.entering(CLASS, METHOD, domainHome);

        extractDatabaseWalletForArchiveHelper(DEFAULT_RCU_WALLET_NAME, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the named database wallet from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param walletName the name of the database wallet to remove
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the database wallet is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the walletName is null or empty
     */
    public int removeDatabaseWallet(String walletName) throws WLSDeployArchiveIOException {
        return removeDatabaseWallet(walletName, false);
    }

    /**
     * Remove the RCU database wallet from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the RCU database wallet is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     */
    public int removeRCUDatabaseWallet() throws WLSDeployArchiveIOException {
        return removeDatabaseWallet(DEFAULT_RCU_WALLET_NAME);
    }

    /**
     * Remove the named database wallet from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param walletName    the name of the database wallet to remove
     * @param silent        If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the database wallet is not present (and silent = false)
     *                                      or an IOException occurred while reading the archive or writing the file
     * @throws IllegalArgumentException     if the walletName is null or empty
     */
    public int removeDatabaseWallet(String walletName, boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, walletName, silent);

        validateNonEmptyString(walletName, "walletName", METHOD);

        String archivePath = ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletName;

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.DB_WALLET, walletName);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01457", walletName,
                getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }
        result += removeEmptyTypeDir(ArchiveEntryType.DB_WALLET, ARCHIVE_DB_WALLETS_DIR + ZIP_SEP);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Remove the RCU database wallet from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @param silent        If false, a WLSDeployArchiveIOException is thrown is the RCU wallet does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the RCU database wallet is not present (and silent = false)
     *                                      or an IOException occurred while reading the archive or writing the file
     */
    public int removeRCUDatabaseWallet(boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeRCUDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, silent);

        int result = removeDatabaseWallet(DEFAULT_RCU_WALLET_NAME, silent);

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   OPSS wallet methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Add the OPSS wallet to the archive.
     *
     * @param sourceLocation The file/directory to add
     * @return the archive path to the OPSS wallet directory
     * @throws WLSDeployArchiveIOException if an error occurs while reading or extracting the archive files.
     * @throws IllegalArgumentException    if the provided source location file/directory does not exist
     */
    public String addOPSSWallet(String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "addOPSSWallet";
        LOGGER.entering(CLASS, METHOD, sourceLocation);

        String newName = addOPSSWallet(sourceLocation, true);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Replace the OPSS wallet in the archive.
     *
     * @param sourceLocation The file/directory to use to replace the existing one
     * @return the archive path to the new OPSS wallet directory
     * @throws WLSDeployArchiveIOException if an error occurs while reading or extracting the archive files.
     * @throws IllegalArgumentException    if the provided source location file/directory does not exist
     */
    public String replaceOPSSWallet(String sourceLocation) throws WLSDeployArchiveIOException {
        final String METHOD = "replaceOPSSWallet";
        LOGGER.entering(CLASS, METHOD, sourceLocation);

        File sourceFile = FileUtils.getCanonicalFile(sourceLocation);
        validateExistingFile(sourceFile, "sourceLocation", getArchiveFileName(), METHOD, true);

        getZipFile().removeZipEntries(ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
        String newName = addOPSSWallet(sourceLocation, false);

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    /**
     * Extract the OPSS wallet from the archive.  If the OPSS wallet is stored as a zip inside the archive,
     * this method will unzip that zip file so the result is always an expanded directory.
     *
     * @param domainHome the domain home directory
     * @return the full path to the directory containing the extracted wallet files or null, if no wallet was found.
     * @throws WLSDeployArchiveIOException  if an error occurs while reading or extracting the archive files
     * @throws IllegalArgumentException     if the domain home directory does not exist
     * @see WLSDeployArchive#extractOPSSWalletForArchiveHelper(File)
     */
    public String extractOPSSWallet(File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractOPSSWallet";

        LOGGER.entering(CLASS, METHOD, domainHome);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        // Look in the updated location first
        String extractPath = null;
        List<String> zipEntries = getZipFile().listZipEntries(ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
        zipEntries.remove(ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
        if (!zipEntries.isEmpty()) {
            extractPath = ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP;
            extractWallet(domainHome, extractPath, zipEntries, null, null, null);
            extractPath = new File(domainHome, extractPath).getAbsolutePath();
        } else {
            // Look in the deprecated location.
            zipEntries = getZipFile().listZipEntries(OLD_ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
            zipEntries.remove(OLD_ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP);
            if (!zipEntries.isEmpty()) {
                extractPath = OLD_ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP;
                extractWallet(domainHome, extractPath, zipEntries, "WLSDPLY-01433",null, null);
                extractPath = new File(domainHome, extractPath).getAbsolutePath();
            }
        }

        LOGGER.exiting(CLASS, METHOD, extractPath);
        return extractPath;
    }

    /**
     * Extract the OPSS wallet.  Unlike extractOPSSWallet(), this method will not
     * unzip the wallet if it is a zip file stored in the archive.  It also does not have any
     * handling of the old archive location for the OPSS wallet.
     *
     * @param domainHome   the existing domain home directory
     * @throws WLSDeployArchiveIOException  if an error occurs while reading or extracting the archive files
     * @throws IllegalArgumentException     if the domain home directory does not exist
     * @see WLSDeployArchive#extractOPSSWallet(File)
     */
    public void extractOPSSWalletForArchiveHelper(File domainHome)
        throws WLSDeployArchiveIOException {
        final String METHOD = "extractDatabaseWalletForArchiveHelper";
        LOGGER.entering(CLASS, METHOD, domainHome);

        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        String archivePath = ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP;
        extractDirectoryFromZip(archivePath, domainHome);

        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Remove the OPSS wallet from the archive file.  If this is the only entry
     * in the archive file directory, the directory entry will also be removed, if present.
     *
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the OPSS wallet is not present or an IOException
     *                                      occurred while reading the archive or writing the file
     */
    public int removeOPSSWallet()
        throws WLSDeployArchiveIOException {
        return removeOPSSWallet(false);
    }

    /**
     * Remove the OPSS wallet from the archive file.
     *
     * @param silent        If false, a WLSDeployArchiveIOException is thrown is the named item does not exist
     * @return the number of zip entries removed from the archive
     * @throws WLSDeployArchiveIOException  if the OPSS wallet is not present (and silent = false)
     *                                      or an IOException occurred while reading the archive or writing the file
     */
    public int removeOPSSWallet(boolean silent)
        throws WLSDeployArchiveIOException {
        final String METHOD = "removeOPSSWallet";
        LOGGER.entering(CLASS, METHOD, silent);

        String archivePath = ARCHIVE_OPSS_WALLET_PATH + ZIP_SEP;

        List<String> zipEntries = getArchiveEntries(ArchiveEntryType.OPSS_WALLET);

        if (!silent && zipEntries.isEmpty()) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01458",
                getArchiveFileName(), archivePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        int result = zipEntries.size();
        for (String zipEntry : zipEntries) {
            getZipFile().removeZipEntry(zipEntry);
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////
    // Protected Helper methods                                                              //
    ///////////////////////////////////////////////////////////////////////////////////////////

    protected static String getArchiveName(String zipPathPrefix, String itemToAdd) {
        return getArchiveName(zipPathPrefix, itemToAdd, true);
    }

    protected static String getArchiveName(String zipPathPrefix, String itemToAdd, boolean useFileNameInEntryPath) {
        String newName = zipPathPrefix;
        if (useFileNameInEntryPath) {
            if (!newName.endsWith(ZIP_SEP)) {
                newName += ZIP_SEP;
            }
            newName += new File(itemToAdd).getName();
        }
        return newName;
    }

    protected WLSDeployZipFile getZipFile() {
        return zipFile;
    }

    protected void setZipFile(WLSDeployZipFile zipFile) {
        this.zipFile = zipFile;
    }

    protected static FileOrDirectoryType getFileType(ArchiveEntryType type) {
        final String METHOD = "getFileType";
        LOGGER.entering(CLASS, METHOD, type);

        FileOrDirectoryType result;
        switch(type) {
            case COHERENCE:
            case COHERENCE_PERSISTENCE_DIR:
            case DB_WALLET:
            case FILE_STORE:
            case OPSS_WALLET:
            case RCU_WALLET:
            case STRUCTURED_APPLICATION:
                result = FileOrDirectoryType.DIRECTORY_ONLY;
                break;

            case APPLICATION_PLAN:
            case COHERENCE_CONFIG:
            case DOMAIN_BIN:
            case DOMAIN_LIB:
            case JMS_FOREIGN_SERVER:
            case MIME_MAPPING:
            case NODE_MANAGER_KEY_STORE:
            case SCRIPT:
            case SERVER_KEYSTORE:
            case SHLIB_PLAN:
                result = FileOrDirectoryType.FILE_ONLY;
                break;

            default:
                result = FileOrDirectoryType.EITHER;
                break;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    protected static boolean isSegregatedType(ArchiveEntryType type) {
        final String METHOD = "isSegregatedType";
        LOGGER.entering(CLASS, METHOD, type);

        boolean result;
        switch(type) {
            case COHERENCE:
            case COHERENCE_CONFIG:
            case COHERENCE_PERSISTENCE_DIR:
            case DB_WALLET:
            case JMS_FOREIGN_SERVER:
            case SERVER_KEYSTORE:
                result = true;
                break;

            default:
                result = false;
                break;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
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

    protected static String getURLArchiveName(String zipPathPrefix, URL url, boolean useFileNameInEntryPath) {
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

    protected List<String> getZipListEntries(String prefix, String name, FileOrDirectoryType type)
        throws WLSDeployArchiveIOException {
        final String METHOD = "getZipListEntries";
        LOGGER.entering(CLASS, METHOD, prefix, name, type.name());

        validateNonEmptyString(prefix, "prefix", METHOD);
        validateNonEmptyString(name, "name", METHOD);

        String archivePrefix = prefix;
        if (!archivePrefix.endsWith(ZIP_SEP)) {
            archivePrefix += ZIP_SEP;
        }

        String archivePath = archivePrefix + name;
        List<String> zipEntries = getZipFile().listZipEntries(archivePath);

        ListIterator<String> zipEntriesIterator = zipEntries.listIterator();
        while (zipEntriesIterator.hasNext()) {
            String zipEntry = zipEntriesIterator.next();

            if (filterEntry(zipEntry, archivePrefix, name, type)) {
                zipEntriesIterator.remove();
            }
        }

        LOGGER.exiting(CLASS, METHOD, zipEntries);
        return zipEntries;
    }

    protected void extractWallet(File domainHome, String extractPath, List<String> zipEntries, String deprecationKey,
                                 String fromDir, String toDir) throws WLSDeployArchiveIOException {
        final String METHOD = "extractWallet";
        LOGGER.entering(CLASS, METHOD, domainHome, extractPath, zipEntries, deprecationKey);

        File fullExtractPath = new File(domainHome, extractPath);
        if (zipEntries != null && !zipEntries.isEmpty()) {
            String firstZipEntry = zipEntries.get(0);
            if (!fullExtractPath.exists() && !fullExtractPath.mkdirs()) {
                WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01430", firstZipEntry,
                    getArchiveFileName(), fullExtractPath.getAbsolutePath());
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
            }

            // The archive file wallet directory can either contain a single zip file containing the wallet files
            // or one or more wallet files.  Before starting to iterate, check for the single zip file case.
            //
            if (zipEntries.size() == 1 && firstZipEntry.toLowerCase().endsWith(".zip")) {
                if (!StringUtils.isEmpty(deprecationKey)) {
                    LOGGER.warning(deprecationKey, getArchiveFileName(), firstZipEntry, extractPath);
                }
                unzipZippedArchiveFileEntry(firstZipEntry, fullExtractPath);
            } else {
                for (String zipEntry : zipEntries) {
                    File extractToLocation = domainHome;
                    if (!StringUtils.isEmpty(deprecationKey)) {
                        extractToLocation = new File(domainHome, WLSDPLY_ARCHIVE_BINARY_DIR);
                        LOGGER.deprecation(deprecationKey, getArchiveFileName(), zipEntry, extractPath);
                    }
                    if (StringUtils.isEmpty(fromDir) && StringUtils.isEmpty(toDir)) {
                        extractFileFromZip(zipEntry, extractToLocation);
                    } else {
                        extractFileFromZip(zipEntry, fromDir, toDir, extractToLocation);
                    }
                }
            }
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    protected void unzipZippedArchiveFileEntry(String zippedItemToExtract, File extractToLocation)
        throws WLSDeployArchiveIOException {
        final String METHOD = "unzipZippedArchiveFileEntry";
        LOGGER.entering(CLASS, METHOD, zippedItemToExtract, extractToLocation);

        File tempDir;
        try {
            tempDir = Files.createTempDirectory("tempzip").toFile();
            tempDir.deleteOnExit();
        } catch (IOException ioe) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01428", ioe, zippedItemToExtract,
                ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        String zippedEntryPath = extractFile(zippedItemToExtract, tempDir);

        try (FileInputStream fis = new FileInputStream(zippedEntryPath);
             ZipInputStream zis = new ZipInputStream(fis)) {

            ZipEntry ze = zis.getNextEntry();
            while (ze != null) {
                String zipEntryFileName = ze.getName();
                checkForZipSlip(extractToLocation, zipEntryFileName);

                File zipEntryFile = new File(extractToLocation, ze.getName());
                if (!zipEntryFile.getParentFile().exists() && !zipEntryFile.getParentFile().mkdirs()) {
                    WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01429", zipEntryFileName,
                        extractToLocation.getAbsolutePath());
                    LOGGER.throwing(CLASS, METHOD, ex);
                    throw ex;
                }

                try (FileOutputStream fos = new FileOutputStream(zipEntryFile, false)) {
                    byte[] buffer = new byte[4096];
                    int len = zis.read(buffer);
                    while (len > 0) {
                        fos.write(buffer, 0, len);
                        len = zis.read(buffer);
                    }
                }
                zis.closeEntry();
                ze = zis.getNextEntry();
            }
        } catch (IOException ioe) {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01432", ioe, zippedEntryPath,
                zippedItemToExtract, extractToLocation, ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    protected String addDatabaseWallet(String walletName, String sourceLocation, boolean verifyNotExists)
        throws WLSDeployArchiveIOException {
        final String METHOD = "addDatabaseWallet";
        LOGGER.entering(CLASS, METHOD, walletName, sourceLocation, verifyNotExists);

        File sourceFile = FileUtils.getCanonicalFile(sourceLocation);
        validateNonEmptyString(walletName, "walletName", METHOD);
        validateExistingFile(sourceFile, "sourceLocation", getArchiveFileName(), METHOD, true);

        // Because there is only one RCU wallet per domain, we have to make sure that
        // there is no existing RCU wallet in the archive prior to adding one.
        //
        if (verifyNotExists) {
            List<String> rcuWalletEntries = getArchiveEntries(ArchiveEntryType.RCU_WALLET);
            if (!rcuWalletEntries.isEmpty()) {
                WLSDeployArchiveIOException ex =
                    new WLSDeployArchiveIOException("WLSDPLY-01459", getArchiveFileName(), rcuWalletEntries.size());
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
            }
        }

        String newName;
        if (sourceFile.isDirectory()) {
            newName = addItemToZip(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletName, sourceFile, false);
        } else {
            newName = addItemToZip(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP + walletName, sourceFile);

            // When adding a file (e.g., zip file), the wallet name returned should always point
            // to the wallet directory containing the file.
            //
            newName = getDatabaseWalletArchivePathFromAddedFile(ARCHIVE_DB_WALLETS_DIR, newName);
        }

        LOGGER.exiting(CLASS, METHOD, newName);
        return newName;
    }

    protected String addOPSSWallet(String sourceLocation, boolean verifyNotExists) throws WLSDeployArchiveIOException {
        final String METHOD = "addOPSSWallet";
        LOGGER.entering(CLASS, METHOD, sourceLocation, verifyNotExists);

        File sourceFile = FileUtils.getCanonicalFile(sourceLocation);
        validateExistingFile(sourceFile, "sourceLocation", getArchiveFileName(), METHOD, true);

        // Because there is only one OPSS wallet per domain, we have to make sure that
        // there is no existing OPSS wallet in the archive prior to adding one.
        //
        if (verifyNotExists) {
            List<String> opssWalletEntries = getArchiveEntries(ArchiveEntryType.OPSS_WALLET);
            if (!opssWalletEntries.isEmpty()) {
                WLSDeployArchiveIOException ex =
                    new WLSDeployArchiveIOException("WLSDPLY-01437", getArchiveFileName(), opssWalletEntries.size());
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
            }
        }

        String newName;
        if (sourceFile.isDirectory()) {
            newName = addItemToZip(ARCHIVE_OPSS_WALLET_PATH, sourceFile);
        } else {
            addItemToZip(ARCHIVE_OPSS_WALLET_PATH, sourceFile);

            // When adding a file (e.g., zip file), the wallet name returned should always point
            // to the wallet directory containing the file.
            //
            newName = ARCHIVE_OPSS_WALLET_PATH;
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
                    checkForZipSlip(extractToLocation, targetFileName);
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
            } else {
                WLSDeployArchiveIOException ex =
                    new WLSDeployArchiveIOException("WLSDPLY-01416", getArchiveFileName(), dirName);
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
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
        String targetFileName = itemToExtract;
        if (fromDir != null && toDir != null) {
            targetFileName = itemToExtract.replace(fromDir + ZIP_SEP, toDir + SEP);
        }
        checkForZipSlip(extractToLocation, targetFileName);

        InputStream inputStream = getZipFile().getZipEntry(itemToExtract);
        if (inputStream == null) {
            WLSDeployArchiveIOException wdaioe =
                new WLSDeployArchiveIOException("WLSDPLY-01416", getArchiveFileName(), itemToExtract);
            LOGGER.throwing(CLASS, METHOD, wdaioe);
            throw wdaioe;
        }

        File targetFile = new File(extractToLocation, targetFileName);
        File targetDirectory = targetFile.getParentFile();
        if (!targetDirectory.exists() && !targetDirectory.mkdirs()) {
            WLSDeployArchiveIOException wdaioe = new WLSDeployArchiveIOException("WLSDPLY-01414", getArchiveFileName(),
                targetDirectory.getAbsolutePath());
            try {
                inputStream.close();
            } catch (IOException ignore) {
                // best effort
            }
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

    protected String extractRCUWallet(File domainHome) throws WLSDeployArchiveIOException {
        final String METHOD = "extractRCUWallet";

        LOGGER.entering(CLASS, METHOD, domainHome);
        validateExistingDirectory(domainHome, "domainHome", getArchiveFileName(), METHOD);

        // Look in the updated location first
        String extractPath = null;
        List<String> zipEntries = getZipFile().listZipEntries(DEFAULT_RCU_WALLET_PATH + ZIP_SEP);
        zipEntries.remove(DEFAULT_RCU_WALLET_PATH + ZIP_SEP);
        if (!zipEntries.isEmpty()) {
            extractPath = DEFAULT_RCU_WALLET_PATH + ZIP_SEP;
            extractWallet(domainHome, extractPath, zipEntries, null, null, null);
            extractPath = new File(domainHome, extractPath).getAbsolutePath();
        } else {
            // Look in the deprecated location.
            zipEntries = getZipFile().listZipEntries(OLD_ARCHIVE_ATP_WALLET_PATH + ZIP_SEP);
            zipEntries.remove(OLD_ARCHIVE_ATP_WALLET_PATH + ZIP_SEP);
            if (!zipEntries.isEmpty()) {
                extractPath = DEFAULT_RCU_WALLET_PATH + ZIP_SEP;
                extractWallet(domainHome, extractPath, zipEntries, "WLSDPLY-01427",
                    OLD_ARCHIVE_ATP_WALLET_PATH, DB_WALLETS_DIR_NAME + ZIP_SEP + DEFAULT_RCU_WALLET_NAME);
                extractPath = new File(domainHome, extractPath).getAbsolutePath();
            }
        }

        LOGGER.exiting(CLASS, METHOD, extractPath);
        return extractPath;
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

    private boolean filterEntry(String entry, String prefix, String name, FileOrDirectoryType allowedType) {
        boolean result = true;

        String prefixStrippedZipEntry = entry.substring(prefix.length());
        String directoryName = name.endsWith(ZIP_SEP) ? name : name + ZIP_SEP;
        if ((prefixStrippedZipEntry.startsWith(directoryName) && allowedType != FileOrDirectoryType.FILE_ONLY) ||
            (prefixStrippedZipEntry.equals(name) && allowedType != FileOrDirectoryType.DIRECTORY_ONLY)){
            result = false;
        }
        return result;
    }

    // TODO - remove me and replace calls with addItemToZip() to get the correct behavior.
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

    private void checkForZipSlip(File extractLocation, String zipEntry) throws WLSDeployArchiveIOException {
        String canonicalExtractLocation = FileUtils.getCanonicalPath(extractLocation);
        String canonicalZipEntry = FileUtils.getCanonicalPath(new File(extractLocation, zipEntry));

        if (!canonicalZipEntry.startsWith(canonicalExtractLocation)) {
            throw new WLSDeployArchiveIOException("WLSDPLY-01431", getArchiveFileName(), zipEntry, canonicalZipEntry,
                canonicalExtractLocation);
        }
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

    private String getSegregationNameFromSegregatedArchivePath(String segregationName, String archivePath) {
        String result = null;
        if (StringUtils.isEmpty(segregationName)) {
            String[] pathComponents = archivePath.split(ZIP_SEP);
            if (pathComponents.length > 3) {
                result = pathComponents[2];
            }
        } else {
            result = segregationName;
        }
        return result;
    }

    private String getFileStoreNameFromArchivePath(String archivePath) {
        String result = archivePath;

        if (result.endsWith(ZIP_SEP)) {
            result = result.substring(0, result.length() - 1);
        }
        int lastIndex = result.lastIndexOf(ZIP_SEP);
        if (lastIndex != -1) {
            result = result.substring(lastIndex + 1);
        }
        return result;
    }

    private String getDatabaseWalletNameFromArchivePath(String archivePath) {
        String result = archivePath;

        if (result.endsWith(ZIP_SEP)) {
            result = result.substring(0, result.length() - 1);
        }
        if (result.startsWith(ARCHIVE_DB_WALLETS_DIR + ZIP_SEP)) {
            String[] comps = result.split(ZIP_SEP);
            if (comps.length > 2) {
                result = comps[2];
            }
        }
        return result;
    }

    private String getDatabaseWalletArchivePathFromAddedFile(String walletParentPath, String walletFileName) {
        String result = null;

        int fromIndex = walletParentPath.length();
        if (!walletParentPath.endsWith(ZIP_SEP)) {
            fromIndex++;
        }
        int endIndex = walletParentPath.indexOf(ZIP_SEP, fromIndex);
        if (endIndex != -1) {
            result = walletFileName.substring(0, endIndex);
        }
        return result;
    }

    private String getNameFromPath(String path, int startIndex) throws WLSDeployArchiveIOException {
        final String METHOD = "getNameFromPath";
        LOGGER.entering(CLASS, METHOD, path, startIndex);

        String result;
        if (!StringUtils.isEmpty(path) && path.length() >= startIndex) {
            result = path.substring(startIndex);
        } else {
            WLSDeployArchiveIOException ex = new WLSDeployArchiveIOException("WLSDPLY-01439", startIndex, path);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    private String getCustomArchivePath(String relativePath) {
        final String METHOD = "getCustomArchivePath";
        LOGGER.entering(CLASS, METHOD, relativePath);

        String archivePath = ARCHIVE_CUSTOM_TARGET_DIR;
        if (!StringUtils.isEmpty(relativePath)) {
            if (!relativePath.startsWith(ZIP_SEP)) {
                archivePath += ZIP_SEP;
            }
            archivePath += relativePath;
        }

        LOGGER.exiting(CLASS, METHOD, archivePath);
        return archivePath;
    }

    private String getCustomArchivePathForReplace(String replacementPath) {
        final String METHOD = "getCustomArchivePathForReplace";
        LOGGER.entering(CLASS, METHOD, replacementPath);

        String archivePath = replacementPath;
        if (replacementPath.startsWith(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP)) {
            archivePath = replacementPath.substring(ARCHIVE_CUSTOM_TARGET_DIR.length() + 2);
        } else if (replacementPath.startsWith(ZIP_SEP)) {
            archivePath = replacementPath.substring(1);
        }

        if (archivePath.endsWith(ZIP_SEP)) {
            archivePath = archivePath.substring(0, archivePath.length() - 1);
        }

        int lastZipSep = archivePath.lastIndexOf(ZIP_SEP);
        if (lastZipSep != -1) {
            archivePath = archivePath.substring(0, lastZipSep);
        } else {
            archivePath = null;
        }

        LOGGER.exiting(CLASS, METHOD, archivePath);
        return archivePath;
    }

    private String getCustomArchivePathParentDir(String removePath) {
        final String METHOD = "getCustomArchivePathParentDir";
        LOGGER.entering(CLASS, METHOD, removePath);

        String archivePath = removePath;
        if (!removePath.startsWith(ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP)) {
            archivePath = ARCHIVE_CUSTOM_TARGET_DIR + ZIP_SEP + removePath;
        }

        if (archivePath.endsWith(ZIP_SEP)) {
            archivePath = archivePath.substring(0, archivePath.length() - 1);
        }

        int lastZipSep = archivePath.lastIndexOf(ZIP_SEP);
        if (lastZipSep != -1) {
            archivePath = archivePath.substring(0, lastZipSep);
        } else {
            archivePath = null;
        }

        LOGGER.exiting(CLASS, METHOD, archivePath);
        return archivePath;

    }

    private int removeEmptyDirs(String parentDir) throws WLSDeployArchiveIOException {
        final String METHOD = "removeEmptyDirs";
        LOGGER.entering(CLASS, METHOD, parentDir);

        String archivePath = parentDir;
        if (!archivePath.endsWith(ZIP_SEP)) {
            archivePath += ZIP_SEP;
        }

        List<String> zipEntries = getZipFile().listZipEntries(archivePath);

        int result = 0;
        if (zipEntries.size() == 1 && archivePath.equals(zipEntries.get(0))) {
            getZipFile().removeZipEntry(zipEntries.get(0));
            result++;

            int lastZipSep = archivePath.substring(0, archivePath.length() - 1).lastIndexOf(ZIP_SEP);
            if (lastZipSep != -1) {
                String newParentDir = archivePath.substring(0, lastZipSep);
                result += removeEmptyDirs(newParentDir);
            }
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    private int removeEmptyTypeDir(ArchiveEntryType type, String prefixPath) throws WLSDeployArchiveIOException {
        final String METHOD = "removeEmptyTypeDir";
        LOGGER.entering(CLASS, METHOD, type.name(), prefixPath);

        List<String> zipEntries = getArchiveEntries(type);

        int result = 0;
        if (zipEntries.size() == 1 && prefixPath.equals(zipEntries.get(0))) {
            getZipFile().removeZipEntry(zipEntries.get(0));
            result = 1;
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    // The archiveHelper does not require that users specify a trailing / on directory names.
    // As such, we have to figure out if the path is a directory and requires appending a
    // trailing / to make the extraction code work properly with directories.
    //
    private String fixupPathForDirectories(String path) throws WLSDeployArchiveIOException {
        final String METHOD = "fixupPathForDirectories";
        LOGGER.entering(CLASS, METHOD, path);

        String result = path;
        if (!path.endsWith(ZIP_SEP)) {
            List<String> zipEntries = getZipFile().listZipEntries(path + ZIP_SEP);
            if (zipEntries.contains(path + ZIP_SEP)) {
                result = path + ZIP_SEP;
            }
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }
}
