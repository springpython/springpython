import unittest
from springpython.context import *
from springpython.config import *

class UnicodeTestCaseXml(unittest.TestCase):
	def testParsingAppContextWithNonAscii1(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext1.xml"))

	def testParsingAppContextWithNonAscii2(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext2.xml"))

	def testParsingAppContextWithNonAscii3(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext3.xml"))

	def testParsingAppContextWithNonAscii4(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext4.xml"))

	def testParsingAppContextWithNonAscii5(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext5.xml"))

	def testParsingAppContextWithNonAscii6(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext6.xml"))

	def testParsingAppContextWithNonAscii7(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext7.xml"))

	def testParsingAppContextWithNonAscii8(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext8.xml"))

	def testParsingAppContextWithNonAscii9(self):
		ctx = ApplicationContext(XMLConfig("support/unicodeContext9.xml"))

	def testParsingAppContextWithNonAscii10(self):
 		try:
 			ctx = ApplicationContext(XMLConfig("support/unicodeContext10.xml"))
			self.fail("Expected an encoding error since Python code is ASCII based.")
		except UnicodeEncodeError:
			pass

class UnicodeTestCaseYaml(unittest.TestCase):
	def testParsingAppContextWithNonAscii1(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext1.yaml"))

	def testParsingAppContextWithNonAscii3(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext3.yaml"))

	def testParsingAppContextWithNonAscii4(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext4.yaml"))

	def testParsingAppContextWithNonAscii5(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext5.yaml"))


	def testParsingAppContextWithNonAscii6(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext6.yaml"))

	def testParsingAppContextWithNonAscii7(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext7.yaml"))

	def testParsingAppContextWithNonAscii8(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext8.yaml"))

	def testParsingAppContextWithNonAscii9(self):
		ctx = ApplicationContext(YamlConfig("support/unicodeContext9.yaml"))

	def testParsingAppContextWithNonAscii10(self):
 		try:
 			ctx = ApplicationContext(YamlConfig("support/unicodeContext10.yaml"))
			self.fail("Expected an encoding error since Python code is ASCII based.")
		except UnicodeEncodeError:
			pass
