"""Transform XML Documents to Python objects

Please see the information at gnosis.xml.objectify.doc for
explanation of usage, design, license, and other details
"""
from types import *
from cStringIO import StringIO
from copy import deepcopy

#-- Node types are now class constants defined in class Node.
DOM = 'DOM'

# This used to support older version of Python, which didn't have the expat parser.
# This redistribution requires a new version of Python, so there is no value in checking
# for this. Instead, it is hard-coded to use the EXPAT mode.
import xml.parsers.expat
EXPAT = 'EXPAT'
SCHEMA = 'http://springpython.webfactional.com/schema/context/spring-python-context-1.0.xsd'

def instance (x):
    global minidom, Node
    return XML_Objectify(x,EXPAT).make_instance()

#-- Global option to save every container tag content
KEEP_CONTAINERS = 0
ALWAYS, MAYBE, NEVER = (1,0,-1)
def keep_containers(val=None):
    if val is not None:
        global KEEP_CONTAINERS
        KEEP_CONTAINERS = val
    return KEEP_CONTAINERS

#-- Disable or configure namsepaces in EXPAT
def config_nspace_sep(val=None):
    XML_Objectify.expat_kwargs['nspace_sep'] = val

#-- Convenience functions
make_instance = lambda x, p=EXPAT: XML_Objectify(x,p).make_instance()
children = lambda o: [x for x in o._seq if type(x) is not type(u'')]
content = lambda o: o._seq or []
dumps = lambda o: ''.join([x for x in o._seq if type(x) is type(u'')])
normalize = lambda s: ' '.join(s.split())
tagname = lambda o: o.__class__.__name__.replace('_XO_','')

def addChild(parent, child):
   "Add a child xmlObject to a parent xmlObject"
   name = tagname(child)
   if hasattr(parent, name):  # If exists add, make into list if needed
      tag = getattr(parent, name)
      if type(tag) is not list:
         setattr(parent, name, [tag])
         tag = [tag]
      tag.append(child)
   else:                      # Create a new one
      setattr(parent, name, child)
      if not parent._seq: parent._seq = []
   parent._seq.append(child)  # All tags end up in _seq

#-- Base class for objectified XML nodes
class _XO_:
    def __getitem__(self, key):
        if key == 0:
            return self
        else:
            raise IndexError
    def __len__(self):
        return 1
    def __repr__(self):
        name = self.__class__.__name__.replace('_XO_','')
        return '<%s id="%x">' % (name, id(self))

#-- Needed for mixed usage in Python (xml.dom) and Jython (org.w3c.dom)
def _makeNodeList(nodes):
    if not nodes:
        return []
    try:
        nodes[0]
    except AttributeError:
        # assume W3C NodeList
        nl = []
        for i in range(nodes.length):
            nl.append(nodes.item(i))
        return nl
    else:
        return nodes

#-- Needed for mixed usage in Python (xml.dom) and Jython (org.w3c.dom)
def _makeAttrDict(attr):
    if not attr:
        return {}
    try:
        attr.has_key('dummy')
    except AttributeError:
        # assume a W3C NamedNodeMap
        attr_dict = {}
        for i in range(attr.length):
            node = attr.item(i)
            attr_dict[node.nodeName] = node
        return attr_dict
    else:
        return attr

#-- Class interface to module functionality
class XML_Objectify:
    """Factory object class for 'objectify XML document'"""
    expat_args, expat_kwargs = [], {}
    def __init__(self, xml_src=None, parser=DOM):
        self._parser = parser
        if parser==DOM and (hasattr(xml_src,'documentElement')
                            or hasattr(xml_src,'childNodes')):
            self._dom = xml_src
            self._fh = None
        elif type(xml_src) in (StringType, UnicodeType):
            if xml_src[0]=='<':     # looks like XML
                from cStringIO import StringIO
                self._fh = StringIO(xml_src)
            else:                   # looks like filename
                self._fh = open(xml_src,'rb')
        elif hasattr(xml_src,'read'):
            self._fh = xml_src
        else:
            raise ValueError, \
                  "XML_Objectify must be initialized with " +\
                  "a filename, file-like object, or DOM object"

        # First parsing option:  EXPAT (stream based)
        if self._parser == EXPAT:
            if not EXPAT:
                raise ImportError, "Expat parser not available"
            self.__class__.__bases__ += (ExpatFactory,)
            ExpatFactory.__init__(self,
                                  *self.__class__.expat_args,
                                  **self.__class__.expat_kwargs)

        # Second parsing option: DOM (keeps _dom)
        elif self._parser == DOM:
            if self._fh:
                self._dom = minidom.parseString(self._fh.read())
                self._processing_instruction = {}
            for child in _makeNodeList(self._dom.childNodes):
                if child.nodeType == Node.PROCESSING_INSTRUCTION_NODE:
                    self._processing_instruction[child.nodeName] = child.nodeValue
                elif child.nodeType == Node.ELEMENT_NODE:
                    self._root = child.nodeName
            self._PyObject = pyobj_from_dom(self._dom)

        else:
            raise ValueError, \
                  "An invalid parser was specified: %s" % self._parser

    def make_instance(self):
        if self._parser == EXPAT:
            return self.ParseFile(self._fh)
        elif self._parser == DOM:
            return deepcopy(getattr(self._PyObject, py_name(self._root)))
        else:
            return None

#-- expat based stream-oriented parser/objectifier
class ExpatFactory:
    def __init__(self, encoding="UTF-8", nspace_sep=" ", *args, **kws):
        self._myparser = xml.parsers.expat.ParserCreate(encoding, nspace_sep)
        self.returns_unicode = 1

        self._current = None
        self._root    = None
        self._pcdata  = 0

        myhandlers = dir(self.__class__)
        for b in  self.__class__.__bases__:
            myhandlers.extend(dir(b))
        myparsers = dir(self._myparser)
        myhandlers = [ h for h in myhandlers if h in myparsers \
                       if h.find('Handler') > 0 ]
        myparser = self._myparser
        for h in myhandlers:
            setattr(myparser, h, getattr(self,h))

    def ParseFile(self, file):
        self._myparser.returns_unicode = self.returns_unicode
        self._myparser.ParseFile(file)
        return self._root

    def Parse(self, data, isfinal=1):
        self._myparser.returns_unicode = self.returns_unicode
        self._myparser.Parse(data, isfinal)
        return self._root

    def StartElementHandler(self, name, attrs):
        # Create mangled name for current Python class and define it if need be
        pyname = py_name(name)
        py_obj = createPyObj(pyname)

        # Maintain sequence of all the children
        if self._current:
            if self._current._seq is None:
                self._current._seq = [py_obj]
            else:
                self._current._seq.append(py_obj)

        # Does our current object have a child of this type already?
        if hasattr(self._current, pyname):
            # Convert a single child object into a list of children
            if type(getattr(self._current, pyname)) is not ListType:
                setattr(self._current, pyname, [getattr(self._current, pyname)])
            # Add the new subtag to the list of children
            getattr(self._current, pyname).append(py_obj)
        # Start out by creating a child object as attribute value
        else:
            # Make sure that for the first call, i.e. the root of the DOM tree,
            # we attach it to our 'product', self._root
            if not self._root:
                self._root = py_obj
            else:
                setattr(self._current, pyname, py_obj)

        # Build the attributes of the object being created
        py_obj.__dict__   = attrs
        py_obj.__parent__ = self._current
        self._current = py_obj

    def EndElementHandler(self, name):
        if self._current._seq is not None:
            self._current.PCDATA = normalize(dumps(self._current))
        self._current = self._current.__parent__

    def CharacterDataHandler(self, data):
        """
        # Only adjust formatting if we are in a PCDATA section
        if self._pcdata:
            if hasattr(self._current,'PCDATA') and self._current.PCDATA:
                self._current.PCDATA += data
            else:
                self._current.PCDATA = data
        else:
            # Only use "real" node contents (not bare whitespace)
            if data.strip():
                if hasattr(self._current,'PCDATA') and self._current.PCDATA:
                    self._current.PCDATA += ' '+data.strip()
                else:
                    self._current.PCDATA = data.strip()
        """
        # Add the PCDATA to the parent's sequence
        # (XXX: more efficient mechanism is desirable.  intern()? slices?)
        if getattr(self._current, '_seq', None):
            if type(self._current._seq[-1])==type(u''):
                self._current._seq[-1] += data
            else:
                self._current._seq.append(data)
        else:
            self._current._seq = [data]

    def StartCdataSectionHandler(self):
        self._pcdata = 1

    def EndCdataSectionHandler(self):
        self._pcdata = 0


#-- Helper functions
def pyobj_from_dom(dom_node):
    """Converts a DOM tree to a "native" Python object"""

    py_obj = createPyObj(dom_node.nodeName)

    # attach any tag attributes as instance attributes
    attr_dict = _makeAttrDict(dom_node.attributes)
    if attr_dict is None:
        attr_dict = {}
    for key in attr_dict.keys():
        setattr(py_obj, py_name(key), attr_dict[key].value)

    # for nodes with character markup, might want the literal XML
    dom_node_xml = ''
    intro_PCDATA, subtag, exit_PCDATA = (0, 0, 0)

    # now look at the actual tag contents (subtags and PCDATA)
    for node in _makeNodeList(dom_node.childNodes):
        # Do not want DocumentType node
        if node.nodeType == Node.DOCUMENT_TYPE_NODE:
            continue
        node_name = py_name(node.nodeName)
        if KEEP_CONTAINERS > NEVER:
            if hasattr(node, 'toxml'):
                dom_node_xml += node.toxml()
            else:
                dom_node_xml += ''

        # PCDATA is a kind of node, but not a new subtag
        if node.nodeName=='#text' or node.nodeName=='#cdata-section':
            if hasattr(py_obj,'PCDATA') and py_obj.PCDATA is not None:
                py_obj.PCDATA += node.nodeValue
            elif node.nodeValue.strip():  # only use "real" node contents
                py_obj.PCDATA = node.nodeValue  # (not bare whitespace)
                if not subtag: intro_PCDATA = 1
                else: exit_PCDATA = 1

        # does a py_obj attribute corresponding to the subtag already exist?
        elif hasattr(py_obj, node_name):
            # convert a single child object into a list of children
            if type(getattr(py_obj, node_name)) is not ListType:
                setattr(py_obj, node_name, [getattr(py_obj, node_name)])
            # add the new subtag to the list of children
            getattr(py_obj, node_name).append(pyobj_from_dom(node))

        # start out by creating a child object as attribute value
        else:
            setattr(py_obj, node_name, pyobj_from_dom(node))
            subtag = 1

    # See if we want to save the literal character string of element
    if KEEP_CONTAINERS <= NEVER:
        pass
    elif KEEP_CONTAINERS >= ALWAYS:
        py_obj._XML = dom_node_xml
    else:       # if dom_node appears to contain char markup, save _XML
        if subtag and (intro_PCDATA or exit_PCDATA):
            py_obj._XML = dom_node_xml

    return py_obj

def py_name(name):
    name = name.replace(SCHEMA, '')
    name = name.replace('#', '_')
    name = name.replace(':', '_')
    name = name.replace('-', '__')
    name = name.replace('.', '_')
    name = name.replace(' ', '')
    return name

import objectify
cl_cache = {}
def createPyObj(s):
    """Return a new XML Python object (much faster than original)"""

    # does the tag-named class exist, or should we create it?
    klass = '_XO_'+py_name(s)
    try:
        return objectify.__dict__.get(klass)()
    except:
        pass

    cl = cl_cache.get(klass) # already cached?
    if cl is None:
        cl = globals().get(klass) # already defined?
        if cl is None:
            exec ('class %s(_XO_): pass' % klass)
            cl = locals()[klass]
            cl.PCDATA = None
            cl._seq = None
        cl_cache[klass] = cl
    # create an instance of the tag-named class

    return cl()

def _dir(o):
    try:
        return o.__dict__.keys()
    except:
        return []

#-- Self-test utility functions
def pyobj_printer(py_obj, level=0):
    """Return a "deep" string description of a Python object"""
    if level==0: descript = '-----* '+py_obj.__class__.__name__+' *-----\n'
    else: descript = ''
    if hasattr(py_obj, '_XML'):     # present the literal XML of object
        prettified_XML = ' '.join(py_obj._XML.split())[:50]
        descript = (' '*level)+'CONTENT='+prettified_XML+'...\n'
    else:                           # present the object hierarchy view
        for membname in _dir(py_obj):
            if membname in ("__parent__", "_seq"):
               continue             # ExpatFactory uses bookeeping attribute
            member = getattr(py_obj,membname)
            if type(member) == InstanceType:
                descript += '\n'+(' '*level)+'{'+membname+'}\n'
                descript += pyobj_printer(member, level+3)
            elif type(member) == ListType:
                for i in range(len(member)):
                    descript += '\n'+(' '*level)+'['+membname+'] #'+str(i+1)
                    descript += (' '*level)+'\n'+pyobj_printer(member[i],level+3)
            else:
                descript += (' '*level)+membname+'='
                memval = ' '.join(unicode(member).split())
                if len(memval) > 50:
                    descript += memval[:50]+'...\n'
                else:
                    descript += memval + '\n'
    return descript

