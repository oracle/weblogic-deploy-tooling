@ECHO OFF
@rem **************************************************************************
@rem doGenerateSC.cmd
@rem
@rem Copyright (c) 2021, Oracle Corporation and/or its affiliates.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       doGenerateSC.cmd - generate a JSON file with Security Configuration Provider types
@rem
@rem     DESCRIPTION
@rem       This script connects to the admin server and collects the Security Configuration
@rem       Provider Type names that are installed by the WLS template. This JSON file is
@rem       used by the generate jobs to collect the attributes for each provider.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME             - The location of the JDK to use.  The caller must set
@rem                         this variable to a valid Java 7 (or later) JDK.
@rem
@rem TEST_HOME             - The location of the alias integration test.
@rem
@rem WLSDEPLOY_HOME        - The location of the WebLogic Deploy Tool Object.
@rem
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the WLST environment.
@rem
SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=aliases_test_generate_offline

SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

IF NOT DEFINED WLSDEPLOY_HOME (
    ECHO Required WLSDEPLOY_HOME is not set >&2
    SET RETURN_CODE=2
    GOTO exit_script
) ELSE (
  IF NOT EXIST "%WLSDEPLOY_HOME%" (
    ECHO Specified WLSDEPLOY_HOME of "%WLSDEPLOY_HOME%" does not exist >&2
    SET RETURN_CODE=2
    GOTO exit_script
  )
)
FOR %%i IN ("%WLSDEPLOY_HOME%") DO SET WLSDEPLOY_HOME=%%~fsi
IF %WLSDEPLOY_HOME:~-1%==\ SET WLSDEPLOY_HOME=%WLSDEPLOY_HOME:~0,-1%
ECHO WLSDEPLOY_HOME=%WLSDEPLOY_HOME%

IF NOT DEFINED TEST_HOME (
  SET TEST_HOME=%SCRIPT_PATH%\..
) ELSE (
  IF NOT EXIST "%TEST_HOME%" (
    ECHO Specified TEST_HOME of "%TEST_HOME%" does not exist >&2
    SET RETURN_CODE=2
    GOTO exit_script
  )
)

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
SET TESTFILES_LOCATION=
SET ADMIN_USER=
SET ADMIN_PASSWORD=
SET ADMIN_URL=

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
IF "%1" == "-domain_home" (
  SET DOMAIN_HOME=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-testfiles_path" (
  SET TESTFILES_LOCATION=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-admin_user" (
  SET ADMIN_USER=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-admin_pass" (
  SET ADMIN_PASSWORD=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-admin_url" (
  SET ADMIN_URL=%2
  SHIFT
  GOTO arg_continue
)
@REM If none of the above, unknown argument so skip it
:arg_continue
SHIFT
IF NOT "%~1" == "" (
  GOTO arg_loop
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
IF "%DOMAIN_HOME%" == "" (
  ECHO Required argument DOMAIN_HOME not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)
IF "%TESTFILES_LOCATION%" == "" (
  ECHO Required argument TESTFILES_LOCATION not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)
IF "%ADMIN_USER%" == "" (
  ECHO Required argument ADMIN_USER not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)
IF "%ADMIN_PASSWORD%" == "" (
  ECHO Required argument ADMIN_PASSWORD not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)
IF "%ADMIN_URL%" == "" (
  ECHO Required argument ADMIN_URL not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)

@rem
@rem Find the location for wlst.cmd
@rem
    SET WLST=
    IF EXIST "%ORACLE_HOME%\oracle_common\common\bin\wlst.cmd" (
        SET WLST=%ORACLE_HOME%\oracle_common\common\bin\wlst.cmd
        SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%TEST_HOME%\resources
        SET WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%TEST_HOME%\resources
        GOTO found_wlst
    )
    IF EXIST "%ORACLE_HOME%\wlserver_10.3\common\bin\wlst.cmd" (
        SET WLST=%ORACLE_HOME%\wlserver_10.3\common\bin\wlst.cmd
        SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%TEST_HOME%\resources
        GOTO found_wlst
    )
    IF EXIST "%ORACLE_HOME%\wlserver_12.1\common\bin\wlst.cmd" (
        SET WLST=%ORACLE_HOME%\wlserver_12.1\common\bin\wlst.cmd
        SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%TEST_HOME%\resources
        GOTO found_wlst
    )
    IF EXIST "%ORACLE_HOME%\wlserver\common\bin\wlst.cmd" (
        IF EXIST "%ORACLE_HOME%\wlserver\.product.properties" (
            @rem WLS 12.1.2 or WLS 12.1.3
            SET WLST=%ORACLE_HOME%\wlserver\common\bin\wlst.cmd
            SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%TEST_HOME%\resources
        )
        GOTO found_wlst
    )

    IF NOT EXIST "%WLST%" (
      ECHO Unable to locate wlst.cmd script in ORACLE_HOME %ORACLE_HOME% >&2
      EXIT /B 98
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

ECHO TEST_HOME = %TEST_HOME%
ECHO WLSDEPLOY_PROGRAM_NAME = %WLSDEPLOY_PROGRAM_NAME%
ECHO WLSDEPLOY_LOG_DIRECTORY = %WLSDEPLOY_LOG_DIRECTORY%
ECHO JAVA_HOME = %JAVA_HOME%
ECHO WLST_EXT_CLASSPATH = %WLST_EXT_CLASSPATH%
ECHO CLASSPATH = %CLASSPATH%;
ECHO WLST_PROPERTIES = %WLST_PROPERTIES%

SET PY_SCRIPTS_PATH=%TEST_HOME%\python

ECHO %WLST% "%PY_SCRIPTS_PATH%\generate_sc.py" %*

"%WLST%" "%PY_SCRIPTS_PATH%\generate_sc.py" %*
PRINT %ERRORLEVEL%
SET RETURN_CODE=%ERRORLEVEL%
ECHO ERRORLEVEL=%ERRORLEVEL%
IF "%RETURN_CODE%" == "100" (
  GOTO usage
)
IF "%RETURN_CODE%" == "1" (
  ECHO.
  ECHO doGenerateSC.cmd completed but with some issues ^(exit code = %RETURN_CODE%^) >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "0" (
  ECHO.
  ECHO doGenerateSC.cmd completed successfully ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
@rem Unexpected return code so just print the message and exit...
ECHO.
ECHO doGenerateOSC.cmd failed ^(exit code = %RETURN_CODE%^) >&2
GOTO exit_script

:usage
ECHO.
ECHO Usage: %~nx0 -oracle_home ^<oracle-home^>
ECHO              -domain_home ^<domain-home^>
ECHO              -testfiles_path ^<testfiles-path^>
ECHO              -admin_user ^<admin_user^>
ECHO              -admin_pass ^<admin_pass^>
ECHO              -admin_url ^<admin_url^>
ECHO.
ECHO     where:
ECHO         oracle-home    - the existing Oracle Home directory for the domain
ECHO.
ECHO         domain-home    - the existing Domain directory for the Oracle version
ECHO.
ECHO         testfiles-path - the location to store the generated files and reports
ECHO.
ECHO         admin-url      - the system test admin server URL
ECHO.
ECHO         admin-user     - the system test admin username
ECHO.
ECHO         admin-pass     - the system test admin password
ECHO.

:exit_script
ECHO.
ECHO RC=%RETURN_CODE%

ENDLOCAL