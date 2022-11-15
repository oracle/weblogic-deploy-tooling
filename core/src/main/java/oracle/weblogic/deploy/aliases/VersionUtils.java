/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.aliases;

import java.util.Arrays;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.StringUtils;

/**
 * A utility class that provides helper methods for working with version numbers and ranges.
 */
public final class VersionUtils {
    private static final String CLASS = VersionUtils.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.versions");

    private static final String VERSION_REGEX_STRING = "[(\\[][ ]*(\\d+([-.]\\d+){0,5})[ ]*[)\\]]?";
    private static final Pattern VERSION_REGEX = Pattern.compile(VERSION_REGEX_STRING);
    private static final int VERSION_GROUP = 1;

    private static final String VERSION_RANGE_REGEX_STRING =
        "[(\\[][ ]*(\\d*([-.]\\d+){0,5})[ ]*,[ ]*(\\d*([-.]\\d+){0,5})[ ]*[)\\]]";
    private static final Pattern VERSION_RANGE_REGEX = Pattern.compile(VERSION_RANGE_REGEX_STRING);
    private static final int RANGE_LOW_GROUP = 1;
    private static final int RANGE_HIGH_GROUP = 3;

    private static final int RANGE_SIZE = 2;
    private static final int RANGE_LOW_INDEX = 0;
    private static final int RANGE_HIGH_INDEX = 1;

    private static final int VERSION_SIZE = 1;
    private static final int VERSION_INDEX = 0;

    private VersionUtils() {
        // hide the constructor on this utility class
    }

    /**
     * Compares two version strings.  Any qualifiers are treated as older than the same version without
     * a qualifier.  If both versions have qualifiers and are otherwise equal, they are compared using
     * String.compareTo() to determine the result.
     *
     * @param thisVersion - first version
     * @param otherVersion - second version
     * @return returns 0 if the versions are equal, greater than zero if thisVersion is newer,
     *         and less than zero if thisVersion is older.
     * @throws VersionException - if there is an error parsing the version number
     * @throws IllegalArgumentException - if one or both version numbers are empty or null
     */
    public static int compareVersions(String thisVersion, String otherVersion) throws VersionException {
        final String METHOD = "compareVersions";

        LOGGER.entering(CLASS, METHOD, thisVersion, otherVersion);
        if (StringUtils.isEmpty(thisVersion) || StringUtils.isEmpty(otherVersion)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-08200");
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        String[] tmp = thisVersion.split("-");
        String strippedThisVersion = tmp[0];
        String[] thisVersionElements = strippedThisVersion.split("\\.");

        tmp = otherVersion.split("-");
        String strippedOtherVersion = tmp[0];
        String[] otherVersionElements = strippedOtherVersion.split("\\.");

        int fieldsToCompare;
        if (thisVersionElements.length <= otherVersionElements.length) {
            fieldsToCompare = thisVersionElements.length;
        } else {
            fieldsToCompare = otherVersionElements.length;
        }

        int result = 0;
        int idx;
        for (idx = 0; idx < fieldsToCompare; idx++) {
            int thisVersionNumber = parseVersionElement(thisVersionElements[idx], thisVersion);
            int otherVersionNumber = parseVersionElement(otherVersionElements[idx], otherVersion);

            result = Integer.compare(thisVersionNumber, otherVersionNumber);
            if (result != 0) {
                break;
            }
        }

        // Version fields compared so far are equal so check to see if one version number
        // has more fields than the other.  Extra fields only count if their value is
        // greater than zero.
        //
        if (result == 0 && thisVersionElements.length != otherVersionElements.length) {
            if (thisVersionElements.length > otherVersionElements.length) {
                for (int i = otherVersionElements.length; i < thisVersionElements.length; i++) {
                    int thisVersionNumber = Integer.parseInt(thisVersionElements[i]);
                    if (thisVersionNumber > 0) {
                        result = 1;
                        break;
                    }
                }
            } else {
                result = -1;
            }
        }

        // Finally, look to see if one or both versions have a qualifier if they are otherwise the same.
        //
        if (result == 0) {
            int useCase = 0;
            if (thisVersion.indexOf('-') != -1) {
                useCase += 1;
            }
            if (otherVersion.indexOf('-') != -1) {
                useCase += 2;
            }
            switch (useCase) {
                case 1:
                    result = -1;
                    break;

                case 2:
                    result = 1;
                    break;

                case 3:
                    String thisQualifier = thisVersion.substring(thisVersion.indexOf('-'));
                    String otherQualifier = otherVersion.substring(otherVersion.indexOf('-'));
                    result = thisQualifier.compareTo(otherQualifier);
                    break;

                default:
                    break;
            }
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Determine if the specified version is included in the specified version range.
     *
     * @param version the version to test
     * @param range the Maven-style version range
     * @return true if the specified version falls within the specified version range, false otherwise
     * @throws VersionException if the version range is not a valid version or version range
     * @throws IllegalArgumentException if the version or range arguments are empty or null
     */
    public static boolean isVersionInRange(String version, String range) throws VersionException {
        final String METHOD = "isVersionInRange";
        LOGGER.entering(CLASS, METHOD, version, range);

        if (StringUtils.isEmpty(version)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-08200");
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        String[] versions = getLowerAndUpperVersionStrings(range);
        LOGGER.finest("WLSDPLY-08201", range, Arrays.asList(versions));
        boolean result = false;
        switch (versions.length) {
            case RANGE_SIZE:
                String lowerVersion = versions[RANGE_LOW_INDEX];
                String upperVersion = versions[RANGE_HIGH_INDEX];
                boolean inclusiveStart = range.startsWith("[");
                boolean inclusiveEnd = range.endsWith("]");

                int lowerCompare = compareVersions(version, lowerVersion);
                LOGGER.finest("WLSDPLY-08202", version, lowerVersion, lowerCompare);
                if (lowerCompare > 0 || (lowerCompare == 0 && inclusiveStart)) {
                    if (!StringUtils.isEmpty(upperVersion)) {
                        int upperCompare = compareVersions(version, upperVersion);
                        LOGGER.finest("WLSDPLY-08203", version, upperVersion, upperCompare);
                        if (upperCompare < 0 || (upperCompare == 0 && inclusiveEnd)) {
                            result = true;
                        }
                    } else {
                        LOGGER.finest("WLSDPLY-08204", range);
                        result = true;
                    }
                }
                break;

            case VERSION_SIZE:
                String singleVersion = versions[VERSION_INDEX];
                result = (compareVersions(version, singleVersion) == 0);
                LOGGER.finest("WLSDPLY-08205", version, singleVersion, result);
                break;

            default:
                VersionException ve = new VersionException("WLSDPLY-08206", range, Arrays.asList(versions));
                LOGGER.throwing(CLASS, METHOD, ve);
                throw ve;
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Determine if the specified version ranges overlap.
     *
     * @param range1 the version range to test
     * @param range2 the version range to test against
     * @return true if the specified version ranges overlap, false otherwise
     * @throws VersionException if either version range is not a valid version or version range
     * @throws IllegalArgumentException if either version range argument is empty or null
     */
    public static boolean doVersionRangesOverlap(String range1, String range2) throws VersionException {
        final String METHOD = "doVersionRangesOverlap";
        LOGGER.entering(CLASS, METHOD, range1, range2);

        if (StringUtils.isEmpty(range1) || StringUtils.isEmpty(range2)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-08215");
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        boolean result = false;
        String[] versions1 = getLowerAndUpperVersionStrings(range1);
        boolean isSingleVersion1 = (versions1.length == VERSION_SIZE);
        String lowerVersion1 = versions1[RANGE_LOW_INDEX];
        String upperVersion1 = !isSingleVersion1 ? versions1[RANGE_HIGH_INDEX] : lowerVersion1;

        String[] versions2 = getLowerAndUpperVersionStrings(range2);
        boolean isSingleVersion2 = versions2.length == VERSION_SIZE;
        String lowerVersion2 = versions2[RANGE_LOW_INDEX];
        String upperVersion2 = !isSingleVersion2 ? versions2[RANGE_HIGH_INDEX] : lowerVersion2;
        boolean inclusiveStart2 = range2.startsWith("[");
        boolean inclusiveEnd2 = range2.endsWith("]");

        // check if range2 lower value is inside range1

        if(StringUtils.isEmpty(lowerVersion2)) {
            // if range2 has empty lower version, its upper version must be below range1
            if(StringUtils.isEmpty(lowerVersion1)) {
                result = true;
            } else if(compareVersions(upperVersion2, lowerVersion1) > 0) {
                result = true;
            }
        } else if(isVersionInRange(lowerVersion2, range1)) {
            // it's only ok to be inside range1 if the start of range2 is adjacent to range1
            boolean adjacent = !inclusiveStart2 && lowerVersion2.equals(upperVersion1);
            if(!adjacent) {
                result = true;
            }
        }

        // check if range2 upper value is inside range1

        if(StringUtils.isEmpty(upperVersion2)) {
            // if range2 has empty upper version, its lower version must be above range1
            if(StringUtils.isEmpty(upperVersion1)) {
                result = true;
            } else if(compareVersions(upperVersion1, lowerVersion2) > 0) {
                result = true;
            }
        } else if(isVersionInRange(upperVersion2, range1)) {
            // it's only ok to be inside range1 if the end of range2 is adjacent to range1
            boolean adjacent = !inclusiveEnd2 && upperVersion2.equals(lowerVersion1);
            if(!adjacent) {
                result = true;
            }
        }

        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    /**
     * Get the version range message to use for validation.
     *
     * @param name the attribute name
     * @param path the folder path that contains the attribute
     * @param version the WebLogic version being used
     * @param versionRange the range of versions where the attribute is valid
     * @param wlstMode the WLST mode
     * @return the formatted message
     * @throws VersionException if an error occurs parsing the version range
     */
    public static String getValidAttributeVersionRangeMessage(String name, String path, String version,
        String versionRange, String wlstMode) throws VersionException {
        final String METHOD = "getValidVersionRangeMessage";

        LOGGER.entering(CLASS, METHOD, name, path, version, versionRange, wlstMode);
        String message;
        if (!StringUtils.isEmpty(versionRange)) {
            String[] versions = getLowerAndUpperVersionStrings(versionRange);

            switch (versions.length) {
                case RANGE_SIZE:
                    String low = versions[RANGE_LOW_INDEX];
                    String high = versions[RANGE_HIGH_INDEX];
                    if (StringUtils.isEmpty(high)) {
                        message = ExceptionHelper.getMessage("WLSDPLY-08207", name, path, version, low);
                    } else {
                        message = ExceptionHelper.getMessage("WLSDPLY-08208", name, path, version, low, high);
                    }
                    break;

                case VERSION_SIZE:
                    String onlyVersion = versions[VERSION_INDEX];
                    message = ExceptionHelper.getMessage("WLSDPLY-08209", name, path, version, onlyVersion);
                    break;

                default:
                    VersionException ve = new VersionException("WLSDPLY-08206", versionRange, Arrays.asList(versions));
                    LOGGER.throwing(CLASS, METHOD, ve);
                    throw ve;
            }
        } else {
            message = ExceptionHelper.getMessage("WLSDPLY-08210", name, path, version, wlstMode);
        }
        return message;
    }

    /**
     * Get the version range message to use for validation.
     *
     * @param name the subfolder name
     * @param path the folder path that contains the subfolder
     * @param version the WebLogic version being used
     * @param versionRange the range of versions where the subfolder is valid
     * @param wlstMode the WLST mode
     * @return the formatted message
     * @throws VersionException if an error occurs parsing the version range
     */
    public static String getValidFolderVersionRangeMessage(String name, String path, String version,
        String versionRange, String wlstMode) throws VersionException {
        final String METHOD = "getValidFolderVersionRangeMessage";

        LOGGER.entering(CLASS, METHOD, name, path, version, versionRange, wlstMode);
        String message;
        if (!StringUtils.isEmpty(versionRange)) {
            String[] versions = getLowerAndUpperVersionStrings(versionRange);

            switch (versions.length) {
                case RANGE_SIZE:
                    String low = versions[RANGE_LOW_INDEX];
                    String high = versions[RANGE_HIGH_INDEX];
                    if (StringUtils.isEmpty(high)) {
                        message = ExceptionHelper.getMessage("WLSDPLY-08211", name, path, version, low);
                    } else {
                        message = ExceptionHelper.getMessage("WLSDPLY-08212", name, path, version, low, high);
                    }
                    break;

                case VERSION_SIZE:
                    String onlyVersion = versions[VERSION_INDEX];
                    message = ExceptionHelper.getMessage("WLSDPLY-08213", name, path, version, onlyVersion);
                    break;

                default:
                    VersionException ve = new VersionException("WLSDPLY-08206", versionRange, Arrays.asList(versions));
                    LOGGER.throwing(CLASS, METHOD, ve);
                    throw ve;
            }
        } else {
            message = ExceptionHelper.getMessage("WLSDPLY-08214", name, path, version, wlstMode);
        }
        return message;
    }
    /**
     * Decompose the version range into an array of version strings.
     *
     * @param range the version range
     * @return an array of versions parsed from the range, which is either one or two elements long.
     * @throws VersionException if an error occurs parsing the range
     * @throws IllegalArgumentException if the range argument is empty or null
     */
    public static String[] getLowerAndUpperVersionStrings(String range) throws VersionException {
        final String METHOD = "getLowerAndUpperVersionStrings";
        LOGGER.entering(CLASS, METHOD, range);

        if (StringUtils.isEmpty(range)) {
            String message = ExceptionHelper.getMessage("WLSDPLY-08215");
            IllegalArgumentException iae = new IllegalArgumentException(message);
            LOGGER.throwing(CLASS, METHOD, iae);
            throw iae;
        }

        Matcher rangeMatcher = VERSION_RANGE_REGEX.matcher(range);
        Matcher versionMatcher = VERSION_REGEX.matcher(range);

        String[] result;
        if (rangeMatcher.matches()) {
            String lowerVersion = rangeMatcher.group(RANGE_LOW_GROUP);
            String upperVersion = rangeMatcher.group(RANGE_HIGH_GROUP);

            if (StringUtils.isEmpty(upperVersion)) {
                upperVersion = null;
            }
            result = new String[RANGE_SIZE];
            result[RANGE_LOW_INDEX] = lowerVersion;
            result[RANGE_HIGH_INDEX] = upperVersion;
        } else if (versionMatcher.matches()) {
            String version = versionMatcher.group(VERSION_GROUP);
            result = new String[VERSION_SIZE];
            result[VERSION_INDEX] = version;
        } else {
            VersionException ve = new VersionException("WLSDPLY-08216", range);
            LOGGER.throwing(CLASS, METHOD, ve);
            throw ve;
        }
        LOGGER.exiting(CLASS, METHOD, Arrays.toString(result));
        return result;
    }

    /**
     * Determines if the specified string matches a version range.
     *
     * @param range the range string
     * @return  true if the string is an actual range, false otherwise
     */
    public static boolean isRange(String range) {
        boolean result = false;
        if (!StringUtils.isEmpty(range)) {
            Matcher matcher = VERSION_RANGE_REGEX.matcher(range);
            result = matcher.matches();
        }
        return result;
    }

    /**
     * Determine if the specified string matches a single version.
     *
     * @param version the version string
     * @return  true if the string is a single version, false otherwise
     */
    public static boolean isVersion(String version) {
        boolean result = false;
        if (!StringUtils.isEmpty(version)) {
            Matcher matcher = VERSION_REGEX.matcher(version);
            result = matcher.matches();
        }
        return result;
    }

    private static int parseVersionElement(String element, String version) throws VersionException {
        final String METHOD = "parseVersionElement";

        int result;
        try {
            result = Integer.parseInt(element);
        } catch (NumberFormatException nfe) {
            VersionException ve = new VersionException("WLSDPLY-08217", nfe, element, version);
            LOGGER.throwing(CLASS, METHOD, ve);
            throw ve;
        }
        return result;
    }
}
