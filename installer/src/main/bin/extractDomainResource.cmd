@ECHO OFF
@rem **************************************************************************
@rem extractDomainResource.cmd
@rem
@rem Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       extractDomainResource.cmd - Create a domain resource file for Kubernetes deployment.
@rem
@rem     DESCRIPTION
@rem       This script creates a domain resource file for Kubernetes deployment.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME            - The location of the JDK to use.  The caller must set
@rem                        this variable to a valid Java 7 (or later) JDK.
@rem
@rem WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
@rem                         If the caller sets this, the callers location will be
@rem                         honored provided it is an existing directory.
@rem                         Otherwise, the location will be calculated from the
@rem                         location of this script.
@rem
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the Java environment.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=extractDomainResource

SET SCRIPT_NAME=%~nx0
SET SCRIPT_ARGS=%*
SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

call "%SCRIPT_PATH%\shared.cmd" :checkJythonArgs %SCRIPT_ARGS%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

SET MIN_JDK_VERSION=7
if "%USE_ENCRYPTION%" == "true" (
  SET MIN_JDK_VERSION=8
)

@rem required Java version is dependent on use of encryption
call "%SCRIPT_PATH%\shared.cmd" :javaSetup %MIN_JDK_VERSION%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

call "%SCRIPT_PATH%\shared.cmd" :runJython extract_resource.py
SET RETURN_CODE=%ERRORLEVEL%

:done
set SHOW_USAGE=false
if %RETURN_CODE% == 100 set SHOW_USAGE=true
if %RETURN_CODE% == 99 set SHOW_USAGE=true
if "%SHOW_USAGE%" == "false" (
    GOTO exit_script
)

:usage
ECHO.
ECHO Usage: %SCRIPT_NAME% [-help] [-use_encryption]
ECHO              [-oracle_home ^<oracle_home^>]
ECHO              [-domain_home ^<domain_home^>]
ECHO              [-output_dir ^<output_dir^>]
ECHO              [-target ^<target^>]
ECHO              [-domain_resource_file ^<domain_resource_file^>]
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This is required unless the ORACLE_HOME environment
ECHO                           variable is set.
ECHO.
ECHO         domain_home     - the domain home directory to be used in output files.
ECHO                           This will override any value in the model.
ECHO.
ECHO         output_dir      - the location for the target output files.
ECHO.
ECHO         target          - the target output type. The default is wko.
ECHO.
ECHO         domain_resource_file - the location of the extracted domain resource file.
ECHO                                This is deprecated, use -output_dir to specify output location
ECHO.
ECHO         archive_file    - the path to the archive file to use.  If the -model_file
ECHO                           argument is not specified, the model file in this archive
ECHO                           will be used.  This can also be specified as a
ECHO                           comma-separated list of archive files.  The overlapping contents in
ECHO                           each archive take precedence over previous archives in the list.
ECHO.
ECHO         model_file      - the location of the model file to use.  This can also be specified as a
ECHO                           comma-separated list of model locations, where each successive model
ECHO                           layers on top of the previous ones.
ECHO.
ECHO         variable_file   - the location of the property file containing the values for variables used in
ECHO                           the model. This can also be specified as a comma-separated list of property files,
ECHO                           where each successive set of properties layers on top of the previous ones.
ECHO.
ECHO    The -use_encryption switch tells the program that one or more of the
ECHO    passwords in the model or variables files are encrypted.  The program will
ECHO    prompt for the decryption passphrase to use to decrypt the passwords.
ECHO    Please note that Java 8 or higher is required when using this feature.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
