#!/usr/bin/env python
# -*- coding: utf-8 -*-

###
# Copyright (c) 2010, melodeath
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import sqlite3 as sqlite
import random

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class Kolesa(callbacks.Plugin):
    """Add the help for "@plugin help Kolesa" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        """Tryies to connect do database, if db not exists, it will create one. It will also create cursor and table if needed."""
        self.__parent = super(Kolesa, self)
        self.__parent.__init__(irc)
        self.conn = sqlite.connect(self.registryValue('dbName'),check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._createTable()
          
    def _createTable(self):
        """Creates the new table if not exists."""
        return self.cursor.execute('CREATE TABLE IF NOT EXISTS kolesa (id INTEGER PRIMARY KEY,text TEXT)')
    
    def _toUnicode(self, string, encodings = ['utf-8','cp1250']):
        """Returns the unicode string."""
        if isinstance(string, basestring):
            if not isinstance(string, unicode):
                for encoding in encodings:
                    try:
                        string = unicode(string, encoding)
                    except UnicodeError:
                        pass
                    else:
                        break
        return string
    
    def _fromUnicode(self, string, encodings = ['utf-8','cp1250']):
        """Encodes from unicode string."""
        for encoding in encodings:
            try:
                string = string.encode(encoding)
            except UnicodeError:
                pass
            else:
                break
        return string
        
    def _formatQuote(self, quote):
        """ Returns formatted quote. """
        return '#%s: %s' % (quote[0],self._fromUnicode(quote[1]))
        
    def _getRandFromList(self, fromlist):
        """ Returns random record from given list. """
        return fromlist.pop(random.randrange(len(fromlist)))
    
    def _getQuote(self, get):
        """Returns quote by <get> id."""
        # try to select record with <get> id
        self.cursor.execute('SELECT id,text FROM kolesa WHERE id LIKE (?) LIMIT 1',(int(get),))
        # try to fetch it
        row = self.cursor.fetchone()
        # if record was fetched, return it
        if row is not None:
            return self._formatQuote(row)
        # if no record with <get> id was found, return False
        else:
            return 'No kolesa quote with this id.'
            
    def _randomQuote(self):
        """ Returns a random quote to channel."""
        # try to select random quote
        self.cursor.execute('SELECT id,text FROM kolesa ORDER BY RANDOM() LIMIT 1')
        # try to fetch it
        row = self.cursor.fetchone()
        # if record was fetched, return it
        if row is not None:
            return self._formatQuote(row)
        # if no record was fetched return False
        else:
            return 'No kolesa quotes in db.'
            
    def _searchQuote(self, search):
        """Returns quote which is matching <search>."""
        # we want to search in full string
        search = self._toUnicode(search)
        # try to select records
        self.cursor.execute('SELECT id,text FROM kolesa WHERE text LIKE (?)',('%' + search + '%',))
        # get the results and its count
        result = self.cursor.fetchall()
        count = len(result)
        # if we got one result return it
        if(count == 1):
            return self._formatQuote(self._boldSearch(result[0],search))
        # if we got more than one result return random one
        elif(count > 1):
            return self._formatQuote(self._boldSearch(self._getRandFromList(result),search))
        # no results
        else:
            return 'No kolesa quote is matching this query.'
        
    def _boldSearch(self, quote, search):
        return [quote[0],quote[1].replace(search,'' + search + '')]
        
    def addkolesa(self, irc, msg, args, addkolesa):
        """Inserts the <addkolesa> into db."""
        addkolesa = self._toUnicode(addkolesa)
        # try to insert record
        if(self.cursor.execute('INSERT INTO kolesa VALUES (null, ?)',(addkolesa,))):
            # if everything went fine, commit and send message to channel
            self.conn.commit()
            irc.reply('Kolesa quote added.')
        else:
            # if something went wrong send error message to channel
            irc.reply('There was an error adding kolesa quote.')
        
    addkolesa = wrap(addkolesa,['text'])
    
    def delkolesa(self, irc, msg, args, delkolesa):
        """Deletes the <delkolesa> from db."""
        # try to delete record
        if(self.cursor.execute('DELETE FROM kolesa WHERE id LIKE (?)',(int(delkolesa),))):
            # if everything went fine, commit and send message to channel
            self.conn.commit()
            irc.reply('Kolesa quote #%s deleted.' % (int(delkolesa)))
        else:
            # if something went wrong send error message to channel
            irc.reply('There was an error deleting kolesa quote.')
        
    delkolesa = wrap(delkolesa,['int'])
    
    def kolesa(self, irc, msg, args, kolesa):
        """If <kolesa> is int returns quote by id. If it is text returns it by text search and if its None returns random quote."""
        # if <kolesa> is None that means we want to show random quote
        if(kolesa == None):
            irc.reply(self._randomQuote())
        else:
            try:
                # try to convert <kolesa> to int
                isInt = int(kolesa)
            except ValueError:
                # this means that the <kolesa> is not int
                isInt = False
            
            if(isInt):
                irc.reply(self._getQuote(kolesa))
            else:
                irc.reply(self._searchQuote(kolesa))
    
    kolesa = wrap(kolesa,[additional('text')])
    
    def kolesastats(self, irc, msg, args):
        """ Sends row count to channel. """
        # select all quotes
        if(self.cursor.execute('SELECT id FROM kolesa')):
            # send row count if there where some rows found
            irc.reply('Kolesa stats: %s' % (len(self.cursor.fetchall())))
        else:
          # if werent send message
            irc.reply('There arent any quotes in kolesa db.')
          
    def lastkolesa(self, irc, msg, args):
        """ Sends last quote to channel. """
        # select last quote
        select = self.cursor.execute('SELECT id,text FROM kolesa ORDER BY id DESC')
        # send last row if there is one
        lastrow = self.cursor.fetchone()
        # if we got something
        if lastrow is not None:
            # send it to channel
            irc.reply(self._formatQuote(lastrow))
        else:
            # send response message to channel
            irc.reply('There arent any quotes in kolesa db.')

Class = Kolesa


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
