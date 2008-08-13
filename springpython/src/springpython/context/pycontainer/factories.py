import utils

class Factory (object):
	def getInstance (self, classpath):
		pass

class LocalFactory (Factory):
	def getInstance (self, classpath):
		return utils.getClass(classpath)()
		




	
	