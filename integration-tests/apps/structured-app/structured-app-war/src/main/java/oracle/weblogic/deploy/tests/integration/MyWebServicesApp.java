// Copyright 2024, Oracle Corporation and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
package oracle.weblogic.deploy.tests.integration;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import javax.naming.NamingException;
import javax.naming.InitialContext;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Application;
import javax.ws.rs.core.Response;

@Path("/test")
public class MyWebServicesApp extends Application {
    @GET
    @Produces("text/plain")
    @Path("/plan")
    public Response getEnvValue() {
        Response response;
        try {
            InitialContext ctx = new InitialContext();
            String envValue = (String) ctx.lookup("java:comp/env/myValue");
            response = Response.ok().entity(envValue).build();
        } catch (NamingException ex) {
            response = Response.status(400).entity(ex.getMessage()).build();
        }

        return response;
    }

    @GET
    @Produces("text/plain")
    @Path("/overrides/{overridesFileName}/{propertyName}")
    public Response getOverridesValue(@PathParam("overridesFileName") String overridesFileName, @PathParam("propertyName") String propertyName) {
        Response response;

        Properties myProps = new Properties();
        try (InputStream iostream = Thread.currentThread().getContextClassLoader().getResourceAsStream(overridesFileName)) {
            if (iostream != null) {
                myProps.load(iostream);
                String value = myProps.getProperty(propertyName, "oops");
                response = Response.ok().entity(value).build();
            } else {
                String message = String.format("Failed to find file %s", overridesFileName);
                response = Response.status(400).entity(message).build();
            }
        } catch (IOException ex) {
            response = Response.status(400).entity(ex.getMessage()).build();
        }

        return response;
    }
}
