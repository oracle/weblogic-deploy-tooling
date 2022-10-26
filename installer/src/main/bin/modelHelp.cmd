@ECHO OFF
@rem **************************************************************************
@rem modelHelp.cmd
@rem
@rem Copyright (c) 2020, 2022, Oracle and/or its affiliates.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       modelHelp.cmd - WLS Deploy tool to list the folders and
@rem                       attributes available at a specific location
@rem                       in the domain model.
@rem
@rem     DESCRIPTION
@rem       This script uses the alias framework to determine which attributes
@rem       and folders are available at a specific location in the model.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME             - The location of the JDK to use.  The caller must set
@rem                         this variable to a valid Java 7 (or later) JDK.
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

SET WLSDEPLOY_PROGRAM_NAME=modelHelp

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

@rem Java 7 is required, no encryption is used
call "%SCRIPT_PATH%\shared.cmd" :javaSetup 7
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

call "%SCRIPT_PATH%\shared.cmd" :runJython model_help.py
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
ECHO Usage: %SCRIPT_NAME%
ECHO         [-help]
ECHO         [-oracle_home ^<oracle_home^>]
ECHO         [-target ^<target^>]
ECHO         [-attributes_only ^| -folders_only ^| -recursive ^| -interactive]
ECHO         ^<model_path^>
ECHO.
ECHO     where:
ECHO         oracle_home - an existing Oracle Home directory.
ECHO                       This is required unless the ORACLE_HOME environment
ECHO                       variable is set.
ECHO.
ECHO         target      - target platform (wko, etc.).
ECHO                       this determines the structure of the kubernetes section.
ECHO.
ECHO         model_path  - the path to the model element to be examined.
ECHO                       the format is [^<section^>:][/^<folder^>]...
ECHO.
ECHO     model_path examples:
ECHO         resources:/JDBCSystemResource/JdbcResource
ECHO         /JDBCSystemResource/JdbcResource
ECHO         resources:
ECHO         resources
ECHO         top  (this will list the top-level section names)
ECHO.
ECHO     By default, the tool will display the folders and attributes for the
ECHO     specified model path.
ECHO.
ECHO     The -attributes_only switch will cause the tool to list only the attributes
ECHO     for the specified model path.
ECHO.
ECHO     The -folders_only switch will cause the tool to list only the folders
ECHO     for the specified model path.
ECHO.
ECHO     The -recursive switch will cause the tool to list only the folders
ECHO     for the specified model path, and recursively include the folders below
ECHO     that path.
ECHO.
ECHO     The -interactive switch will cause the tool to enter an interactive
ECHO     command line with the specified model path as your initial location.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
