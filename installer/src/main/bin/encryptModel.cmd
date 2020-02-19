@ECHO OFF
@rem **************************************************************************
@rem encryptModel.cmd
@rem
@rem Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       encryptModel.cmd - WLS Deploy tool to encrypt the password fields in
@rem                          the model and any referenced variables.
@rem
@rem     DESCRIPTION
@rem       This script searches the model file and variable file, if provided,
@rem       looking for password fields and encrypts them using the supplied
@rem       passphrase.  This passphrase must be passed to other tools in
@rem       order for them to be able to decrypt the passwords.  Please note
@rem       this feature requires JDK 1.8 or higher due to the encryption
@rem       algorithms selected.
@rem
@rem
@rem This script uses the following command-line arguments directly, the rest
@rem of the arguments are passed down to the underlying python program:
@rem   -oracle_home
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
@rem JAVA_PROPERTIES       - Extra system properties to pass to Java.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the Java environment.
@rem
SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=encryptModel

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

@rem Java 8 is required for encryption library
call "%SCRIPT_PATH%\shared.cmd" :javaSetup 8
if %ERRORLEVEL% NEQ 0 (
  GOTO exit_script
)

@rem
@rem Check to see if no args were given and print the usage message
@rem
IF "%~1" == "" (
  SET RETURN_CODE=0
  GOTO usage
)

@rem
@rem Find the args required to determine the tool script to run
@rem

SET ORACLE_HOME=

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
@REM If none of the above, unknown argument so skip it
:arg_continue
SHIFT
IF NOT "%~1" == "" (
  GOTO arg_loop
)

SET SCRIPT_ARGS=%*

@rem
@rem Check for values of required arguments for this script to continue.
@rem The underlying tool script has other required arguments.
@rem
IF "%ORACLE_HOME%" == "" (
  ECHO Required argument -oracle_home not provided >&2
  SET RETURN_CODE=99
  GOTO usage
)

call "%SCRIPT_PATH%\shared.cmd" :jythonSetup

ECHO JAVA_HOME = %JAVA_HOME%
ECHO CLASSPATH = %CLASSPATH%
ECHO JAVA_PROPERTIES = %JAVA_PROPERTIES%

SET PY_SCRIPTS_PATH=%WLSDEPLOY_HOME%\lib\python

ECHO ^
%JAVA_HOME%/bin/java -cp %CLASSPATH% ^
	%JAVA_PROPERTIES% ^
	org.python.util.jython ^
	"%PY_SCRIPTS_PATH%\encrypt.py" %SCRIPT_ARGS%

%JAVA_HOME%/bin/java -cp %CLASSPATH% ^
	%JAVA_PROPERTIES% ^
	org.python.util.jython ^
	"%PY_SCRIPTS_PATH%\encrypt.py" %SCRIPT_ARGS%

SET RETURN_CODE=%ERRORLEVEL%
call "%SCRIPT_PATH%\shared.cmd" :checkExitCode %RETURN_CODE%
if %ERRORLEVEL% EQU 0 (
  GOTO exit_script
)

:usage
ECHO.
ECHO Usage: %SCRIPT_NAME% [-help] [-manual]
ECHO              -oracle_home ^<oracle_home^>
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO.
ECHO         model_file      - the location of the model file to use.
ECHO.
ECHO         variable_file   - the location of the property file containing
ECHO                           the variable values for all variables used in
ECHO                           the model.
ECHO.
ECHO     The -manual switch can be used to run the tool without a model and get
ECHO     the encrypted value for a single password.
ECHO.
ECHO     NOTE: The encryption feature requires the use of JDK version 1.8 or higher.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
