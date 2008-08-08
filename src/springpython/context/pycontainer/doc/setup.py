classifiers = """\
Development Status :: 3 - Alpha
Intended Audience :: Developers
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Libraries :: Application Frameworks
"""
import sys
from distutils.core import setup
from pycontainer import __version__ as ver


if sys.version_info < (2, 3):
    _setup = setup
    def setup(**kwargs):
        if kwargs.has_key("classifiers"):
            del kwargs["classifiers"]
        _setup(**kwargs)


setup(name="PyContainer",
      version=ver,
	  author="Rafal Sniezynski",
      author_email="thirdeye at interia pl",
      url = "http://www.iem.pw.edu.pl/~sniezynr/pycontainer/",
	  download_url = "http://www.iem.pw.edu.pl/~sniezynr/pycontainer/PyContainer-"+ver+".zip",
	  description = "A simple Inversion of Control (Dependency Injection) lightweight container",
      license = "Python (modified BSD style)",
      platforms = ["Python >= 2.2"],
	  packages = ["pycontainer"],
      classifiers = filter(None, classifiers.split("\n")),
      long_description = '''PyContainer is a simple Python implementation of an 
      Inversion of Control (Dependency Injection) lightweight container. 
      Lightweight containers make it easier to build well-organized, component 
      based applications by managing all dependencies of the components. This 
      makes it unnecessary to include any implementation-specific component 
      object creation code in the components. Applications are more flexible and 
      components more reusable. 
	  PyContainer supports container hierarchies, interceptors and lifecycle 
	  management. It is configured through XML file. The distribution includes 
	  the pxdom module required in some envrionments (license details in 
	  license.txt).'''
      )
