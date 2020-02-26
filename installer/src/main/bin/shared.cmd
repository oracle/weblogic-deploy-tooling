@ECHO OFF
@rem **************************************************************************
@rem shared.cmd
@rem
@rem Copyright (c) 2020, Oracle Corporation and/or its affiliates.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       shared.cmd - shared script for use with WebLogic Deploy Tooling.
@rem
@rem     DESCRIPTION
@rem       This script contains shared functions for use with WDT scripts.
@rem

CALL %*

GOTO :ENDFUNCTIONS

:javaSetup
    @rem Make sure that the JAVA_HOME environment variable is set to point to a
    @rem JDK with the specified level or higher (and that it isn't OpenJDK).

    SET MIN_JDK_VERSION=%1

    IF NOT DEFINED JAVA_HOME (
      ECHO Please set the JAVA_HOME environment variable to point to a Java 8 installation >&2
      EXIT /B 2
    ) ELSE (
      IF NOT EXIST "%JAVA_HOME%" (
        ECHO Your JAVA_HOME environment variable to points to a non-existent directory: %JAVA_HOME% >&2
        EXIT /B 2
      )
    )
    FOR %%i IN ("%JAVA_HOME%") DO SET JAVA_HOME=%%~fsi
    IF %JAVA_HOME:~-1%==\ SET JAVA_HOME=%JAVA_HOME:~0,-1%

    IF EXIST %JAVA_HOME%\bin\java.exe (
      FOR %%i IN ("%JAVA_HOME%\bin\java.exe") DO SET JAVA_EXE=%%~fsi
    ) ELSE (
      ECHO Java executable does not exist at %JAVA_HOME%\bin\java.exe does not exist >&2
      EXIT /B 2
    )

    FOR /F %%i IN ('%JAVA_EXE% -version 2^>^&1') DO (
      IF "%%i" == "OpenJDK" (
        ECHO JAVA_HOME %JAVA_HOME% contains OpenJDK^, which is not supported >&2
        EXIT /B 2
      )
    )

    FOR /F tokens^=2-5^ delims^=.-_^" %%j IN ('%JAVA_EXE% -fullversion 2^>^&1') DO (
      SET "JVM_FULL_VERSION=%%j.%%k.%%l_%%m"
      SET "JVM_VERSION_PART_ONE=%%j"
      SET "JVM_VERSION_PART_TWO=%%k"
    )

    SET JVM_SUPPORTED=1
    IF %JVM_VERSION_PART_ONE% LEQ 1 (
        IF %JVM_VERSION_PART_TWO% LSS %MIN_JDK_VERSION% (
            SET JVM_SUPPORTED=0
            IF %JVM_VERSION_PART_TWO% LSS 7 (
                ECHO You are using an unsupported JDK version %JVM_FULL_VERSION% >&2
            ) ELSE (
                ECHO JDK version 1.8 or higher is required when using encryption >&2
            )
        )
    )

    IF %JVM_SUPPORTED% NEQ 1 (
      EXIT /B 2
    ) ELSE (
      ECHO JDK version is %JVM_FULL_VERSION%, setting JAVA_VENDOR to Sun...
      SET JAVA_VENDOR=Sun
    )
GOTO :EOF

:checkJythonArgs
    @REM verify that required arg -oracle_home is set.

    @rem if no args were given and print the usage message
    IF "%~1" == "" (
      EXIT /B 100
    )

    @rem check for -help and -oracle_home
    SET ORACLE_HOME=

    :arg_loop
    IF "%1" == "-help" (
      EXIT /B 100
    )

    IF "%1" == "-oracle_home" (
      SET ORACLE_HOME=%2
      SHIFT
      GOTO arg_continue
    )

    @REM if none of the above, skip this argument
    :arg_continue
    SHIFT
    IF NOT "%~1" == "" (
      GOTO arg_loop
    )

    @rem verify that ORACLE_HOME was set.
    IF "%ORACLE_HOME%" == "" (
      ECHO Required argument -oracle_home not provided >&2
      EXIT /B 99
    )
GOTO :EOF

:variableSetup
    @REM set up variables for WLST or Jython execution

    @REM set the WLSDEPLOY_HOME variable. if it was already set, verify that it is valid

    IF NOT DEFINED WLSDEPLOY_HOME (
      SET WLSDEPLOY_HOME=%SCRIPT_PATH%\..
    ) ELSE (
      IF NOT EXIST "%WLSDEPLOY_HOME%" (
        ECHO Specified WLSDEPLOY_HOME of "%WLSDEPLOY_HOME%" does not exist >&2
        EXIT /B 2
      )
    )
    FOR %%i IN ("%WLSDEPLOY_HOME%") DO SET WLSDEPLOY_HOME=%%~fsi
    IF %WLSDEPLOY_HOME:~-1%==\ SET WLSDEPLOY_HOME=%WLSDEPLOY_HOME:~0,-1%

    @REM set up logger configuration, see WLSDeployLoggingConfig.java

    SET LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployCustomizeLoggingConfig
    SET WLSDEPLOY_LOG_HANDLER=oracle.weblogic.deploy.logging.SummaryHandler

    IF NOT DEFINED WLSDEPLOY_LOG_PROPERTIES (
      SET WLSDEPLOY_LOG_PROPERTIES=%WLSDEPLOY_HOME%\etc\logging.properties
    )
    IF NOT DEFINED WLSDEPLOY_LOG_DIRECTORY (
      SET WLSDEPLOY_LOG_DIRECTORY=%WLSDEPLOY_HOME%\logs
    )
    IF NOT DEFINED WLSDEPLOY_LOG_HANDLERS (
      SET WLSDEPLOY_LOG_HANDLERS=%WLSDEPLOY_LOG_HANDLER%
    )
GOTO :EOF

:runJython
    @REM run a jython script, without WLST.
    SET JYTHON_SCRIPT=%1

    @REM set up Oracle directory, logger, classpath

    SET ORACLE_SERVER_DIR=
    IF EXIST "%ORACLE_HOME%\wlserver_10.3" (
        SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver_10.3"
    ) ELSE IF EXIST "%ORACLE_HOME%\wlserver_12.1" (
        SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver_12.1"
    ) ELSE (
        SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver
    )

    CALL :variableSetup
    if %ERRORLEVEL% NEQ 0 (
        EXIT /B %ERRORLEVEL%
    )

    SET "JAVA_PROPERTIES=-Djava.util.logging.config.class=%LOG_CONFIG_CLASS%"
    SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% -Dpython.cachedir.skip=true"
    SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% -Dpython.path=%ORACLE_SERVER_DIR%/common/wlst/modules/jython-modules.jar/Lib"
    SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% -Dpython.console="
    SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% %WLSDEPLOY_PROPERTIES%"

    SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
    SET CLASSPATH=%CLASSPATH%;%ORACLE_SERVER_DIR%\server\lib\weblogic.jar

    @REM print the configuration, and run the script

    ECHO JAVA_HOME = %JAVA_HOME%
    ECHO CLASSPATH = %CLASSPATH%
    ECHO JAVA_PROPERTIES = %JAVA_PROPERTIES%

    SET PY_SCRIPTS_PATH=%WLSDEPLOY_HOME%\lib\python

    ECHO ^
    %JAVA_HOME%/bin/java -cp %CLASSPATH% ^
        %JAVA_PROPERTIES% ^
        org.python.util.jython ^
        "%PY_SCRIPTS_PATH%\%JYTHON_SCRIPT%" %SCRIPT_ARGS%

    %JAVA_HOME%/bin/java -cp %CLASSPATH% ^
        %JAVA_PROPERTIES% ^
        org.python.util.jython ^
        "%PY_SCRIPTS_PATH%\%JYTHON_SCRIPT%" %SCRIPT_ARGS%

    call :checkExitCode %ERRORLEVEL%
    EXIT /B %ERRORLEVEL%
GOTO :EOF

:checkExitCode
    @REM print a message for the exit code passed in.
    @REM calling script must have assigned the SCRIPT_NAME variable.

    SET RETURN_CODE=%1

    IF "%RETURN_CODE%" == "103" (
      ECHO.
      ECHO %SCRIPT_NAME% completed successfully but the domain requires a restart for the changes to take effect ^(exit code = %RETURN_CODE%^)
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "102" (
      ECHO.
      ECHO %SCRIPT_NAME% completed successfully but the effected servers require a restart ^(exit code = %RETURN_CODE%^)
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "101" (
      ECHO.
      ECHO %SCRIPT_NAME% was unable to complete due to configuration changes that require a domain restart.  Please restart the domain and re-invoke the %SCRIPT_NAME% script with the same arguments ^(exit code = %RETURN_CODE%^)
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "100" (
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "99" (
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "98" (
      ECHO.
      ECHO %SCRIPT_NAME% failed due to a parameter validation error >&2
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "2" (
      ECHO.
      ECHO %SCRIPT_NAME% failed ^(exit code = %RETURN_CODE%^)
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "1" (
      ECHO.
      ECHO %SCRIPT_NAME% completed but with some issues ^(exit code = %RETURN_CODE%^) >&2
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "0" (
      ECHO.
      ECHO %SCRIPT_NAME% completed successfully ^(exit code = %RETURN_CODE%^)
      EXIT /B %RETURN_CODE%
    )
    @REM Unexpected return code so just print the message and exit...
    ECHO.
    ECHO %SCRIPT_NAME% failed ^(exit code = %RETURN_CODE%^) >&2
    EXIT /B %RETURN_CODE%
GOTO :EOF

:ENDFUNCTIONS
