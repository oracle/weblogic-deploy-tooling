@ECHO OFF
@rem **************************************************************************
@rem shared.cmd
@rem
@rem Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
      ECHO Java executable does not exist at %JAVA_HOME%\bin\java.exe >&2
      EXIT /B 2
    )

    SET OPEN_JDK=false
    SET ORACLE_ONE=0
    SET ORACLE_TWO=0
    FOR /F "tokens=1,5" %%x IN ('%JAVA_EXE% -version 2^>^&1') DO (
        IF "%%x" == "OpenJDK" (
            SET OPEN_JDK=true
            IF EXIST %ORACLE_HOME%\wlserver\server\lib\weblogic.jar (
                FOR /F "tokens=1-3 delims= " %%A IN ('%JAVA_EXE% -cp %ORACLE_HOME%\wlserver\server\lib\weblogic.jar weblogic.version 2^>^&1') DO (
                    IF "%%A" == "WebLogic" (
                        FOR /F "tokens=1-5 delims=." %%j IN ('ECHO %%C') DO (
                            SET "ORACLE_VERSION=%%j.%%k.%%l.%%m.%%n"
                            SET "ORACLE_ONE=%%j"
                            SET "ORACLE_TWO=%%l"
                        )
                    )
                )
                SET GRAALVM=false
                IF "%%y" == "GraalVM" SET GRAALVM=true
            ) ELSE (
                  ECHO JAVA_HOME %JAVA_HOME% contains OpenJDK^, which is not supported >&2
                  EXIT /B 2
            )
        )
    )

    SET NOT_VALID=false
    IF "%OPEN_JDK%"=="true" (
        IF "%GRAALVM%"=="false" SET NOT_VALID=true
        IF %ORACLE_ONE% LSS 14 (
            SET NOT_VALID=true
        ) ELSE IF %ORACLE_ONE% EQU 14 IF %ORACLE_TWO% LSS 2 SET NOT_VALID=true
        SET JAVA_VENDOR=GraalVM
    )

    IF "%NOT_VALID%"=="true" (
        IF "%GRAALVM%"=="true" (
            SET ORACLE_VERSION
            ECHO JAVA_HOME %JAVA_HOME% contains GraalVM OpenJDK^, which is not supported in versions before 14.1.2 >&2
            EXIT /B 2
        )
        ECHO JAVA_HOME %JAVA_HOME% contains OpenJDK^, which is not supported. >&2
        EXIT /B 2
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
      IF "%JAVA_VENDOR%"=="" SET JAVA_VENDOR=Sun
    )
GOTO :EOF

:checkArgs
:checkJythonArgs
    @REM verify -oracle_home is provided, or ORACLE_HOME is set.
    @REM if -help is provided, return usage exit code.
    @REM if -use_encryption is provided, set USE_ENCRYPTION to true
    @REM if -wlst_path is provided, set WLST_PATH_DIR

    @rem if no args were given and print the usage message
    IF "%~1" == "" (
      EXIT /B 100
    )

    SET ORACLE_HOME_ARG=
    SET WLST_PATH_DIR=

    :arg_loop
    set firstArg=%1

    @REM remove any double quotes (replace with empty string)
    set firstArg=%firstArg:"=%

    IF "%firstArg%" == "-help" (
      EXIT /B 100
    )

    IF "%firstArg%" == "-oracle_home" (
      SET ORACLE_HOME_ARG=%2
      SHIFT
      GOTO arg_continue
    )

    IF "%firstArg%" == "-use_encryption" (
      SET USE_ENCRYPTION=true
      GOTO arg_continue
    )

    IF "%firstArg%" == "-wlst_path" (
      SET WLST_PATH_DIR=%2
      SHIFT
      GOTO arg_continue
    )

    @REM if none of the above, skip this argument
    :arg_continue
    SHIFT
    IF NOT "%~1" == "" (
      GOTO arg_loop
    )

    IF NOT "%ORACLE_HOME_ARG%" == "" (
      SET ORACLE_HOME=%ORACLE_HOME_ARG%
    ) ELSE (
      @REM if -oracle_home argument was not found, but ORACLE_HOME was set in environment,
      @REM add the -oracle_home argument with the environment value.
      @REM put it at the beginning to protect trailing arguments.

      IF NOT "%ORACLE_HOME%" == "" (
        SET SCRIPT_ARGS= -oracle_home %ORACLE_HOME% %SCRIPT_ARGS%
      )
    )

    @rem verify that ORACLE_HOME was set.
    IF "%ORACLE_HOME%" == "" (
      ECHO -oracle_home not provided, and ORACLE_HOME not set >&2
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

    SET LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig

    IF NOT DEFINED WLSDEPLOY_LOG_PROPERTIES (
      SET WLSDEPLOY_LOG_PROPERTIES=%WLSDEPLOY_HOME%\etc\logging.properties
    )
    IF NOT DEFINED WLSDEPLOY_LOG_DIRECTORY (
      SET WLSDEPLOY_LOG_DIRECTORY=%WLSDEPLOY_HOME%\logs
    )
GOTO :EOF

:runWlst
    @REM run a WLST script.
    SET WLST_SCRIPT=%1

    CALL :variableSetup
    if %ERRORLEVEL% NEQ 0 (
        EXIT /B %ERRORLEVEL%
    )

    @rem set WLST variable to the WLST executable.
    @rem set CLASSPATH and WLST_CLASSPATH to include the WDT core JAR file.
    @rem if the WLST_PATH_DIR was set, verify and use that value.

    IF DEFINED WLST_PATH_DIR (
      FOR %%i IN ("%WLST_PATH_DIR%") DO SET WLST_PATH_DIR=%%~fsi
      IF NOT EXIST "%WLST_PATH_DIR%" (
        ECHO Specified -wlst_path directory does not exist: %WLST_PATH_DIR% >&2
        EXIT /B 98
      )
      set "WLST=%WLST_PATH_DIR%\common\bin\wlst.cmd"
      IF NOT EXIST "%WLST%" (
        SETLOCAL enabledelayedexpansion
        ECHO WLST executable !WLST! not found under -wlst_path directory %WLST_PATH_DIR% >&2
        EXIT /B 98
      )
      SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
      IF DEFINED WLST_EXT_CLASSPATH (
        SET "WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%WLST_EXT_CLASSPATH%"
      ) ELSE (
        SET "WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar"
      )
      GOTO found_wlst
    )

    @rem if WLST_PATH_DIR was not set, find the WLST executable in one of the known ORACLE_HOME locations.

    SET WLST=
    IF EXIST "%ORACLE_HOME%\oracle_common\common\bin\wlst.cmd" (
        SET WLST=%ORACLE_HOME%\oracle_common\common\bin\wlst.cmd
        SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar
        IF DEFINED WLST_EXT_CLASSPATH (
          SET "WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%WLST_EXT_CLASSPATH%"
        ) ELSE (
          SET "WLST_EXT_CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar"
        )
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
      EXIT /B 98
    )
    :found_wlst

    SET "WLST_PROPERTIES=-Dcom.oracle.cie.script.throwException=true"
    SET "WLST_PROPERTIES=%WLST_PROPERTIES% -Djava.util.logging.config.class=%LOG_CONFIG_CLASS%"
    SET "WLST_PROPERTIES=%WLST_PROPERTIES% %WLSDEPLOY_PROPERTIES%"

    @REM print the configuration, and run the script

    ECHO JAVA_HOME = %JAVA_HOME%
    ECHO WLST_EXT_CLASSPATH = %WLST_EXT_CLASSPATH%
    ECHO CLASSPATH = %CLASSPATH%
    ECHO WLST_PROPERTIES = %WLST_PROPERTIES%

    SET PY_SCRIPTS_PATH=%WLSDEPLOY_HOME%\lib\python

    ECHO %WLST% %PY_SCRIPTS_PATH%\%WLST_SCRIPT% %SCRIPT_ARGS%

    CALL "%WLST%" "%PY_SCRIPTS_PATH%\%WLST_SCRIPT%" %SCRIPT_ARGS%

    call :checkExitCode %ERRORLEVEL%
    EXIT /B %ERRORLEVEL%
GOTO :EOF

:runJython
    @REM run a jython script, without WLST.
    SET JYTHON_SCRIPT=%1

    @REM set up Oracle directory, logger, classpath

    SET ORACLE_SERVER_DIR=
    IF EXIST "%ORACLE_HOME%\wlserver_10.3" (
        SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver_10.3
    ) ELSE IF EXIST "%ORACLE_HOME%\wlserver_12.1" (
        SET ORACLE_SERVER_DIR=%ORACLE_HOME%\wlserver_12.1
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

    IF "%RETURN_CODE%" == "104" (
      ECHO.
      ECHO %SCRIPT_NAME% completed successfully but the domain changes have been canceled because -cancel_changes_if_restart_required is specified  ^(exit code = %RETURN_CODE%^)
      EXIT /B %RETURN_CODE%
    )
    IF "%RETURN_CODE%" == "103" (
      ECHO.
      ECHO %SCRIPT_NAME% completed successfully but the domain requires a restart for the changes to take effect ^(exit code = %RETURN_CODE%^)
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
