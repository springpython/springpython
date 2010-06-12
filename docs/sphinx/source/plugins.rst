Spring Python's plugin system
=============================

Spring Python's plugin system is designed to help you rapidly develop applications.
Plugin-based solutions have been proven to enhance developer efficiency, with
examples such as `Grails <http://grails.org/>`_ and `Eclipse <http://eclipse.org/>`_
being market leaders in usage and productivity.

This plugin solution was mainly inspired by the Grails demo presented by
Graeme Rocher at the SpringOne Americas 2008 conference, in which he created
a Twitter application in 40 minutes. Who wouldn't want to have something similar
to support Spring Python development?

Introduction
------------

Spring Python will manage an approved set of plugins. These are plugins written
by the committers of Spring Python and are verified to work with an associated
version of the library. These plugins are also hosted by the same services used
to host Spring Python downloads, meaning they have the same level of support
as Spring Python.

However, being an open source framework, developers have every right to code
their own plugins. We fully support the concept of 3rd party plugins. We want
to provide as much support in the way of documentation and extension points
for you to develop your own plugins as well.

.. note::

    Have you considered submitting your plugin as a Spring Extension?

    `Spring Extensions <http://www.springsource.org/extensions>`_ is the official
    incubator process for SpringSource. You can
    always maintain your own plugin separately, using whatever means you wish. But
    if want to get a larger adoption of your plugin, name association with
    SpringSource, and perhaps one day becoming an official part of the software
    suite of SpringSource, you may want to consider looking into the Spring
    Extensions process.


Coily - Spring Python's command-line tool
-----------------------------------------

Coily is the command-line tool that utilizes the plugin system. It is similar
to grails command-line tool, in that through a series of installed plugins,
you are able to do many tasks, including build skeleton apps that you can later
flesh out. If you look at the details of this app, you will find a sophisticated,
command driven tool to built to manage plugins. The real power is in the
plugins themselves.

Commands
++++++++

.. highlight:: bash

To get started, all you need is a copy of coily installed in some directory located
on your path::

    % coily --help

The results should list available commands::

    Coily - the command-line management tool for Spring Python
    ==========================================================
    Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved
    Licensed under the Apache License, Version 2.0


    Usage: coily [command]

            --help                          print this help message
            --list-installed-plugins        list currently installed plugins
            --list-available-plugins        list plugins available for download
            --install-plugin [name]         install coily plugin
            --uninstall-plugin [name]       uninstall coily plugin
            --reinstall-plugin [name]       reinstall coily plugin


* --help - Print out the help menu being displayed

* --list-installed-plugins - list the plugins currently installed in this
  account. It is important to know that each plugin creates a directly
  underneath the user's home directory in a hidden directory *~/.springpython*.
  If you delete this entire directory, you have effectively uninstalled all plugins.

* --list-available-plugins - list the plugins available for installation.
  Coily will check certain network locations, such as the S3 site used to host
  Spring Python downloads. It will also look on the local file system. This is
  in case you have a checked out copy of the plugins source code, and want to
  test things out without uploading to the network.

* --install-plugin - install the named plugin. In this case, you don't have to
  specify a version number. Coily will figure out which version of the plugin
  you need, download it if necessary, and finally copy it into *~/.springpython*.

* --uninstall-plugin - uninstall the named plugin by deleting its entry from *~/.springpython*

* --reinstall-plugin - uninstall then install the plugin. This is particulary
  useful if you are working on a plugin, and need a shortcut step to deploy.

In this case, no plugins have been installed yet. Every installed plugin will
list itself as another available command to run. If you have already installed
the *gen-cherrypy-app* plugin, you will see it listed::

    Coily - the command-line management tool for Spring Python
    ==========================================================
    Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved
    Licensed under the Apache License, Version 2.0


    Usage: coily [command]

            --help                          print this help message
            --list-installed-plugins        list currently installed plugins
            --list-available-plugins        list plugins available for download
            --install-plugin [name]         install coily plugin
            --uninstall-plugin [name]       uninstall coily plugin
            --reinstall-plugin [name]       reinstall coily plugin
            --gen-cherrypy-app [name]       plugin to create skeleton CherryPy applications

You should notice an extra option listed at the bottom: *gen-cherrypy-app*
is listed as another command with one argument. Later on, you can read
official documentation on the existing plugins, and also how to write your own.


Officially Supported Plugins
----------------------------

This section documents plugins that are developed by the Spring Python team.

External dependencies
+++++++++++++++++++++

*gen-cherrypy-app* plugin requires the installation of `CherryPy 3 <http://cherrypy.org/>`_.

gen-cherrypy-app
++++++++++++++++

This plugin is used to generate a skeleton `CherryPy <http://cherrypy.org/>`_
application based on feeding it a command-line argument::

    % coily --gen-cherrypy-app twitterclone

This will generate a subdirectory *twitterclone* in the user's current directory.
Inside twitterclone are several files, including *twitterclone.py*. If you run
the app, you will see a working CherryPy application, with Spring Python
security in place::

    % cd twitterclone
    % python twitterclone.py

You can immediately start modifying it to put in your features.

Writing your own plugin
-----------------------

Architecture of a plugin
++++++++++++++++++++++++

.. highlight:: python

A plugin is pretty simple in structure. It is basically a Python package with
some special things added on. *gen-cherrypy-app* plugin demonstrates this.

.. image:: gfx/gen-cherrypy-app-folder-struct.png
    :align: center

The special things needed to define a plugin are as follows:

* A root folder with the same name as your plugin and a *__init__.py*, making
  the plugin a Python package.

* A package-level variable named *__description__*
  This attribute should be assigned the string value description you want
  shown for your plugin when coily --help is run.

* A package-level function named either *create* or *apply*

  * If your plugin needs one command line argument, define a *create* method with the following signature::

        def create(plugin_path, name)

  * If your plugin doesn't need any arguments, define an *apply* method with the following signature::

        def apply(plugin_path)

  In either case, your plugin gets passed an extra argument, plugin_path,
  which contains the directory the plugin is actually installed in. This is
  typically so you can reference other files your plugin needs access to.

  .. note::

     What does "package-level" mean?

     The code needs to be in the __init__.py file. This file makes the enclosing
     directory a Python package.

Case Study - gen-cherrypy-app plugin
++++++++++++++++++++++++++++++++++++

*gen-cherrypy-app* is a plugin used to build a `CherryPy <http://cherrypy.org/>`_ web application using
Spring Python's feature set. It saves the developer from having to re-configure
Spring Python's security module, coding CherryPy's engine, and so forth. This
allows the developer to immediately start writing business code against a
working application.

Using this plugin, we will de-construct this simple, template-based plugin.
This will involve looking line-by-line at *gen-cherrypy-app/__init__.py*.

Source Code
>>>>>>>>>>>

::

    """
       Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

       Licensed under the Apache License, Version 2.0 (the "License");
       you may not use this file except in compliance with the License.
       You may obtain a copy of the License at

           http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS,
       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
       See the License for the specific language governing permissions and
       limitations under the License.
    """
    import re
    import os
    import shutil

    __description__ = "plugin to create skeleton CherryPy applications"

    def create(plugin_path, name):
        if not os.path.exists(name):
            print "Creating CherryPy skeleton app %s" % name
            os.makedirs(name)

            # Copy/transform the template files
            for file_name in ["cherrypy-app.py", "controller.py", "view.py", "app_context.py"]:
                input_file = open(plugin_path + "/" + file_name).read()

                # Iterate over a list of patterns, performing string substitution on the input file
                patterns_to_replace = [("name", name), ("properName", name[0].upper() + name[1:])]
                for pattern, replacement in patterns_to_replace:
                    input_file = re.compile(r"\$\{%s}" % pattern).sub(replacement, input_file)

                output_filename = name + "/" + file_name
                if file_name == "cherrypy-app.py":
                    output_filename = name + "/" + name + ".py"

                app = open(output_filename, "w")
                app.write(input_file)
                app.close()

            # Recursively copy other parts
            shutil.copytree(plugin_path + "/images", name + "/" + "images")
        else:
            print "There is already something called %s. ABORT!" % name


Deconstructing the factory
>>>>>>>>>>>>>>>>>>>>>>>>>>

* The opening section shows the copyright statement, which should tip you off
  that this is an official plugin.

* __description__ is a required variable::

    __description__ = "plugin to create skeleton CherryPy applications"

  It contains the description displayed when a user runs::

    % coily --help

  ::

    Usage: coily [command]
    ...
            --gen-cherrypy-app [name]       plugin to create skeleton CherryPy applications

* Opening line defines create with two arguments::

    def create(plugin_path, name):

  The arguments allow both the plugin path to be fed along with the command-line
  argument that is filled in when the user runs the command::

    % coily --gen-cherrypy-app [name]

  It is important to realize that *plugin_path* is needed in case the plugin
  needs to refer to any files inside its installed directory. This is because
  plugins are not installed anywhere on the *PYTHONPATH*, but instead, in the
  user's home directory underneath *~/.springpython*.

  This mechanism was chosen because it gives users an easy ability to pick
  which plugins they wish to use, without requiring system admin power. It also
  eliminates the need to deal with multiple versions of plugins being installed
  on your *PYTHONPATH*. This provides maximum flexibility which is needed in a
  development environment.

* This plugin works by creating a directory in the user's current working directory,
  and putting all relevant files into it. The argument passed into the command-line
  is used as the name of an application, and the directory created has the same name::

      if not os.path.exists(name):
          print "Creating CherryPy skeleton app %s" % name
          os.makedirs(name)

  However, if the directory already exists, it won't proceed::

      else:
          print "There is already something called %s. ABORT!" % name

* This plugin then iterates over a list of filenames, which happen to match the
  names of files found in the plugin's directory. These are essentially template
  files, intended to be copied into the target directory. However, the files
  are not copied directly. Instead they are opened and read into memory::

      # Copy/transform the template files
      for file_name in ["cherrypy-app.py", "controller.py", "view.py", "app_context.py"]:
          input_file = open(plugin_path + "/" + file_name).read()

  Then, the contents are scanned for key phrases, and substituted. In this case,
  the substitution is a variant of the name of the application being generated::

      # Iterate over a list of patterns, performing string substitution on the input file
      patterns_to_replace = [("name", name), ("properName", name[0].upper() + name[1:])]
      for pattern, replacement in patterns_to_replace:
          input_file = re.compile(r"\$\{%s}" % pattern).sub(replacement, input_file)

  The substituted content is written to a new output file. In most cases,
  the original filename is also the target filename. However, the key file,
  *cherrypy-app.py* is renamed to the application's name::

      output_filename = name + "/" + file_name
      if file_name == "cherrypy-app.py":
          output_filename = name + "/" + name + ".py"

      app = open(output_filename, "w")
      app.write(input_file)
      app.close()

* Finally, the images directory is recursively copied into the target directory::

      # Recursively copy other parts
      shutil.copytree(plugin_path + "/images", name + "/" + "images")

Summary
>>>>>>>

All these steps effectively copy a set of files used to template an application.
With this template approach, the major effort of developing this plugin is spent
working on the templates themselves, not on this template factory. While this is
mostly working with python code for a python solution, the fact that this is a
template requires reinstalling the plugin everytime a change is made in order
to test them.

Users are welcome to use *gen-cherypy-app*'s *__init__.py* file to generate their
own template solutions, and work on other skeleton tools or solutions.