"""
    Copyright 2007 Greg L. Turnquist, All Rights Reserved

    springbot is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import cPickle
import ircbot
import re

class DictionaryBot(ircbot.SingleServerIRCBot):
    def __init__(self, server_list, channel, ops, logfile, nickname, realname):
        ircbot.SingleServerIRCBot.__init__(self, server_list, nickname, realname)
        self.datastore = "%s.data" % self._nickname
        self.channel = channel
        self.definition = {}
        try:
            f = open(self.datastore, "r")
            self.definition = cPickle.load(f)
            f.close()
        except IOError:
            pass
        self.whatIsR = re.compile(",?\s*[Ww][Hh][Aa][Tt]\s*[Ii][Ss]\s+([\w ]+)[?]?")
        self.definitionR = re.compile(",?\s*([\w ]+)\s+[Ii][Ss]\s+(.+)")
        self.ops = ops
        self.logfile = logfile

    def on_welcome(self, connection, event):
        """This event is generated after you connect to an irc server, and should be your signal to join your target channel."""
        connection.join(self.channel)

    def on_join(self, connection, event):
        """This catches everyone who joins. In this case, my bot has a list of whom to grant op status to when they enter."""
        self._log_event(event)
        source = event.source().split("!")[0]
        if source in self.ops:
            connection.mode(self.channel, "+o %s" % source)

    def on_mode(self, connection, event):
        """No real action here, except to log locally every mode action that happens on my channel."""
        self._log_event(event)

    def on_pubmsg(self, connection, event):
        """This is the real meat. This event is generated everytime a message is posted to the channel."""
        self._log_event(event)

        # Capture who posted the messsage, and what the message was.
        source = event.source().split("!")[0]
        arguments = event.arguments()[0]

        # Some messages are meant to signal this bot to do something.
        if arguments.lower().startswith("!%s" % self._nickname):
            # "What is xyz" command
            match = self.whatIsR.search(arguments[len(self._nickname)+1:])
            if match:
                self._lookup_definition(connection, match.groups()[0])
                return

            # "xyz is blah blah" command
            match = self.definitionR.search(arguments[len(self._nickname)+1:])
            if match:
                self._set_definition(connection, match.groups()[0], match.groups()[1])
                return

        # There are also some shortcut commands, so you don't always have to address the bot.
        if arguments.startswith("!"):
            match = re.compile("!([\w ]+)").search(arguments)
            if match:
                self._lookup_definition(connection, match.groups()[0])
                return

    def getDefinitions(self):
        """This is to support a parallel web app fetching data from the bot."""
        return self.definition

    def _log_event(self, event):
        """Log an event to a flat file. This can support archiving to a web site for past activity."""
        f = open(self.logfile, "a")
        f.write("%s::%s::%s::%s\n" % (event.eventtype(), event.source(), event.target(), event.arguments()))
        f.close()

    def _lookup_definition(self, connection, keyword):
        """Function to fetch a definition from the bot's dictionary."""
        if keyword.lower() in self.definition:
            connection.privmsg(self.channel, "%s is %s" % self.definition[keyword.lower()])
        else:
            connection.privmsg(self.channel, "I have no idea what %s means. You can tell me by sending '!%s, %s is <your definition>'" % (keyword, self._nickname, keyword))

    def _set_definition(self, connection, keyword, definition):
        """Function to store a definition in cache and to disk in the bot's dictionary."""
        self.definition[keyword.lower()] = (keyword, definition)
        connection.privmsg(self.channel, "Got it! %s is %s" % self.definition[keyword.lower()])
        f = open(self.datastore, "w")
        cPickle.dump(self.definition, f)
        f.close()

