/*
 *  Copyright 2006-2008 SpringSource (http://springsource.com, All Rights Reserved
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

package net.sourceforge.springpython;

import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import org.mortbay.jetty.Server;
import org.mortbay.jetty.servlet.Context;
import org.mortbay.jetty.servlet.ServletHolder;
import org.mortbay.log.StdErrLog;

import com.caucho.hessian.server.HessianServlet;

public class HessianJavaServer extends HessianServlet implements SampleService {

	private static final long serialVersionUID = 1L;
	private static final StdErrLog log = new StdErrLog();

	
	public static void main(String[] args) throws Exception {
		Server server = new Server(8080);
		Context root = new Context(server,"/",Context.SESSIONS);
		
		// This thread is a fall back to make sure the test server shuts down eventually.
    	Executors.newSingleThreadScheduledExecutor().schedule(new Runnable() {
			public void run() {
				log.warn("Jetty did not shut down normally!", null, null);
				System.exit(0);
			}
    	}, 6, TimeUnit.SECONDS);

		root.addServlet(new ServletHolder(new HessianJavaServer()), "/*");
		server.start();
	}
	
    public Person transform(String input) {
    	Executors.newSingleThreadScheduledExecutor().schedule(new Runnable() {
			public void run() {
				log.warn("Jetty is now shutting down.", null, null);
				System.exit(0);
			}
    	}, 1, TimeUnit.SECONDS);
    	
    	Person results = new Person();
		results.setFirstName(input.split(" ")[0]);
		results.setLastName(input.split(" ")[1]);
		results.setAttributes(input.split(" ")[2].split(","));
		return results;
	}

}

