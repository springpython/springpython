#
# A Hessian client interface for Python.  The date and long types require
# Python 2.2 or later.
#
# The Hessian proxy is used as follows:
#
# proxy = Hessian("http://hessian.caucho.com/test/basic")
#
# print proxy.hello()
#
# --------------------------------------------------------------------
#
# The Apache Software License, Version 1.1
#
# Copyright (c) 2001-2002 Caucho Technology, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. The end-user documentation included with the redistribution, if
#    any, must include the following acknowlegement:
#       "This product includes software developed by the
#        Caucho Technology (http://www.caucho.com/)."
#    Alternately, this acknowlegement may appear in the software itself,
#    if and wherever such third-party acknowlegements normally appear.
#
# 4. The names "Hessian", "Resin", and "Caucho" must not be used to
#    endorse or promote products derived from this software without prior
#    written permission. For written permission, please contact
#    info@caucho.com.
#
# 5. Products derived from this software may not be called "Resin"
#    nor may "Resin" appear in their names without prior written
#    permission of Caucho Technology.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESSED OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL CAUCHO TECHNOLOGY OR ITS CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# --------------------------------------------------------------------
#
# Credits: hessianlib.py was inspired and partially based on
# xmlrpclib.py created by Fredrik Lundh at www.pythonware.org
#
import string, time
import urllib
from types import *
from struct import unpack
from struct import pack

__version__ = "0.1"


# --------------------------------------------------------------------
# Exceptions

class Error:
    # base class for client errors
    pass

class ProtocolError(Error):
    # Represents an HTTP protocol error
    def __init__(self, url, code, message, headers):
	self.url = url
	self.code = code
	self.message = message
	self.headers = headers

    def __repr__(self):
	return (
	    "<ProtocolError for %s: %s %s>" %
	    (self.url, self.code, self.message)
	    )

class Fault(Error):
    # Represents a fault from Hessian
    def __init__(self, code, message, **detail):
	self.code = code
	self.message = message

    def __repr__(self):
	return "<HessianFault %s: %s>" % (self.code, self.message)

# --------------------------------------------------------------------
# Wrappers for Hessian data types non-standard in Python
#

#
# Boolean -- use the True or False constants
#
class Boolean:
    def __init__(self, value = 0):
	self.value = (value != 0)

    def _hessian_write(self, out):
	if self.value:
	    out.write('T')
	else:
	    out.write('F')

    def __repr__(self):
	if self.value:
	    return "<True at %x>" % id(self)
	else:
	    return "<False at %x>" % id(self)

    def __int__(self):
	return self.value

    def __nonzero__(self):
	return self.value

True, False = Boolean(1), Boolean(0)

#
# Date - wraps a time value in seconds
#
class Date:
    def __init__(self, value = 0):
	self.value = value

    def __repr__(self):
	return ("<Date %s at %x>" %
                (time.asctime(time.localtime(self.value)), id(self)))

    def _hessian_write(self, out):
	out.write("d")
	out.write(pack(">q", self.value * 1000.0))
#
# Binary - binary data
#

class Binary:
    def __init__(self, data=None):
	self.data = data

    def _hessian_write(self, out):
	out.write('B')
	out.write(pack('>H', len(self.data)))
	out.write(self.data)

# --------------------------------------------------------------------
# Marshalling and unmarshalling code

#
# HessianWriter - writes Hessian data from Python objects
#
class HessianWriter:
    dispatch = {}

    def write_call(self, method, params):
	self.refs = {}
	self.ref = 0
	self.__out = []
	self.write = write = self.__out.append

        write("c\x01\x00m");
        write(pack(">H", len(method)));
        write(method);
	for v in params:
	    self.write_object(v)
        write("z");
	result = string.join(self.__out, "")
	del self.__out, self.write, self.refs
	return result

    def write_object(self, value):
	try:
	    f = self.dispatch[type(value)]
	except KeyError:
	    raise TypeError, "cannot write %s objects" % type(value)
	else:
	    f(self, value)

    def write_int(self, value):
	self.write('I')
	self.write(pack(">l", value))
    dispatch[IntType] = write_int

    def write_long(self, value):
	self.write('L')
	self.write(pack(">q", value))
    dispatch[LongType] = write_long

    def write_double(self, value):
	self.write('D')
	self.write(pack(">d", value))
    dispatch[FloatType] = write_double

    def write_string(self, value):
	self.write('S')
	self.write(pack('>H', len(value)))
	self.write(value)
    dispatch[StringType] = write_string

    def write_reference(self, value):
        # check for and write circular references
        # returns 1 if the object should be written, i.e. not a reference
	i = id(value)
	if self.refs.has_key(i):
	    self.write('R')
	    self.write(pack(">L", self.refs[i]))
	    return 0
	else:
	    self.refs[i] = self.ref
	    self.ref = self.ref + 1
	    return 1

    def write_list(self, value):
	if self.write_reference(value):
	    self.write("Vt\x00\x00I");
	    self.write(pack('>l', len(value)))
	    for v in value:
	        self.__write(v)
	    self.write('z')
    dispatch[TupleType] = write_list
    dispatch[ListType] = write_list

    def write_map(self, value):
	if self.write_reference(value):
	    self.write("Mt\x00\x00")
	    for k, v in value.items():
	        self.__write(k)
	        self.__write(v)
	    self.write("z")
    dispatch[DictType] = write_map

    def write_instance(self, value):
	# check for special wrappers
	if hasattr(value, "_hessian_write"):
	    value._hessian_write(self)
	else:
	    fields = value.__dict__
	    if self.write_reference(fields):
	        self.write("Mt\x00\x00")
	        for k, v in fields.items():
	            self.__write(k)
	            self.__write(v)
	        self.write("z")
    dispatch[InstanceType] = write_instance

#
# Parses the results from the server
#
class HessianParser:
    def __init__(self, f):
	self._f = f
        self._peek = -1
	# self.read = f.read
	self._refs = []

    def read(self, len):
	if self._peek >= 0:
	  value = self._peek
	  self._peek = -1
	  return value
	else:
	  return self._f.read(len)

    def parse_reply(self):
        # parse header 'c' x01 x00 'v' ... 'z'
	read = self.read
	if read(1) != 'r':
	    self.error()
	major = read(1)
	minor = read(1)

        value = self.parse_object()

	if read(1) == 'z':
	    return value
	self.error() # actually a fault

    def parse_object(self):
	# parse an arbitrary object based on the type in the data
	return self.parse_object_code(self.read(1))

    def parse_object_code(self, code):
	# parse an object when the code is known
	read = self.read

	if code == 'N':
	    return None

	elif code == 'T':
	    return True

	elif code == 'F':
	    return False

	elif code == 'I':
	    return unpack('>l', read(4))[0]

	elif code == 'L':
	    return unpack('>q', read(8))[0]

	elif code == 'D':
	    return unpack('>d', read(8))[0]

	elif code == 'd':
	    ms = unpack('>q', read(8))[0]

	    return Date(int(ms / 1000.0))

	elif code == 'S' or code == 'X':
	    return self.parse_string()

	elif code == 'B':
	    return Binary(self.parse_string())

	elif code == 'V':
	    self.parse_type() # skip type
	    self.parse_length()           # skip length
	    list = []
	    self._refs.append(list)
	    ch = read(1)
	    while ch != 'z':
		list.append(self.parse_object_code(ch))
		ch = read(1)
	    return list

	elif code == 'M':
	    self.parse_type() # skip type
	    map = {}
	    self._refs.append(map)
	    ch = read(1)
	    while ch != 'z':
		key = self.parse_object_code(ch)
		value = self.parse_object()
		map[key] = value
		ch = read(1)
	    return map

	elif code == 'R':
	    return self._refs[unpack('>l', read(4))[0]]

	elif code == 'r':
	    self.parse_type()       # skip type
	    url = self.parse_type() # reads the url
	    return Hessian(url)

	else:
	    raise "UnknownObjectCode %d" % code

    def parse_string(self):
	f = self._f
	len = unpack('>H', f.read(2))[0]
	return f.read(len)

    def parse_type(self):
	f = self._f
	code = self.read(1)
	if code != 't':
	  self._peek = code
	  return ""
	len = unpack('>H', f.read(2))[0]
	return f.read(len)

    def parse_length(self):
	f = self._f
	code = self.read(1);
	if code != 'l':
	  self._peek = code
	  return -1;
	len = unpack('>l', f.read(4))
	return len

    def error(self):
	raise "FOO"

#
# Encapsulates the method to be called
#
class _Method:
    def __init__(self, invoker, method):
	self._invoker = invoker
	self._method = method

    def __call__(self, *args):
	return self._invoker(self._method, args)

# --------------------------------------------------------------------
# Hessian is the main class.  A Hessian proxy is created with the URL
# and then called just as for a local method
#
# proxy = Hessian("http://www.caucho.com/hessian/test/basic")
# print proxy.hello()
#
class Hessian:
    """Represents a remote object reachable by Hessian"""

    def __init__(self, url):
	# Creates a Hessian proxy object

	self._url = url

	# get the uri
	type, uri = urllib.splittype(url)
	if type != "http":
	    raise IOError, "unsupported Hessian protocol"

	self._host, self._uri = urllib.splithost(uri)

    def __invoke(self, method, params):
	# call a method on the remote server

	request = HessianWriter().write_call(method, params)

	import httplib

	h = httplib.HTTP(self._host)
	h.putrequest("POST", self._uri)

	# required by HTTP/1.1
	h.putheader("Host", self._host)

	h.putheader("User-Agent", "hessianlib.py/%s" % __version__)
	h.putheader("Content-Length", str(len(request)))

	h.endheaders()

	h.send(request)

	errcode, errmsg, headers = h.getreply()

	if errcode != 200:
	    raise ProtocolError(self._url, errcode, errmsg, headers)

	return self.parse_response(h.getfile())

    def parse_response(self, f):
	# read response from input file, and parse it

	parser = HessianParser(f)
	value = parser.parse_reply()
	f.close()

	return value

    def _hessian_write(self, out):
	# marshals the proxy itself
	out.write("rt\x00\x00S")
	out.write(pack(">H", len(self._url)))
	out.write(self._url)

    def __repr__(self):
	return "<HessianProxy %s>" % self._url

    __str__ = __repr__

    def __getattr__(self, name):
	# encapsulate the method call
	return _Method(self.__invoke, name)

#
# Testing code.
#
if __name__ == "__main__":

    proxy = Hessian("http://hessian.caucho.com/test/test")

    try:
	print proxy.hello()
    except Error, v:
	print "ERROR", v
