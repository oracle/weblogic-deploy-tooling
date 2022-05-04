/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.logging.WLSDeployLoggingConfig;

/**
 * This class provides the ability to run an external program.
 */
public class ScriptRunner {
    private static final String CLASS = ScriptRunner.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    private static final boolean WINDOWS = File.separatorChar == '\\';
    private static final String OUT_FILE_NAME_TEMPLATE = "{0}.out";

    private Map<String, String> env;
    private List<String> stdoutBuffer;
    private File stdoutFile;
    private String stdoutLogBaseName;

    /**
     * The constructor.
     *
     * @param env the map of environment variables to use for executing the external program
     * @param stdoutBaseFileName the base name to use for logging the stdout of the external program
     */
    public ScriptRunner(Map<String, String> env, String stdoutBaseFileName) {
        this.stdoutLogBaseName = stdoutBaseFileName;
        this.env = new HashMap<>(env);
    }

    /**
     * Run the external program.
     *
     * @param scriptToRun the executable program to run
     * @param linesToPipeToStdout an optional list of lines to write to the external program's standard input
     * @param args the arguments to pass to the external program on the command-line
     * @return the exit code of the external program
     * @throws ScriptRunnerException if argument validation error or error running the external program occurs
     */
    public int executeScript(File scriptToRun, List<String> linesToPipeToStdout, String... args)
            throws ScriptRunnerException{
        return executeScript(scriptToRun,false, linesToPipeToStdout, args);
    }

    /**
     * Run the external program.
     *
     * @param scriptToRun the executable program to run
     * @param appendFlag flag indicating if stdout file should be appended to
     * @param linesToPipeToStdout an optional list of lines to write to the external program's standard input
     * @param args the arguments to pass to the external program on the command-line
     * @return the exit code of the external program
     * @throws ScriptRunnerException if argument validation error or error running the external program occurs
     */
    public int executeScript(File scriptToRun, boolean appendFlag, List<String> linesToPipeToStdout, String... args)
        throws ScriptRunnerException{
        final String METHOD = "executeScript";

        LOGGER.entering(CLASS, METHOD, scriptToRun, args);
        File cwd = FileUtils.getCanonicalFile(new File(System.getProperty("user.dir")));
        stdoutFile = getStdoutFile(stdoutLogBaseName);
        String[] command = getCommandStringArray(scriptToRun, args);

        ProcessHandler processHandler = new ProcessHandler(command, cwd);
        processHandler.setStdoutLog(stdoutFile, appendFlag);
        processHandler.setBufferStdout();

        for (Map.Entry<String, String> envEntry : env.entrySet()) {
            String key = envEntry.getKey();
            String val = envEntry.getValue();
            processHandler.setEnvironmentVariable(key, val);
        }

        processHandler.registerWaitHandler(new ProcessHandler.WaitHandler() {
            public boolean isWaitComplete() {
                return false;
            }

            public boolean processTimeout(Process process) {
                return false;
            }

            public void processExit(Process process) {
                // nothing to do
            }
        });

        LOGGER.info("WLSDPLY-01300", scriptToRun.getName(), processHandler);
        LOGGER.info("WLSDPLY-01301", scriptToRun.getName(), stdoutFile.getAbsolutePath());
        processHandler.exec(linesToPipeToStdout);
        int exitCode = processHandler.getExitCode();
        stdoutBuffer = processHandler.getStdoutBuffer();
        LOGGER.exiting(CLASS, METHOD, exitCode);
        return exitCode;
    }

    /**
     * Get the buffer containing the lines of output from the external program's standard output.
     *
     * @return the lines of output
     */
    public List<String> getStdoutBuffer() {
        return new ArrayList<>(stdoutBuffer);
    }

    /**
     * Get the name of the stdout log file used to write the external program's standard output.
     *
     * @return the file name
     */
    public String getStdoutFileName() {
        String result = "";
        if (stdoutFile != null) {
            result = stdoutFile.getAbsolutePath();
        }
        return result;
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private Helper Methods                                                //
    ///////////////////////////////////////////////////////////////////////////

    private static String[] getShellInterpretorCmd() {
        String[] command = new String[2];

        if (WINDOWS) {
            String comSpec = System.getenv("ComSpec");
            if (StringUtils.isEmpty(comSpec)) {
                String str = System.getenv("PATH");
                String[] envPath = str.split(File.pathSeparator);
                for (String s : envPath) {
                    File file = new File(s, "cmd.exe");
                    if (file.exists()) {
                        command[0] = transformString(s + File.separatorChar + "cmd.exe");
                        break;
                    }
                }
            } else {
                command[0] = comSpec;
            }
            command[1] = "/c";
        } else {
            String shell = System.getenv("SHELL");
            if (StringUtils.isEmpty(shell)) {
                String str = System.getenv("PATH");
                String[] envPath = str.split(File.pathSeparator);
                for (String s : envPath) {
                    File file = new File(s, "sh");
                    if (file.exists()) {
                        command[0] = file.getAbsolutePath();
                        command[1] = "-c";
                        return command;
                    }
                }
            } else {
                command[0] = shell;
                command[1] = "-c";
                return command;
            }
        }
        return command;
    }

    private static String[] getCommandStringArray(File scriptToRun, String...args) {
        String[] shell = getShellInterpretorCmd();
        String[] command;
        if (WINDOWS) {
            command = new String[shell.length + 1 + args.length];
            System.arraycopy(shell, 0, command, 0, shell.length);
            int idx = shell.length;
            command[idx] = scriptToRun.getAbsolutePath();
            idx++;
            System.arraycopy(args, 0, command, idx, args.length);
        } else {
            // Have to concatenate the args and the script to execute into
            // a single string so that bash -c will not strip off the args.
            //
            StringBuilder scriptCommand = new StringBuilder();
            scriptCommand.append(scriptToRun.getAbsolutePath());
            for (String arg : args) {
                scriptCommand.append(' ');
                scriptCommand.append(arg);
            }

            command = new String[shell.length + 1];
            System.arraycopy(shell, 0, command, 0, shell.length);
            command[shell.length] = scriptCommand.toString();
        }
        return command;
    }

    private static String transformString(String str) {
        return str.replace("\\", "\\\\");
    }

    private static File getStdoutFile(String logFileBaseName) {
        final String METHOD = "getStdoutFile";

        LOGGER.entering(CLASS, METHOD, logFileBaseName);
        String stdoutFileName = MessageFormat.format(OUT_FILE_NAME_TEMPLATE, logFileBaseName);
        File standardOutFile =
            FileUtils.getCanonicalFile(new File(WLSDeployLoggingConfig.getLoggingDirectory(), stdoutFileName));
        LOGGER.exiting(CLASS, METHOD, standardOutFile);
        return standardOutFile;
    }
}
