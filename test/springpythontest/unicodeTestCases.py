import unittest
from springpython.context import *
from springpython.config import *

class UnicodeTestCase(unittest.TestCase):
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
