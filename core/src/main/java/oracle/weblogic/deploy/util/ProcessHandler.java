/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * This class is used to configure and run external, out-of-process programs and interact with them.
 */
public class ProcessHandler {
    private static final String CLASS = ProcessHandler.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    private static final long POLL_INTERVAL = 1000L;
    private static final int MILLIS_PER_SECOND = 1000;
    private static final Charset DEFAULT_CHARSET = Charset.defaultCharset();

    private final ProcessBuilder procBuilder;
    private Process process;
    private File logFile;
    private boolean appendFlag = false;
    private PrintStream stdoutWriter;
    private int timeout = -1;
    private WaitHandler waitHandler;
    private List<String> stdoutBuffer;

    /**
     * The constructor.
     *
     * @param cmd the command and its arguments
     * @param workingDir the working directory from which to run the command
     */
    public ProcessHandler(String[] cmd, File workingDir) {
        procBuilder = new ProcessBuilder();
        procBuilder.command(cmd);
        procBuilder.directory(workingDir);
        procBuilder.redirectErrorStream(true);
    }

    /**
     * Set the file to which standard out of the process should be written.
     *
     * @param log the stdout log file
     */
    public void setStdoutLog(File log) {
        setStdoutLog(log, false);
    }

    /**
     * Set the log that standard out of process will be written to, using
     * the specified append flag. The default is to not append to <code>log</code>.
     *
     * @param log the stdout log file
     * @param appendFlag flag indicating if file should be appended to
     */
    public void setStdoutLog(File log, boolean appendFlag) {
        this.logFile = log;
        this.appendFlag = appendFlag;
    }

    /**
     * Set the buffering of the standard output of the process for retrieval by this process.
     * Note that this will clear any previously buffered standard output.
     */
    public void setBufferStdout() {
        stdoutBuffer = new ArrayList<>();
    }

    /**
     * Get the buffered standard output of the process.
     *
     * @return the buffered standard output of the process
     */
    public List<String> getStdoutBuffer() {
        return stdoutBuffer;
    }

    /**
     * Set the echoing of the standard output of the process to standard out of this process.
     */
    public void setEchoStdoutToStdout() {
        stdoutWriter = System.out;
    }

    /**
     * Set the time to wait for the process to complete.  The default is -1, which means no timeout.
     *
     * @param timeout the number of seconds to wait for the process to complete
     */
    public void setTimeoutSecs(int timeout) {
        this.timeout = timeout * MILLIS_PER_SECOND;
    }

    /**
     * Register the wait handler to use with the process.  This field must be set prior to calling exec().
     *
     * @param handler the wait handler to use with the process
     */
    public void registerWaitHandler(WaitHandler handler) {
        this.waitHandler = handler;
    }

    /**
     * Empty the environment of this process handler.
     */
    public void clearEnv() {
        procBuilder.environment().clear();
    }

    /**
     * Add the environment variable to the environment only if it is not already set.
     *
     * @param name environment variable name
     * @param value environment variable value
     * @return whether or not the environment variable was added
     */
    public boolean addEnvironmentVariableIfNotSet(String name, String value) {
        Map<String, String> env = procBuilder.environment();
        if (env.get(name) != null) {
            return false;
        }
        env.put(name, value);
        return true;
    }

    /**
     * Set the environment variable to the specified value.
     *
     * @param name environment variable name
     * @param value environment variable value
     */
    public void setEnvironmentVariable(String name, String value) {
        procBuilder.environment().put(name, value);
    }

    /**
     * Determines if the child process is still running.
     *
     * @return true if the process is still running; false otherwise
     */
    public boolean isRunning() {
        if (process == null) {
            return false;
        }
        try {
            process.exitValue();
            return false;
        } catch (IllegalThreadStateException ignore) {
            LOGGER.finest("WLSDPLY-01200", ignore, this.toString(), ignore.getLocalizedMessage());
            return true;
        }
    }

    /**
     * Get the process exit code.
     *
     * @return the exit code of the process
     */
    public int getExitCode() {
        return process.exitValue();
    }

    /**
     * Kill the process.
     */
    public void kill() {
        process.destroy();
    }

    /**
     * Execute the process.
     *
     * @throws ScriptRunnerException if an error occurs while running or handling the child process
     */
    public void exec() throws ScriptRunnerException {
        exec(null);
    }

    /**
     * Execute the process and write the specified lines to standard input of the process.
     *
     * @param linesToPipeToStdin lines to write to standard input of the process
     * @throws ScriptRunnerException if an error occurs while running or handling the child process
     */
    public void exec(List<String> linesToPipeToStdin) throws ScriptRunnerException {
        final String METHOD = "exec";

        // Don't log the list since it contains passwords.
        LOGGER.entering(CLASS, METHOD);

        if (waitHandler == null) {
            ScriptRunnerException sre = new ScriptRunnerException("WLSDPLY-01201", this.toString());
            LOGGER.throwing(CLASS, METHOD, sre);
            throw sre;
        }

        Thread drainerThread = new Thread(new DrainerThread(procBuilder.command()));
        drainerThread.setDaemon(true);
        long beginTime = System.currentTimeMillis();
        LOGGER.info("WLSDPLY-01202", this.toString());
        try {
            process = procBuilder.start();
        } catch (IOException ioe) {
            ScriptRunnerException sre =
                new ScriptRunnerException("WLSDPLY-01203", ioe, this.toString(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, sre);
            throw sre;
        }

        if (linesToPipeToStdin != null && !linesToPipeToStdin.isEmpty()) {
            try (BufferedWriter writer =
                new BufferedWriter(new OutputStreamWriter(process.getOutputStream(), DEFAULT_CHARSET))) {

                for (String line : linesToPipeToStdin) {
                    writer.write(line);
                    writer.newLine();
                }
            } catch (IOException ioe) {
                ScriptRunnerException sre =
                    new ScriptRunnerException("WLSDPLY-01204", ioe, this.toString(), ioe.getLocalizedMessage());
                LOGGER.throwing(CLASS, METHOD, sre);
                throw sre;
            }
        }
        drainerThread.start();

        try {
            while (true) {
                if (waitHandler.isWaitComplete()) {
                    return;
                }
                if (!isRunning()) {
                    waitHandler.processExit(process);
                    return;
                }
                Thread.sleep(POLL_INTERVAL);
                long elapsed = System.currentTimeMillis() - beginTime;
                if (timeout > 0 && elapsed > timeout) {
                    if (!waitHandler.processTimeout(process)) {
                        process.destroy();
                    }
                    ScriptRunnerException sre =
                        new ScriptRunnerException("WLSDPLY-01205", this.toString(), elapsed, timeout);
                    LOGGER.throwing(CLASS, METHOD, sre);
                    throw sre;
                }
            }
        } catch (InterruptedException e) {
            LOGGER.fine("WLSDPLY-01206", e, this.toString(), e.getLocalizedMessage());
            Thread.currentThread().interrupt();
        }
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public String toString() {
        return "[cmd:" + procBuilder.command() + "]";
    }

    /**
     * Internal class for draining stdout from the child process.
     */
    private final class DrainerThread implements Runnable {
        private List<String> command;

        private DrainerThread(List<String> command) {
            this.command = new ArrayList<>(command);
        }

        /**
         * {@inheritDoc}
         */
        @Override
        public String toString() {
            StringBuilder builder = new StringBuilder();
            for (String element : command) {
                builder.append(element);
                builder.append(' ');
            }
            return builder.toString().trim();
        }

        /**
         * {@inheritDoc}
         */
        @Override
        public void run() {
            PrintStream logWriter = null;
            try (BufferedReader reader =
                new BufferedReader(new InputStreamReader(process.getInputStream(), DEFAULT_CHARSET))) {

                if (logFile != null) {
                    FileOutputStream fos = new FileOutputStream(logFile, appendFlag);
                    logWriter = new PrintStream(fos, true, StandardCharsets.UTF_8.toString());
                }

                String msg;
                boolean logToLog = (logWriter == null && stdoutWriter == null && stdoutBuffer == null);
                while ((msg = reader.readLine()) != null) {
                    if (logWriter != null) {
                        logWriter.println(msg);
                        logWriter.flush();
                    }
                    if (stdoutWriter != null) {
                        stdoutWriter.println(msg);
                        stdoutWriter.flush();
                    }
                    if (stdoutBuffer != null) {
                        stdoutBuffer.add(msg);
                    }
                    if (logToLog) {
                        LOGGER.fine("WLSDPLY-01207", this.toString(), msg);
                    }
                }
            } catch (IOException ioe) {
                LOGGER.severe("WLSDPLY-01208", ioe, this.toString(), ioe.getLocalizedMessage());
            } finally {
                if (logWriter != null) {
                    logWriter.close();
                }
            }
        }
    }

    /**
     * The WaitHandler interface that must be implemented to use the ProcessHandler.
     */
    public interface WaitHandler {
        /**
         * Determines if the wait is complete or not.
         *
         * @return true if the wait is complete; false otherwise
         */
        boolean isWaitComplete();

        /**
         * Determines whether or not the timeout should be considered as successfully handled.
         *
         * @param process the process
         * @return true if the timeout was handled; false otherwise
         */
        boolean processTimeout(Process process);

        /**
         * Process the exit of the process.
         *
         * @param process the process
         */
        void processExit(Process process);
    }
}
