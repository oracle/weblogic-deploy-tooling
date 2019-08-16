/*
 * Copyright (c) 2018, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logger;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogEndHandler;
import oracle.weblogic.deploy.logging.WLSDeployLoggingConfig;
import oracle.weblogic.deploy.util.WLSDeployContext;
import oracle.weblogic.deploy.util.WLSDeployContext.WLSTMode;
import oracle.weblogic.deploy.util.WLSDeployExit;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.powermock.api.easymock.PowerMock;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Handler;
import java.util.logging.LogRecord;
import java.util.logging.Logger;

import static org.easymock.EasyMock.expect;
import static org.powermock.api.easymock.PowerMock.createMock;
import static org.powermock.api.easymock.PowerMock.mockStatic;

/**
 * Test the exit methods in the WLSDeployExit class.
 */
@RunWith(PowerMockRunner.class)
@PrepareForTest(PlatformLogger.class)
public class WLSDeployExitTest {

    private static final String WLSDEPLOY_NAME = WLSDeployLoggingConfig.WLSDEPLOY_LOGGER_NAME;
    private static int[] expected;
    private static int[] actual;
    private static int actualIdx;

    @Before
    public void setUp() {
        mockStatic(PlatformLogger.class);
        actualIdx = 0;
    }

    @Test
    public void testDepthOfHandlers() throws Exception {
        expected = new int[] { 1, 2, 3, 5, 4, 6, 7 };
        actual = new int[7];
        List<Logger> loggers = new ArrayList<>();

        Logger logger7 = getLogger(null, getHandlerList(getDeployHandler(7)), true, 2);
        Logger logger6 = getLogger(logger7, getHandlerList(getDeployHandler(6)), true, 2);

        Logger logger5 = getLogger(null, getHandlerList(getDeployHandler(5)), true);
        Logger logger1 = getLogger(logger5, getHandlerList(getDeployHandler(1)), true);
        expect(logger1.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger1);

        Logger logger4 = getLogger(logger6, getHandlerList(getDeployHandler(4)), true);
        Logger logger2 = getLogger(logger4, getHandlerList(getDeployHandler(2)), true);
        expect(logger2.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger2);

        Logger logger3 = getLogger(logger6, getHandlerList(getDeployHandler(3)), true);
        expect(logger3.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger3);

        expect(PlatformLogger.getLoggers()).andReturn(loggers);
        PowerMock.replayAll();

        WLSDeployExit.logCleanup(new WLSDeployContext("myname", "12.2.1.3", WLSTMode.OFFLINE));

        PowerMock.verifyAll();

        for (int idx = 0; idx < expected.length; idx++) {
            Assert.assertEquals(expected[idx], actual[idx]);
        }
    }

    @Test
    public void testSkipMiddle() throws Exception {
        expected = new int[] { 1, 2, 3, 7};
        actual = new int[4];
        List<Logger> loggers = new ArrayList<>();

        Logger logger7 = getLogger(null, getHandlerList(getDeployHandler(7)), true, 3);
        Logger logger6 = getLogger(logger7, getHandlerList(getHandler(6)), true, 3);

        Logger logger1 = getLogger(logger6, getHandlerList(getDeployHandler(1)), true);
        expect(logger1.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger1);

        Logger logger2 = getLogger(logger6, getHandlerList(getDeployHandler(2)), true);
        expect(logger2.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger2);

        Logger logger3 = getLogger(logger6, getHandlerList(getDeployHandler(3)), true);
        expect(logger3.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger3);

        expect(PlatformLogger.getLoggers()).andReturn(loggers);
        PowerMock.replayAll();

        WLSDeployExit.logCleanup(new WLSDeployContext("myname", "12.2.1.3", WLSTMode.OFFLINE));

        PowerMock.verifyAll();

        for (int idx = 0; idx < expected.length; idx++) {
            Assert.assertEquals(expected[idx], actual[idx]);
        }

    }

    @Test
    public void testSingleDepth() throws Exception {
        expected = new int[] {1, 2, 3};
        actual = new int[3];
        List<Logger> loggers = new ArrayList<>();

        Logger logger7 = getLogger(null, getHandlerList(getHandler(7)), true, 3);
        Logger logger6 = getLogger(logger7, getHandlerList(getHandler(6)), true, 3);

        Logger logger1 = getLogger(logger6, getHandlerList(getDeployHandler(1)), true);
        expect(logger1.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger1);

        Logger logger2 = getLogger(logger6, getHandlerList(getDeployHandler(2)), true);
        expect(logger2.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger2);

        Logger logger3 = getLogger(logger6, getHandlerList(getDeployHandler(3)), true);
        expect(logger3.getName()).andReturn(WLSDEPLOY_NAME);
        loggers.add(logger3);

        expect(PlatformLogger.getLoggers()).andReturn(loggers);
        PowerMock.replayAll();

        WLSDeployExit.logCleanup(new WLSDeployContext("myname", "12.2.1.3", WLSTMode.OFFLINE));

        PowerMock.verifyAll();

        for (int idx = 0; idx < expected.length; idx++) {
            Assert.assertEquals(expected[idx], actual[idx]);
        }
    }

    private Handler[] getHandlerList(Handler... handlers) {
        return handlers;
    }

    private Logger getLogger(Logger parent, Handler[] handlers, boolean useParentHandlers) {
        return getLogger(parent, handlers, useParentHandlers, 1);
    }

    private Logger getLogger(Logger parent, Handler[] handlers, boolean useParentHandlers, int times) {
        Logger logger = createMock(Logger.class);
        expect(logger.getHandlers()).andReturn(handlers).times(times);
        expect(logger.getParent()).andReturn(parent).times(times);
        expect(logger.getUseParentHandlers()).andReturn(useParentHandlers).times(times);
        return logger;
    }

    private Handler getDeployHandler(int handlerIdx) {
        return new FakeDeployHandler(handlerIdx);
    }

    private Handler getHandler(int handlerIdx) {
        return new FakeHandler(handlerIdx);
    }

    private class FakeDeployHandler extends FakeHandler implements WLSDeployLogEndHandler {

        FakeDeployHandler(int state) {
            super(state);
        }

        @Override
        public synchronized void logEnd(WLSDeployContext context) {
            actual[actualIdx++] = getState();
        }
    }

    private class FakeHandler extends Handler {

        private int state = -1;

        FakeHandler(int state) {
            this.state = state;
        }


        @Override
        public void publish(LogRecord record) {

        }

        @Override
        public void flush() {

        }

        @Override
        public void close() throws SecurityException {

        }

        int getState() {
            return state;
        }
    }


}
