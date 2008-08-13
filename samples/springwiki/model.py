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

intrawikiR = re.compile("\[\[(?P<link>.*?)(\|(?P<desc>.*?))?\]\](?P<trail>[a-zA-Z0-9]*)")
externalLinkR = re.compile("\[(?P<link>.*?)\s(?P<description>.*)\]")
header1R = re.compile("=(?P<header>.*)=")
header2R = re.compile("==(?P<header>.*)==")
header3R = re.compile("===(?P<header>.*)===")
header4R = re.compile("====(?P<header>.*)====")
header5R = re.compile("=====(?P<header>.*)=====")

class Page(object):
    def __init__(self, article, wikitext, controller):
        self.article = article
        self.wikitext = wikitext
        self.controller = controller
        
    def makeAList(self, wikitext):
        keyCharR = re.compile("(([*#]+)(.*))")
        tokens = wikitext.split("\n")
        bulletCount = 0
        currentLevel = 0
        
        tagStack = []
        for i in range(1,len(tokens)):
            if tokens[i]:
                match = keyCharR.match(tokens[i])
                if match:
                    token = match.groups()[1]
                    text = match.groups()[2]
                    if len(token) > currentLevel:
                        tokens[i] = ""
                        for j in range(currentLevel, len(token)):
                            if token[j] == "*":
                                tagStack.append("</ul>")
                                tokens[i] += "<ul>"
                            elif token[j] == "#":
                                tagStack.append("</ol>")
                                tokens[i] += "<ol>"
                        tokens[i] += "<li>" + text + "</li>"
                        currentLevel = len(token)
                    elif len(token) < currentLevel:
                        tokens[i] = ""
                        for j in range(len(token), currentLevel):
                            tokens[i] += tagStack.pop()
                        tokens[i] += "<li>" + text + "</li>"
                        currentLevel = len(token)
                    else:
                        if token[-1] == "*":
                            tokens[i] = "<li>" + text + "</li>"
                        elif token[-1] == "#":
                            tokens[i] = "<li>" + text + "</li>"
            else:
                if currentLevel > 0:
                    tokens[i] = ""
                    for j in range(0, currentLevel):
                        tokens[i] += tagStack.pop()
                    currentLevel = 0
        return "\n".join(tokens)
        
    def intrawikiSubstitution(self, match):
        g = match.groupdict()
        
        if self.controller.exists(g["link"]):
            str = '<a href="' + g["link"] + '"'
        else:
            str = '<a href="edit/' + g["link"] + '"'
        
        if not self.controller.exists(g["link"]):
            str += ' class="new" '
        
        str += ">"
            
        if g["desc"]:
            str += g["desc"]
        else:
            str += g["link"]
            
        if g["trail"]:
            str += g["trail"]
            
        if not self.controller.exists(g["link"]):
            str += '</font>'

        str += "</a>"
        return str

    def header(self):
        """Standard header used for all pages"""
        return """
            <!--
            
                SpringWiki :: a Spring Python demonstration (powered by CherryPy)
            
            -->
            
            <html>
            <head>
            <title>SpringWiki :: a Spring Python demonstration</title>
            <!--<link rel="stylesheet" type="text/css" href="styles/springwiki.css"/>-->
            <link rel="stylesheet" type="text/css" href="styles/main.css"/>
            </head>
            
            <body class="ns-0">
                <div id="globalWrapper">
                    <div id="column-content">
                        <div id="content">
                            <a name="top" id="top"></a>
                            <h1 class="firstHeading">""" + self.article + """</h1>
                            <div id="bodyContent">
                                <h3 id="siteSub">From Springwiki</h3>
                                <div id="contentSub"></div>
            """

    def footer(self, selected = "article"):
        """Standard footer used for all pages."""
        footer = """
                                <div class="visualClear"></div>
                            </div>
                        </div>
                    </div>
                    <div id="column-one">
                        <div id="p-cactions" class="portlet">
                            <ul>
            """
            
        if selected == "article" and self.article.split(":")[0] == "Talk":
            selected = "discussion"

        if selected == "article":
            if self.controller.exists(self.article.split(":")[-1]):
                footer += """       <li class="selected" id="ca-nstab-main"><a href="/""" + self.article.split(":")[-1] + """">article</a></li>\n"""
            else:
                footer += """       <li class="selected new" id="ca-nstab-main"><a href="/edit/""" + self.article.split(":")[-1] + """">article</a></li>\n"""
            
            if self.controller.exists("Talk:" + self.article.split(":")[-1]):
                footer += """   <li id="ca-talk"><a href="/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
            else:
                footer += """   <li class="new" id="ca-talk"><a href="/edit/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
            
            
            footer += """       <li id="ca-edit"><a href="/edit/""" + self.article + """">edit</a></li>\n"""
            if self.controller.exists(self.article.split(":")[-1]):
                footer += """
                                <li id="ca-history"><a href="/history/""" + self.article + """">history</a></li>
                                <li id="ca-delete"><a href="/delete/""" + self.article + """">delete</a></li>
                """
        elif selected == "discussion":
            footer += """
                                <li id="ca-nstab-main"><a href="/""" + self.article.split(":")[-1] + """">article</a></li>
                                <li class="selected" id="ca-talk"><a href="/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>
                                <li id="ca-edit"><a href="/edit/""" + self.article + """">edit</a></li>
                """
            if self.controller.exists("Talk:" + self.article.split(":")[-1]):
                footer += """
                                <li id="ca-history"><a href="/history/""" + self.article + """">history</a></li>
                                <li id="ca-delete"><a href="/delete/""" + self.article + """">delete</a></li>
                """
        elif selected == "edit":
            if self.controller.exists(self.article.split(":")[-1]):
                footer += """       <li id="ca-nstab-main"><a href="/""" + self.article.split(":")[-1] + """">article</a></li>\n"""
            else:
                footer += """       <li class="new" id="ca-nstab-main"><a href="/edit/""" + self.article.split(":")[-1] + """">article</a></li>\n"""

            if self.controller.exists("Talk:" + self.article.split(":")[-1]):
                footer += """   <li id="ca-talk"><a href="/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
            else:
                footer += """   <li class="new" id="ca-talk"><a href="/edit/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
                
            footer += """
                                <li class="selected" id="ca-edit"><a href="/edit/""" + self.article + """">edit</a></li>
                """
            if self.controller.exists(self.article):
                footer += """
                                <li id="ca-history"><a href="/history/""" + self.article + """">history</a></li>
                                <li id="ca-delete"><a href="/delete/""" + self.article + """">delete</a></li>
                """
        elif selected == "history":
            footer += """       <li id="ca-nstab-main"><a href="/""" + self.article.split(":")[-1] + """">article</a></li>
                """
                
            if self.controller.exists("Talk:" + self.article.split(":")[-1]):
                footer += """   <li id="ca-talk"><a href="/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
            else:
                footer += """   <li class="new" id="ca-talk"><a href="/edit/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
                
            footer += """
                                <li id="ca-edit"><a href="/edit/""" + self.article + """">edit</a></li>
                                <li class="selected" id="ca-history"><a href="/history/""" + self.article + """">history</a></li>
                                <li id="ca-delete"><a href="/delete/""" + self.article + """">delete</a></li>
                """
        elif selected == "delete":
            footer += """       <li id="ca-nstab-main"><a href="/""" + self.article.split(":")[-1] + """">article</a></li>
                """
            if self.controller.exists("Talk:" + self.article.split(":")[-1]):
                footer += """   <li id="ca-talk"><a href="/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
            else:
                footer += """   <li class="new" id="ca-talk"><a href="/edit/Talk:""" + self.article.split(":")[-1] + """">discussion</a></li>\n"""
            footer += """
                                <li id="ca-edit"><a href="/edit/""" + self.article + """">edit</a></li>
                                <li id="ca-history"><a href="/history/""" + self.article + """">history</a></li>
                                <li class="selected" id="ca-delete"><a href="/delete/""" + self.article + """">delete</a></li>
                """
            
        footer += """
                            </ul>
                        </div><!-- id="p-cactions" -->
                        """ + self.icon() + """
                        """ + self.navigationHeader() + """
                    </div><!-- id="column-one" -->
            
                    <div class="visualClear"></div>
                    
                    <div id="footer">
                        <div id="f-poweredbyico">
                            <a href="http://springpython.webfactional.com">
                                <img src="images/spring_python_white_89x31.png" alt="Spring Python"/>
                            </a>
                        </div><!-- f-poweredbyico -->
                        <ul id="f-list">
                            <li id="f-about">
                                SpringWiki :: a <a href="http://springpython.webfactional.com">Spring Python</a> demonstration (powered by <A HREF="http://www.cherrypy.org">CherryPy</A>)
                            </li>
                        </ul>
                    </div><!-- footer -->
                </div><!-- globalWrapper -->
            </body>
            """
        return footer

    def icon(self):
        return """
            <div class="portlet" id="p-logo">
                <a style="background-image: url(images/spring_python_white_89x31.png);" href="Main Page" title="Main Page"></a>
            </div>
            """

    def navigationHeader(self):
        """Left hand HTML"""
        sidebar = self.controller.getPage("Springwiki Sidebar")
        results = """
            <script type="text/javascript"> if (window.isMSIE55) fixalpha(); </script>
        """
        
        listStack = []
        for eachLine in sidebar.wikitext.split("\n"):
            if len(eachLine) > 1 and eachLine[0:2] == "**":
                temp = re.compile("\[.*\]").findall(eachLine[2:])[0]
                wikiLink = re.compile("[\[]+(.*?)[\]]+").findall(temp)[0]
                if temp[0:2] == "[[":
                    pipe = wikiLink.split("|")[-1]
                    link = wikiLink.split("|")[0]
                    results += """
                                        <li id="n-%s"><a href="/%s">%s</a></li>""" % (link, link, pipe)
                else:
                    pipe = " ".join(wikiLink.split(" ")[1:])
                    link = wikiLink.split(" ")[0]
                    results += """
                                        <li id="n-%s"><a href="%s" class="external text">%s</a></li>""" % (link, link, pipe)
                                
            elif len(eachLine) > 0 and eachLine[0] == "*":
                target = eachLine[1:]
                if len(listStack) > 0:
                    results += """
                                </ul>
                            </div>
                        </div><!-- id='%s' -->""" % listStack[-1]
                    listStack.pop()
                results += """
                        <div class='portlet' id='p-%s'>
                            <h5>%s</h5>
                            
                            <div class='pBody'>
                                <ul>""" % (target, target)
                listStack.append(target)
                
        if len(listStack) > 0:
            results += """
                                </ul>
                            </div>
                        </div><!-- id='%s' -->""" % listStack[-1]
            listStack.pop()
                 
        return results
            
    def wikiToHtml(self):
        htmlText = self.wikitext
        htmlText = header5R.sub('<h5>\g<header></h5>', htmlText)
        htmlText = header4R.sub('<h4>\g<header></h4>', htmlText)
        htmlText = header3R.sub('<h3>\g<header></h3>', htmlText)
        htmlText = header2R.sub('<h2>\g<header></h2>', htmlText)
        htmlText = header1R.sub('<h1>\g<header></h1>', htmlText)
        htmlText = intrawikiR.sub(self.intrawikiSubstitution, htmlText)
        htmlText = externalLinkR.sub('<a href="\g<link>" class="external text">\g<description></a>', htmlText)        
        htmlText = self.makeAList(htmlText)
        return htmlText
    
    def html(self):
        results = self.header()
        results += """
            <!-- BEGIN main content -->
        """
        results += self.wikiToHtml()
        results += """
            <!-- END main content -->
        """
        results += self.footer(selected="article")
        return results
    
class EditPage(Page):
    def __init__(self, article, wikitext, controller):
        Page.__init__(self, article, wikitext, controller)
 
    def header(self):
        """Standard header used for all pages"""
        return """
            <!--
            
                SpringWiki :: a Spring Python demonstration (powered by CherryPy)
            
            -->
            
            <html>
            <head>
            <title>SpringWiki :: a Spring Python demonstration</title>
            <!--<link rel="stylesheet" type="text/css" href="styles/springwiki.css"/>-->
            <link rel="stylesheet" type="text/css" href="styles/main.css"/>
            <script type="text/javascript" src="scripts/wikibits.js"></script>
            </head>
            
            <body class="ns-0">
                <div id="globalWrapper">
                    <div id="column-content">
                        <div id="content">
                            <a name="top" id="top"></a>
                            <h1 class="firstHeading">Editing """ + self.article + """</h1>
                            <div id="bodyContent">
                                <h3 id="siteSub">From Springwiki</h3>
                                <div id="contentSub"></div>
            """
    def wikiToHtml(self):
        htmlText = """
            <script type='text/javascript'>
                document.writeln("<div id='toolbar'>");
                addButton('../images/button_bold.png','Bold text','\'\'\'','\'\'\'','Bold text');
                addButton('/images/button_italic.png','Italic text','\'\'','\'\'','Italic text');
                addButton('images/button_link.png','Internal link','[[',']]','Link title');
                addButton('images/button_extlink.png','External link (remember http:// prefix)','[',']','http://www.example.com link title');
                addButton('images/button_headline.png','Level 2 headline','\n== ',' ==\n','Headline text');
                addButton('images/button_image.png','Embedded image','[[Image:',']]','Example.jpg');
                addButton('images/button_media.png','Media file link','[[Media:',']]','Example.ogg');
                addButton('images/button_math.png','Mathematical formula (LaTeX)','\<math\>','\</math\>','Insert formula here');
                addButton('images/button_nowiki.png','Ignore wiki formatting','\<nowiki\>','\</nowiki\>','Insert non-formatted text here');
                addButton('images/button_sig.png','Your signature with timestamp','--~~~~','','');
                addButton('images/button_hr.png','Horizontal line (use sparingly)','\n----\n','','');
                addInfobox('Click a button to get an example text','Please enter the text you want to be formatted.\\n It will be shown in the infobox for copy and pasting.\\nExample:\\n$1\\nwill become:\\n$2');
                document.writeln("</div>");
            </script>
            """
        htmlText += """
            <form id="editform" name="editform" method="post" action="/submit?article=""" + self.article + """" enctype="multipart/form-data">
                <textarea tabindex='1' accesskey="," name="wpTextbox1" rows='25' cols='80'>""" + self.wikitext + """</textarea>
                <br/>
                Summary: <input tabindex='2' type='text' value="" name="wpSummary" maxlength='200' size='60'/>
                <br/>
                <input tabindex='3' type='checkbox' value='1' name='wpMinoredit' accesskey='i' id='wpMinoredit' /><label for='wpMinoredit' title='Mark this as a minor edit [alt-i]'>This is a minor edit</label><br />
                <input tabindex='5' id='wpSave' type='submit' value="Save page" name="wpSave" accesskey="s" title="Save your changes [alt-s]"/>
                <input tabindex='6' id='wpPreview' type='submit'  value="Show preview" name="wpPreview" accesskey="p" title="Preview your changes, please use this before saving! [alt-p]"/>
                <input tabindex='7' id='wpDiff' type='submit' value="Show changes" name="wpDiff" accesskey="v" title="Show which changes you made to the text. [alt-d]"/>
                <em><a href="/""" + self.article + """" title='""" + self.article + """'>Cancel</a></em>
            </form>
            """
        return htmlText

    def html(self):
        results = self.header()
        results += """
            <!-- BEGIN main content -->
        """
        results += self.wikiToHtml()
        results += """
            <!-- END main content -->
        """
        results += self.footer(selected="edit")
        return results


class PreviewEditPage(Page):
    def __init__(self, article, wikitext, controller):
        Page.__init__(self, article, wikitext, controller)
 
    def header(self):
        """Standard header used for all pages"""
        return """
            <!--
            
                SpringWiki :: a Spring Python demonstration (powered by CherryPy)
            
            -->
            
            <html>
            <head>
            <title>SpringWiki :: a Spring Python demonstration</title>
            <!--<link rel="stylesheet" type="text/css" href="styles/springwiki.css"/>-->
            <link rel="stylesheet" type="text/css" href="styles/main.css"/>
            </head>
            
            <body class="ns-0">
                <div id="globalWrapper">
                    <div id="column-content">
                        <div id="content">
                            <a name="top" id="top"></a>
                            <h1 class="firstHeading">Editing """ + self.article + """</h1>
                            <div id="bodyContent">
                                <h3 id="siteSub">From Springwiki</h3>
                                <div id="contentSub"></div>
            """
    def html(self):
        results = self.header()
        results += '<div id="wikiPreview"><h2>Preview</h2>'
        results += Page(self.article, self.wikitext, self.controller).wikiToHtml()
        results += '<br style="clear:both;" /></div>'
        results += EditPage(self.article, self.wikitext, self.controller).wikiToHtml()
        results += self.footer()
        return results
    
class Version(object):
    def __init__(self, article, versionNumber, wikitext, summary, date, editor):
        self.article = article
        self.versionNumber = versionNumber
        self.wikitext = wikitext
        self.summary = summary
        self.date = date
        self.editor = editor
        
class HistoryPage(Page):
    def __init__(self, article, controller, history):
        Page.__init__(self, article, 'History', controller)
        self.history = []
        for rev in history:
            self.history.append(Version(article=article, versionNumber=len(self.history), wikitext=rev[0], summary=rev[1], date=rev[2], editor=rev[3]))
    
    def header(self):
        """Standard header used for all pages"""
        return """
            <!--
            
                SpringWiki :: a Spring Python demonstration (powered by CherryPy)
            
            -->
            
            <html>
            <head>
            <title>SpringWiki :: a Spring Python demonstration</title>
            <!--<link rel="stylesheet" type="text/css" href="styles/springwiki.css"/>-->
            <link rel="stylesheet" type="text/css" href="styles/main.css"/>
            </head>
            
            <body class="ns-0">
                <div id="globalWrapper">
                    <div id="column-content">
                        <div id="content">
                            <a name="top" id="top"></a>
                            <h1 class="firstHeading">""" + self.article + """</h1>
                            <div id="bodyContent">
                                <h3 id="siteSub">From Springwiki</h3>
                                <div id="contentSub">Revision history</div>
            """
    

    def generateHistory(self):
        print self.history
        results = """
            <p>
                Diff selection: mark the radio boxes of the versions to compare and hit enter or the button at the bottom.<br/>
                Legend: (cur) = difference with current version,
                (last) = difference with preceding version, M = minor edit.
            </p>
            <form action="history" method="get">
                <input class="historysubmit" type="submit" accesskey="v" title="See the differences between the two selected versions of this page. [alt-v]" value="Compare selected versions"/>
                <ul id="pagehistory">
            """
        
        if len(self.history) > 0:
            for rev in reversed(self.history):
                hiddenStyle = ""
                if rev == self.history[-1]:
                    hiddenStyle = 'style="visibility:hidden"'
    
                userStyle = ""
                if self.controller.exists(rev.editor):
                    userStyle = 'class="new"'
    
                try:
                    editor = rev.editor.split(":")[1]
                except:
                    editor = rev.editor
                    
                results += """
                            <li>
                                <input type="radio" value="%s" title="Select an older version for comparison" %s name="oldid"/>
                                <input type="radio" value="%s" title="Select an older version for comparison" name="diff"/>
                                <a href="/%s?oldid=%s">%s</a>
                                <span class='user'><a href="/%s" %s>%s</a></span>
                                <span class='comment'>(->%s</span>)</span>
                            </li>
                        """ % (rev.versionNumber, hiddenStyle, rev.versionNumber, rev.article, rev.versionNumber, rev.date,
                               rev.editor, editor, userStyle, rev.summary)
            
        results += """
                </ul>
                <input id="historysubmit" class="historysubmit" type="submit" accesskey="v" title="See the differences between the two selected versions of this page. [alt-v]" value="Compare selected versions" />
            </form>
            """
        return results
    
    def html(self):
        results = self.header()
        results += """
            <!-- BEGIN main content -->
        """
        results += self.generateHistory()
        results += """
            <!-- END main content -->
        """
        results += self.footer(selected="history")
        return results
    
class OldPage(Page):
     def __init__(self, article, wikitext, controller):
         Page.__init__(self, article, wikitext, controller)
      
class NoPage(Page):
    def __init__(self, article, controller):
        Page.__init__(self, article, "This page does not yet exist.", controller)
        
class DeletePage(Page):
    def __init__(self, article, controller):
        Page.__init__(self, article, "This page does not yet exist.", controller)
    
    def header(self):
        """Standard header used for all pages"""
        return """
            <!--
            
                SpringWiki :: a Spring Python demonstration (powered by CherryPy)
            
            -->
            
            <html>
            <head>
            <title>SpringWiki :: a Spring Python demonstration</title>
            <!--<link rel="stylesheet" type="text/css" href="styles/springwiki.css"/>-->
            <link rel="stylesheet" type="text/css" href="styles/main.css"/>
            </head>
            
            <body class="ns-0">
                <div id="globalWrapper">
                    <div id="column-content">
                        <div id="content">
                            <a name="top" id="top"></a>
                            <h1 class="firstHeading">""" + self.article + """</h1>
                            <div id="bodyContent">
                                <h3 id="siteSub">From Springwiki</h3>
                                <div id="contentSub">(Deleting "%s")</div>
            """ % self.article
            
    def html(self):
        results = self.header()
        results += """
            <!-- BEGIN main content -->
        """
        results += """
            <b>Warning: The page you are about to delete has a history</b>
            <p>
            You are about to permanently delete a page or image along with all of its history from the database.
            Please confirm that you intend to do this, that you understand the consequences.<p>
            <form id='deleteconfirm' method='post' action="/doDelete?article=%s">
                <table border='0'>
                    <tr>            
                        <td align='right'>
                            <label for='wpReason'>Reason for deletion:</label>
                        </td>
                        <td align='left'>
                            <input type='text' size='60' name='wpReason' id='wpReason' value="" />
                        </td>
                    </tr>
                    <tr>
            
                        <td>&nbsp;</td>
                        <td>
                            <input type='submit' name='wpConfirmB' value="Confirm" />
                        </td>
                    </tr>
                </table>
            </form>
            </p>
            <p>Return to <a href="/%s" title="%s">%s</a>.</p>
            """ % (self.article, self.article, self.article, self.article)
        results += """
            <!-- END main content -->
        """
        results += self.footer(selected="delete")
        return results
    
class ActionCompletedPage(Page):
    def __init__(self, article, controller):
        Page.__init__(self, article, "This page does not yet exist.", controller)
    
    def html(self):
        results = self.header()
        results += """
            <!-- BEGIN main content -->
        """
        results += """
            <p>"%s" has been deleted.</p>
            <p>Return to <a href="Main Page" title="Main Page">Main Page</a>.</p>
        """ % self.article

        results += """
            <!-- END main content -->
        """
        results += self.footer(selected="article")
        return results
    
   
