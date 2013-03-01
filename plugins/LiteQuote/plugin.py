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

import supybot.conf as conf
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

QUOTE_NOT_FOUND = u'There are no quotes matching your criteria.'
QUOTE_DB_EMPTY = u'Quote database is empty.'
QUOTE_ADDED = u'Quote has been added successfully.'
QUOTE_NOT_ADDED = u'Quote has not been added successfully.'
QUOTE_DELETED = u'Quote has been deleted successfully.'
QUOTE_NOT_DELETED = u'Quote has not been deleted successfully.'

def check_identify(user, capability):
    try:
        u = ircdb.users.getUser(user)
    except KeyError:
        pass
    else:
        if u._checkCapability(capability):
            return True
    return False
    
def identify(capability):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            if check_identify(args[2].nick, capability):
                return f(*args, **kwargs)
            return args[1].error(conf.supybot.replies.incorrectAuthentication(), Raise=True) 
        return wrapped_f
    return wrap

class LiteQuote(callbacks.Plugin):
    """Simple quote database."""

    def __init__(self, irc):
        self.__parent = super(LiteQuote, self)
        self.__parent.__init__(irc)
        self.conn = sqlite.connect(self.registryValue('dbName'), check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def to_unicode(self, string, encodings = ['utf-8', 'cp1250']):
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

    def from_unicode(self, string, encodings = ['utf-8', 'cp1250']):
        for encoding in encodings:
            try:
                string = string.encode(encoding)
            except UnicodeError:
                pass
            else:
                break
        return string

    def create_table(self):
        return self.cursor.execute('CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY,text TEXT)')

    def format_quote(self, quote):
        return 'Quote #%s: %s' % (quote[0], quote[1])

    def list_random(self, l):
        return l.pop(random.randrange(len(l)))

    def get_quote(self, id):
        id = int(id)
        if self.cursor.execute('SELECT id,text FROM quotes WHERE id LIKE (?) LIMIT 1', (id,)):
            row = self.cursor.fetchone()
            if row:
                return self.format_quote(row)
        return QUOTE_NOT_FOUND

    def get_random_quote(self):
        if self.cursor.execute('SELECT id,text FROM quotes ORDER BY RANDOM() LIMIT 1'):
            row = self.cursor.fetchone()
            if row:
                return self.format_quote(row)
        return QUOTE_DB_EMPTY

    def search_quote(self, search):
        search = u'%' + self.to_unicode(search) + u'%'
        if self.cursor.execute('SELECT id,text FROM quotes WHERE text LIKE (?)', (search,)):
            result = self.cursor.fetchall()
            count = len(result)
            if count == 1:
                return self.format_quote(result[0])
            elif count > 1:
                return self.format_quote(self.list_random(result))
        return QUOTE_NOT_FOUND

       
    def addquote(self, irc, msg, args, text):
        """
        <text> Adds new quote.
        """
        text = self.to_unicode(text)
        if self.cursor.execute('INSERT INTO quotes VALUES (null, ?)', (text,)):
            self.conn.commit()
            irc.reply(QUOTE_ADDED) 
        else:
            irc.reply(QUOTE_NOT_ADDED)
    addquote = wrap(addquote, ['text'])

    @identify("owner")
    def delquote(self, irc, msg, args, id):
        """
        <id> Deletes quote by id.
        """
        id = int(id)
        if self.cursor.execute('DELETE FROM quotes WHERE id = (?)', (id,)):
            self.conn.commit()
            irc.reply(QUOTE_DELETED)
        else:
            irc.reply(QUOTE_NOT_DELETED)
    delquote = wrap(delquote, ['int'])

    def quote(self, irc, msg, args, text):
        """
        <text> Searches quote by id or by text query. Returns random quote by default.
        """
        if not text:
            irc.reply(self.get_random_quote())
            return
        try:
            int(text)
        except ValueError:
            irc.reply(self.search_quote(text))
        else:
            irc.reply(self.get_quote(text))
    quote = wrap(quote, [additional('text')])
    
    def quotestats(self, irc, msg, args):
        """
        Returns database stats.
        """
        if self.cursor.execute('SELECT count(*) as cnt FROM quotes'):
            row = self.cursor.fetchone()
            irc.reply('Quote stats: %s' % row[0])
            return
        irc.reply(QUOTE_DB_EMPTY)
    quotestats = wrap(quotestats)
        
    def lastquote(self, irc, msg, args):
        """
        Returns the last quote.
        """
        if self.cursor.execute('SELECT id,text FROM quotes ORDER BY id DESC LIMIT 1'):
            row = self.cursor.fetchone()
            irc.reply(self.format_quote(row))
            return
        irc.reply(QUOTE_DB_EMPTY)
    lastquote = wrap(lastquote)

Class = LiteQuote

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79: