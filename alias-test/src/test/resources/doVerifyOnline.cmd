@ECHO OFF

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=aliases_test_verify_online

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

IF NOT DEFINED PYTHON_HOME (
  SET PYTHON_HOME=%SCRIPT_PATH%\..
) ELSE (
  IF NOT EXIST "%PYTHON_HOME%" (
    ECHO Specified PYTHON_HOME of "%PYTHON_HOME%" does not exist >&2
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

SET TESTFILES_LOCATION=
SET WLS_VERSION=

:arg_loop
IF "%1" == "-help" (
  SET RETURN_CODE=0
  GOTO usage
)
IF "%1" == "-testfiles_path" (
  SET TESTFILES_LOCATION=%2
  SHIFT
  GOTO arg_continue
)
IF "%1" == "-wls_version" (
  SET WLS_VERSION=%2
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
IF "%TESTFILES_LOCATION%" == "" (
  ECHO Required argument TESTFILES_LOCATION not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)
@rem
@rem If the WLST_PATH_DIR is specified, validate that it contains the wlst.cmd script
@rem
@rem
@rem Find the location for wlst.cmd
@rem



SET LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig
SET "WLST_PROPERTIES=-Djava.util.logging.config.class=%LOG_CONFIG_CLASS%"
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
SET PY_SCRIPTS_PATH=%TEST_HOME%\python

SET "JAVA_PROPERTIES=-Djava.util.logging.config.class=%LOG_CONFIG_CLASS%"
SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% -Dpython.cachedir.skip=true"
SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% -Dpython.path=%PYTHON_HOME%\Lib"
SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% -Dpython.console="
SET "JAVA_PROPERTIES=%JAVA_PROPERTIES% %WLSDEPLOY_PROPERTIES%"

SET CLASSPATH=%WLSDEPLOY_HOME%\lib\weblogic-deploy-core.jar;%TEST_HOME%\resources;%PYTHON_HOME%\jython.jar

@REM print the configuration, and run the script

ECHO JAVA_HOME = %JAVA_HOME%
ECHO CLASSPATH = %CLASSPATH%
ECHO JAVA_PROPERTIES = %JAVA_PROPERTIES%


ECHO ^
%JAVA_HOME%/bin/java -cp %CLASSPATH% ^
    %JAVA_PROPERTIES% ^
    org.python.util.jython ^
    "%PY_SCRIPTS_PATH%\verify_online.py" %*

%JAVA_HOME%/bin/java -cp %CLASSPATH% ^
    %JAVA_PROPERTIES% ^
    org.python.util.jython ^
    "%PY_SCRIPTS_PATH%\verify_online.py" %*

SET RETURN_CODE=%ERRORLEVEL%
IF "%RETURN_CODE%" == "100" (
  GOTO usage
)
IF "%RETURN_CODE%" == "99" (
  GOTO usage
)
IF "%RETURN_CODE%" == "98" (
  ECHO.
  ECHO doGenerateVerify.cmd failed due to a parameter validation error >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "2" (
  ECHO.
  ECHO doGenerateVerify.cmd failed ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
IF "%RETURN_CODE%" == "1" (
  ECHO.
  ECHO doGenerateVerify.cmd completed but with some issues ^(exit code = %RETURN_CODE%^) >&2
  GOTO exit_script
)
IF "%RETURN_CODE%" == "0" (
  ECHO.
  ECHO doVerifyOnline.cmd completed successfully ^(exit code = %RETURN_CODE%^)
  GOTO exit_script
)
@rem Unexpected return code so just print the message and exit...
ECHO.
ECHO doVerifyOnline.cmd failed ^(exit code = %RETURN_CODE%^) >&2
GOTO exit_script

:usage
ECHO.
ECHO Usage: %~nx0 -testfiles_path ^<testfiles-path^>
ECHO              -wls_version ^<wls-version^>
ECHO
ECHO.
ECHO     where:
ECHO         testfiles_path  - the location to store the generated files and reports
ECHO.
ECHO         wls-version     - the version of WebLogic that is being verified in string format such as 12.2.1.4.0

:exit_script
ECHO %RETURN_CODE%

ENDLOCAL
