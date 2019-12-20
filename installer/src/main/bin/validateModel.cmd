@ECHO OFF
@rem **************************************************************************
@rem validateModel.cmd
@rem
@rem Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       validateModel.cmd - WLS Deploy tool to validate artifacts and print usage
@rem
@rem     DESCRIPTION
@rem        This script validates the model, archive structure and print usage
@rem
@rem
@rem This script uses the following command-line arguments directly, the rest
@rem of the arguments are passed down to the underlying python program:
@rem
@rem     - -oracle_home       The directory of the existing Oracle Home to use.
@rem                          This directory must exist and it is the caller^'s
@rem                          responsibility to verify that it does. This
@rem                          argument is required.
@rem
@rem     - -wlst_path         The path to the Oracle Home product directory under
@rem                          which to find the wlst.cmd script.  This is only
@rem                          needed for pre-12.2.1 upper stack products like SOA.
@rem
@rem                          For example, for SOA 12.1.3, -wlst_path should be
@rem                          specified as %ORACLE_HOME%\soa
@rem
@rem     - -domain_type       The type of domain (e.g., WLS, JRF).
@rem                          Used to locate wlst.cmd if -wlst_path not specified
@rem
@rem The following arguments are passed down to the underlying python program:
@rem
@rem     - -print_usage       Specify the context for printing out the model structure.
@rem                          By default, the specified folder attributes and subfolder
@rem                          names are printed.  Use one of the optional control
@rem                          switches to customize the behavior.  Note that the
@rem                          control switches are mutually exclusive.
@rem
@rem     - -model_file        The location of the model file to use if not using
@rem                          the -print_usage functionality.  This can also be specified as a
@rem                          comma-separated list of model locations, where each successive model layers
@rem                          on top of the previous ones.  If not specified, the tool will look for the
@rem                          model in the archive.  If the model is not found, validation will only
@rem                          validate the artifacts provided.
@rem
@rem     - -variable_file     The location of the property file containing
@rem                          the variable values for all variables used in
@rem                          the model if not using the -print_usage functionality.
@rem                          If the variable file is not provided, validation will
@rem                          only validate the artifacts provided.
@rem
@rem     - -archive_file      The path to the archive file to use if not using the
@rem                          -print_usage functionality.  If the archive file is
@rem                          not provided, validation will only validate the
@rem                          artifacts provided.
@rem
@rem     - -target_version    The target version of WebLogic Server the tool
@rem                          should use to validate the model content.  This
@rem                          version number can be different than the version
@rem                          being used to run the tool.  If not specified, the
@rem                          tool will validate against the version being used
@rem                          to run the tool.
@rem
@rem     - -target_mode       The target WLST mode that the tool should use to
@rem                          validate the model content.  The only valid values
@rem                          are online or offline.  If not specified, the tool
@rem                          defaults to WLST offline mode.
@rem
@rem     - -method            The validation method to apply. Options: lax, strict.
@rem                          The lax method will skip validation of external model references like @@FILE@@
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
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the WLST environment.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=validateModel

SET SCRIPT_NAME=%~nx0
SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

IF NOT DEFINED WLSDEPLOY_HOME (
  SET WLSDEPLOY_HOME=%SCRIPT_PATH%\..
) ELSE (
  IF NOT EXIST "%WLSDEPLOY_HOME%" (
    ECHO Specified WLSDEPLOY_HOME of "%WLSDEPLOY_HOME%" does not exist >&2
    SET RETURN_CODE=2
    GOTO exit_script
  )
)
FOR %%i IN ("%WLSDEPLOY_HOME%") DO SET WLSDEPLOY_HOME=%%~fsi
IF %WLSDEPLOY_HOME:~-1%==\ SET WLSDEPLOY_HOME=%WLSDEPLOY_HOME:~0,-1%

@rem
@rem Make sure that the JAVA_HOME environment variable is set to point to a
@rem JDK 7 or higher JVM (and that it isn't OpenJDK).
@rem
IF NOT DEFINED JAVA_HOME (
  ECHO Please set the JAVA_HOME environment variable to point to a Java 7 installation >&2
  SET RETURN_CODE=2
  GOTO exit_script
) ELSE (
  IF NOT EXIST "%JAVA_HOME%" (
    ECHO Your JAVA_HOME environment variable to points to a non-existent directory: %JAVA_HOME% >&2
    SET RETURN_CODE=2
    GOTO exit_script
  )
)
FOR %%i IN ("%JAVA_HOME%") DO SET JAVA_HOME=%%~fsi
IF %JAVA_HOME:~-1%==\ SET JAVA_HOME=%JAVA_HOME:~0,-1%

IF EXIST %JAVA_HOME%\bin\java.exe (
  FOR %%i IN ("%JAVA_HOME%\bin\java.exe") DO SET JAVA_EXE=%%~fsi
) ELSE (
  ECHO Java executable does not exist at %JAVA_HOME%\bin\java.exe does not exist >&2
  SET RETURN_CODE=2
  GOTO exit_script
)

FOR /F %%i IN ('%JAVA_EXE% -version 2^>^&1') DO (
  IF "%%i" == "OpenJDK" (
    ECHO JAVA_HOME %JAVA_HOME% contains OpenJDK^, which is not supported >&2
    SET RETURN_CODE=2
    GOTO exit_script
  )
)

FOR /F tokens^=2-5^ delims^=.-_^" %%j IN ('%JAVA_EXE% -fullversion 2^>^&1') DO (
  SET "JVM_FULL_VERSION=%%j.%%k.%%l_%%m"
  SET "JVM_VERSION_PART_ONE=%%j"
  SET "JVM_VERSION_PART_TWO=%%k"
)

SET JVM_SUPPORTED=1
IF %JVM_VERSION_PART_ONE% LEQ 1 (
    IF %JVM_VERSION_PART_TWO% LSS 7 (
		SET JVM_SUPPORTED=0
    )
)
IF %JVM_SUPPORTED% NEQ 1 (
  ECHO You are using an unsupported JDK version %JVM_FULL_VERSION% >&2
  SET RETURN_CODE=2
  GOTO exit_script
) ELSE (
  ECHO JDK version is %JVM_FULL_VERSION%, setting JAVA_VENDOR to Sun...
  SET JAVA_VENDOR=Sun
)

@rem
@rem Check to see if no args were given and print the usage message
@rem
IF "%~1" == "" (
  SET RETURN_CODE=0
  GOTO usage
)

@rem
@rem Find the args required to determine the WLST script to run
@rem

SET ORACLE_HOME=
SET DOMAIN_TYPE=
SET WLST_PATH_DIR=

:arg_loop
IF "%1" == "-help" (
  SET RETURN_CODE=0
  GOTO usage
)
IF "%1" == "-oracle_home" (
  SET ORACLE_HOME=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-domain_type" (
  SET DOMAIN_TYPE=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-wlst_path" (
  SET WLST_PATH_DIR=%2
  SHIFT
  GOTO arg_continue
)
@REM If none of the above, unknown argument so skip it
:arg_continue
SHIFT
IF NOT "%~1" == "" (
  GOTO arg_loop
)

SET SCRIPT_ARGS=%*
@rem Default domain type if not specified
IF "%DOMAIN_TYPE%"=="" (
    SET SCRIPT_ARGS=%SCRIPT_ARGS% -domain_type WLS
)
@rem
@rem Check for values of required arguments for this script to continue.
@rem The underlying WLST script has other required arguments.
@rem
IF "%ORACLE_HOME%" == "" (
  ECHO Required argument -oracle_home not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)

@rem
@rem If the WLST_PATH_DIR is specified, validate that it contains the wlst.cmd script
@rem
IF DEFINED WLST_PATH_DIR (
  FOR %%i IN ("%WLST_PATH_DIR%") DO SET WLST_PATH_DIR=%%~fsi
  IF NOT EXIST "%WLST_PATH_DIR%" (
    ECHO Specified -wlst_path directory does not exist: %WLST_PATH_DIR% >&2
    SET RETURN_CODE=98
    GOTO exit_script
  )
  set "WLST=%WLST_PATH_DIR%\common\bin\wlst.cmd"
  IF NOT EXIST "%WLST%" (
    ECHO WLST executable %WLST% not found under -wlst_path directory %WLST_PATH_DIR% >&2
    SET RETURN_CODE=98
    GOTO exit_script
  )
  SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
  SET WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
  GOTO found_wlst
)

@rem
@rem Find the location for wlst.cmd
@rem
SET WLST=

IF EXIST "%ORACLE_HOME%\oracle_common\common\bin\wlst.cmd" (
    SET WLST=%ORACLE_HOME%\oracle_common\common\bin\wlst.cmd
    SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
    SET WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
    GOTO found_wlst
)
IF EXIST "%ORACLE_HOME%\wlserver_10.3\common\bin\wlst.cmd" (
    SET WLST=%ORACLE_HOME%\wlserver_10.3\common\bin\wlst.cmd
    SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
    GOTO found_wlst
)
IF EXIST "%ORACLE_HOME%\wlserver_12.1\common\bin\wlst.cmd" (
    SET WLST=%ORACLE_HOME%\wlserver_12.1\common\bin\wlst.cmd
    SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
    GOTO found_wlst
)
IF EXIST "%ORACLE_HOME%\wlserver\common\bin\wlst.cmd" (
    IF EXIST "%ORACLE_HOME%\wlserver\.product.properties" (
        @rem WLS 12.1.2 or WLS 12.1.3
        SET WLST=%ORACLE_HOME%\wlserver\common\bin\wlst.cmd
        SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
    )
    GOTO found_wlst
)

IF NOT EXIST "%WLST%" (
  ECHO Unable to locate wlst.cmd script in ORACLE_HOME %ORACLE_HOME% >&2
  SET RETURN_CODE=98
  GOTO exit_script
)
:found_wlst

SET ORACLE_SERVER_DIR=

IF EXIST "%ORACLE_HOME%\wlserver_10.3" (
    SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver_10.3"
    GOTO found_wlst
) ELSE IF EXIST "%ORACLE_HOME%\wlserver_12.1" (
    SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver_12.1"
) ELSE (
    SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver
)

SET LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployCustomizeLoggingConfig
SET WLSDEPLOY_LOG_HANDLER=oracle.weblogic.deploy.logging.SummaryHandler
SET WLST_PROPERTIES=-Dcom.oracle.cie.script.throwException=true
SET "WLST_PROPERTIES=-Djava.util.logging.config.class=%LOG_CONFIG_CLASS% %WLST_PROPERTIES%"
SET "WLST_PROPERTIES=-Dpython.cachedir.skip=true %WLST_PROPERTIES%"
SET "WLST_PROPERTIES=-Dpython.path=%ORACLE_SERVER_DIR%/common/wlst/modules/jython-modules.jar/Lib %WLST_PROPERTIES%"
SET "WLST_PROPERTIES=%WLST_PROPERTIES% %WLSDEPLOY_PROPERTIES%"

IF NOT DEFINED WLSDEPLOY_LOG_PROPERTIES (
  SET WLSDEPLOY_LOG_PROPERTIES=%WLSDEPLOY_HOME%\etc\logging.properties
)
IF NOT DEFINED WLSDEPLOY_LOG_DIRECTORY (
  SET WLSDEPLOY_LOG_DIRECTORY=%WLSDEPLOY_HOME%\logs
)
IF NOT DEFINED WLSDEPLOY_LOG_HANDLERS (
  SET WLSDEPLOY_LOG_HANDLERS=%WLSDEPLOY_LOG_HANDLER%
)

set CLASSPATH=%CLASSPATH%;%ORACLE_SERVER_DIR%\server\lib\weblogic.jar

ECHO JAVA_HOME = %JAVA_HOME%
ECHO WLST_EXT_CLASSPATH = %WLST_EXT_CLASSPATH%
ECHO CLASSPATH = %CLASSPATH%
ECHO WLST_PROPERTIES = %WLST_PROPERTIES%

SET PY_SCRIPTS_PATH=%WLSDEPLOY_HOME%\lib\python

ECHO ^
%JAVA_HOME%/bin/java -cp %CLASSPATH% ^
	%WLST_PROPERTIES% ^
	org.python.util.jython ^
	"%PY_SCRIPTS_PATH%\validate.py" %SCRIPT_ARGS%

%JAVA_HOME%/bin/java -cp %CLASSPATH% ^
	%WLST_PROPERTIES% ^
	org.python.util.jython ^
	"%PY_SCRIPTS_PATH%\validate.py" %SCRIPT_ARGS%

SET RETURN_CODE=%ERRORLEVEL%
IF "%RETURN_CODE%" == "100" (
  GOTO usage
)
IF "%RETURN_CODE%" == "99" (
  GOTO usage
)
IF "%RETURN_CODE%" == "98" (
  ECHO.
  ECHO validateModel.cmd failed due to a parameter validation error >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "2" (
  ECHO.
  ECHO validateModel.cmd failed ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
IF "%RETURN_CODE%" == "1" (
  ECHO.
  ECHO validateModel.cmd completed but with some issues ^(exit code = %RETURN_CODE%^) >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "0" (
  ECHO.
  ECHO validateModel.cmd completed successfully ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
@rem Unexpected return code so just print the message and exit...
ECHO.
ECHO validateModel.cmd failed ^(exit code = %RETURN_CODE%^) >&2
GOTO exit_script

:usage
ECHO.
ECHO Usage: %SCRIPT_NAME% [-help]
ECHO              -oracle_home ^<oracle_home^>
ECHO              [-print_usage ^<context^> [-attributes_only^|-folders_only^|-recursive] ]
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-target_version ^<target_version^>]
ECHO              [-target_mode ^<target_mode^>]
ECHO              [-domain_type ^<domain_type^>]
ECHO              [-wlst_path ^<wlst_path^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain
ECHO.
ECHO         context         - specify the context for printing out the model structure.
ECHO                           By default, the specified folder attributes and subfolder
ECHO                           names are printed.  Use one of the optional control
ECHO                           switches to customize the behavior.  Note that the
ECHO                           control switches are mutually exclusive.
ECHO.
ECHO         model_file      - the location of the model file to use if not using
ECHO                           the -print_usage functionality.  This can also be specified as a
ECHO                           comma-separated list of model locations, where each successive model
ECHO                           layers on top of the previous ones.
ECHO                           If not specified, the tool will look for the model in the archive.
ECHO                           If the model is not found, validation will only
ECHO                           validate the artifacts provided.
ECHO.
ECHO         variable_file   - the location of the property file containing
ECHO                           the variable values for all variables used in
ECHO                           the model if not using the -print_usage functionality.
ECHO                           If the variable file is not provided, validation will
ECHO                           only validate the artifacts provided.
ECHO.
ECHO         archive_file    - the path to the archive file to use if not using the
ECHO                           -print_usage functionality.  If the archive file is
ECHO                           not provided, validation will only validate the
ECHO                           artifacts provided.  This can also be specified as a
ECHO                           comma-separated list of archive files.  The overlapping contents in
ECHO                           each archive take precedence over previous archives in the list.
ECHO.
ECHO         target_version  - the target version of WebLogic Server the tool
ECHO                           should use to validate the model content.  This
ECHO                           version number can be different than the version
ECHO                           being used to run the tool.  If not specified, the
ECHO                           tool will validate against the version being used
ECHO                           to run the tool.
ECHO.
ECHO         target_mode     - the target WLST mode that the tool should use to
ECHO                           validate the model content.  The only valid values
ECHO                           are online or offline.  If not specified, the tool
ECHO                           defaults to WLST offline mode.
ECHO.
ECHO         domain_type     - the type of domain (e.g., WLS, JRF).
ECHO                           Used to locate wlst.cmd if -wlst_path not specified
ECHO.
ECHO         wlst_path       - the Oracle Home subdirectory of the wlst.cmd
ECHO                           script to use (e.g., ^<ORACLE_HOME^>\soa)
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
