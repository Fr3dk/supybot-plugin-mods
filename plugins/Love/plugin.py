###
# Copyright (c) 2010, jbub
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

def getFeedName(irc, msg, args, state):
    if not registry.isValidRegistryName(args[0]):
        state.errorInvalid('love name', args[0],
                           'Love names must not include spaces.')
    state.args.append(callbacks.canonicalName(args.pop(0)))
addConverter('loveName', getFeedName)

class Love(callbacks.Plugin):
    """Add the help for "@plugin help Love" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def __init__(self, irc):
        """ Tryies to connect do database, if db not exists, it will create one. It will also create cursor and table if needed. """
        
        self.__parent = super(Love, self)
        self.__parent.__init__(irc)

        self.conn = sqlite.connect('love.db',check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._createTable()
          
    def _createTable(self):
        """ Creates the new table if not exists. """
        return self.cursor.execute('CREATE TABLE IF NOT EXISTS love (id INTEGER PRIMARY KEY,name TEXT,url TEXT)')
    
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
    
    def _randomLove(self, key, useId):
        """Returns the random love."""
        if key is not None:
            if useId:
                self.cursor.execute('SELECT id,name,url FROM love WHERE id LIKE (?) LIMIT 1',(int(key),))
            else:
                self.cursor.execute('SELECT id,name,url FROM love WHERE name LIKE (?) ORDER BY RANDOM() LIMIT 1',(key,))
        else:
            self.cursor.execute('SELECT id,name,url FROM love ORDER BY RANDOM() LIMIT 1')
        row = self.cursor.fetchone()
        if row is not None:
            return self._formatLove(row)
        return 'This query returned no results.'
    
    def _formatLove(self, row):
        """Returns formatted record."""
        if isinstance(row,tuple):
            return ('Love #%s - %s - %s' % (str(row[0]),row[1],row[2]))
        return 'This query returned corrupted record.'
    
    def _removeLove(self, id):
        """Deletes the record by id."""
        if self.cursor.execute('DELETE FROM love WHERE id LIKE (?)',(id,)):
            return 'Record was deleted successfully.'
        return 'There is no such record with this id.'
    
    def _stats(self):
        """Returns db stats."""
        count = 0
        if self.cursor.execute('SELECT COUNT(*) as count FROM love'):
            result = self.cursor.fetchone()
            if result is not None:
                count = result[0]
        return ('Lovestats: %s' % (str(count)))
    
    def _lastLove(self):
        """Returns last added love."""
        if self.cursor.execute('SELECT MAX(id) as id,name,url FROM love'):
            row = self.cursor.fetchone()
            if row is not None:
                return self._formatLove(row)
        return 'This query returned no results.'
        
    def addlove(self, irc, msg, args, name, url):
        """<name> <url> Adds the new record."""
        if(self.cursor.execute('INSERT INTO love VALUES (null,?,?)',(self._toUnicode(name),self._toUnicode(url)))):
            self.conn.commit()
            irc.reply('New record was added successfully.')
        else:
            irc.reply('There was some error adding new record.')
            
    addlove = wrap(addlove,['somethingWithoutSpaces','url'])
            
    def love(self, irc, msg, args, key):
        """If <key> is passed, returns random record by <key> or id otherwise returns random record from whole db."""
        if key is not None:
            try:
                id = int(key)
            except ValueError:
                # string key
                key = self._toUnicode(key)
                irc.reply(self._randomLove(key,False))
            else:
                # integer key
                irc.reply(self._randomLove(id,True))
        else:
            irc.reply(self._randomLove(None,False))
           
    love = wrap(love,[additional('text')])
    
    def lovestats(self, irc, msg, args):
        """Returns db stats."""
        irc.reply(self._stats())
        
    def lastlove(self, irc, msg, args):
        """Returns last added love."""
        irc.reply(self._lastLove())
        
    def dellove(self, irc, msg, args, id):
        """Removes the record by id."""
        try:
            id = int(id)
        except ValueError:
            pass
        else:
            irc.reply(self._removeLove(id))
            
    dellove = wrap(dellove,['int'])


Class = Love


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
