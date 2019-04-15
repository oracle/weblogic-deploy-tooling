@ECHO OFF
@rem **************************************************************************
@rem injectVariables.cmd
@rem
@rem Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
@rem The Universal Permissive License (UPL), Version 1.0
@rem
@rem     NAME
@rem       injectVariables.cmd - Inject variables into the model.
@rem
@rem     DESCRIPTION
@rem        This script will inject variable tokens into the model and persist the variables to the
@rem        indicated variable file. This can be run against a model that has injected variables. Any
@rem        injected variables will not be replaced. If the existing variable file was provided, the
@rem        new injected variables will be appended to the file.
@rem
@rem
@rem
@rem This script uses the following command-line arguments directly, the rest
@rem of the arguments are passed down to the underlying python program:
@rem
@rem     - -oracle_home        The directory of the existing Oracle Home to use.
@rem                           This directory must exist and it is the caller^'s
@rem                           responsibility to verify that it does. This
@rem                           argument is required.
@rem
@rem     - -domain_type        The type of domain to create. This argument is
@rem                           is optional.  If not specified, it defaults to WLS.
@rem
@rem     - -wlst_path          The path to the Oracle Home product directory under
@rem                           which to find the wlst.cmd script.  This is only
@rem                           needed for pre-12.2.1 upper stack products like SOA.
@rem
@rem                           For example, for SOA 12.1.3, -wlst_path should be
@rem                           specified as %ORACLE_HOME%\soa
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

SET WLSDEPLOY_PROGRAM_NAME=injectVariables

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
  SET "JVM_VERSION=%%k"
)

IF %JVM_VERSION% LSS 7 (
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
  ECHO Required argument ORACLE_HOME not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)

@rem
@rem If the WLST_PATH_DIR is specified, validate that it contains the wlst.cmd script
@rem
IF DEFINED WLST_PATH_DIR (
  FOR %%i IN ("%WLST_PATH_DIR%") DO SET WLST_PATH_DIR=%%~fsi
  IF NOT EXIST "%WLST_PATH_DIR%" (
    ECHO WLST_PATH_DIR specified does not exist: %WLST_PATH_DIR% >&2
    SET RETURN_CODE=98
    GOTO exit_script
  )
  set "WLST=%WLST_PATH_DIR%\common\bin\wlst.cmd"
  IF NOT EXIST "%WLST%" (
    ECHO WLST executable %WLST% not found under specified WLST_PATH_DIR %WLST_PATH_DIR% >&2
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

SET LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig
SET WLST_PROPERTIES=-Dcom.oracle.cie.script.throwException=true
SET "WLST_PROPERTIES=-Djava.util.logging.config.class=%LOG_CONFIG_CLASS% %WLST_PROPERTIES%"
SET "WLST_PROPERTIES=%WLST_PROPERTIES% %WLSDEPLOY_PROPERTIES%"

IF NOT DEFINED WLSDEPLOY_LOG_PROPERTIES (
  SET WLSDEPLOY_LOG_PROPERTIES=%WLSDEPLOY_HOME%\etc\logging.properties
)
IF NOT DEFINED WLSDEPLOY_LOG_DIRECTORY (
  SET WLSDEPLOY_LOG_DIRECTORY=%WLSDEPLOY_HOME%\logs
)

ECHO JAVA_HOME = %JAVA_HOME%
ECHO WLST_EXT_CLASSPATH = %WLST_EXT_CLASSPATH%
ECHO CLASSPATH = %CLASSPATH%
ECHO WLST_PROPERTIES = %WLST_PROPERTIES%

SET PY_SCRIPTS_PATH=%WLSDEPLOY_HOME%\lib\python
ECHO %WLST% %PY_SCRIPTS_PATH%\variable_inject.py %SCRIPT_ARGS%

"%WLST%" "%PY_SCRIPTS_PATH%\variable_inject.py" %SCRIPT_ARGS%

SET RETURN_CODE=%ERRORLEVEL%
IF "%RETURN_CODE%" == "100" (
  GOTO usage
)
IF "%RETURN_CODE%" == "99" (
  GOTO usage
)
IF "%RETURN_CODE%" == "98" (
  ECHO.
  ECHO variableInjector.cmd failed due to a parameter validation error >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "2" (
  ECHO.
  ECHO variableInjector.cmd failed ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
IF "%RETURN_CODE%" == "1" (
  ECHO.
  ECHO variableInjector.cmd completed but with some issues ^(exit code = %RETURN_CODE%^) >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "0" (
  ECHO.
  ECHO variableInjector.cmd completed successfully ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
@rem Unexpected return code so just print the message and exit...
ECHO.
ECHO variableInjector.cmd failed ^(exit code = %RETURN_CODE%^) >&2
GOTO exit_script

:usage
ECHO.
ECHO Usage: %~nx0 [-help]
ECHO              -oracle_home ^<oracle-home^>
ECHO              [-model_file ^<model-file^>]
ECHO              [-archive_file ^<archive-file^>]
ECHO              [-variable_injector_file ^<variable-injector-file^>]
ECHO              [-variable_properties_file ^<variable-file^>]
ECHO              [-domain_type ^<domain-type^>]
ECHO              [-wlst_path ^<wlst-path^>]
ECHO.
ECHO     where:
ECHO         oracle-home            - the existing Oracle Home directory with the correct version for the model
ECHO.
ECHO         model-file             - the location of the model file in which variables will be injected.
ECHO                                  If not specified, the tool will look for the model
ECHO                                  in the archive file. Either the model_file or the archive_file argument
ECHO                                  must be provided.
ECHO.
ECHO         archive-file           - the path to the archive file that contains a model in which the variables
ECHO                                  will be injected. If the model-file argument is used, this argument will be
ECHO                                  ignored. The archive file must contain a valid model.
ECHO.
ECHO         variable_properties_file - the location of the property file in which to store any variable names injected
ECHO                                    into the model. If this command line argument is not specified, the variable
ECHO                                    will be located and named based on the model file or archive file name and
ECHO                                    location. If the file exists, the file will be updated with new variable values.
ECHO.
ECHO         variable-injector-file - the location of the variable injector file which contains the variable
ECHO                                  injector keywords for this model injection run. If this argument is not provided,
ECHO                                  the model_variable_injector.json file must exist in the lib directory in the
ECHO                                  WLSDEPLOY_HOME location.
ECHO.
ECHO         domain-type            - the type of domain (e.g., WLS, JRF).
ECHO                                  Used to locate wlst.cmd if wlst-path not specified
ECHO.
ECHO         wlst-path              - the Oracle Home subdirectory of the wlst.cmd
ECHO                                  script to use (e.g., ^<ORACLE_HOME^>\soa)
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
