import sys

def getModuleAndClassName (classpath):
	'''Splits classpath to modulepath and classname.'''
	parts = classpath.split(".")
	className = parts.pop()
	moduleName = ".".join(parts)
	return moduleName, className

def getClass (classpath):
	'''Returns an instance of a class.'''
	moduleName, className = getModuleAndClassName(classpath)  # Split the class path
	__import__(moduleName)
	klass = getattr(sys.modules[moduleName], className)
	return klass