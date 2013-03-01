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

import urllib2
import re

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.schedule as schedule

class Radio(callbacks.Plugin):
    """Add the help for "@plugin help Radio" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Radio, self)
        self.__parent.__init__(irc)
        self.url = 'http://calloffreedomradio.com/automat/playing.php'
        self.interval = 120
        self.eventname = 'event'
        self.isAuto = False
        self.lastSong = ''

        self.data = [ ['listeners',r'Current listeners ([0-9]+) <br>'],
                      ['song',r'<td ><font size="2" color="#003366"><small>([^<]+)</small></font></td>'],
                      ['album',r'<td nowrap><font color="#003366" size="2"><small>([^<]+)</small></font></td>'] ]

    def _makeCommandFunction(self, irc, msg, command):
        """Makes a function suitable for scheduling from command."""
        tokens = callbacks.tokenize(command)
        def f():
            self.Proxy(irc.irc, msg, tokens)
        return f

    def _update(self):
        """Returns response from the server."""
        data = ''
        try:
            response = urllib2.urlopen(self.url)
            data = response.read()
        except urllib2.URLError:
            return 'NO_NETWORK'
        finally:
            if data != '':
                return data
        return 'NO_DATA'

    def _connected(self,session):
        """Returns true on connected."""
        return session != 'NO_NETWORK' and session != 'NO_DATA'

    def _info(self,type):
        """Returns parsed data."""
        ret = ''
        result = []
        data = self._update()

        if self._connected(data):
            for item in self.data:
                search = re.search(item[1],data,re.M)

                if search is not None:
                    result.append([item[0],search.group(1)])
                else:
                    result.append([item[0],'N/A'])

            if type == 'np':
                ret = 'Now playing: %s from album: %s' % (result[1][1],result[2][1])
            else:
                ret = 'Current listeners: %s' % (result[0][1])
        else:
            return False

        return ret

    def getinterval(self, irc, msg, args):
        """Returns the current interval."""
        irc.reply('Current auto announce interval is: %d' % (self.interval))

    def setinterval(self, irc, msg, args, interval):
        """Setter for the auto announce interval."""
        try:
            self.interval = int(interval)
            irc.reply('Interval is now set to: %d' % (self.interval))
        except ValueError:
            pass

    setinterval = wrap(setinterval, ['positiveInt'])

    def startauto(self, irc, msg, args):
        """Starts the auto announce."""
        if self.isAuto is not True:
            function = self._makeCommandFunction(irc, msg, 'bindnp')
            self.id = schedule.addPeriodicEvent(function, self.interval, self.eventname)
            self.isAuto = True
            irc.reply('Auto announce is now enabled.')
        else:
            irc.reply('Auto announce is already enabled.')

    def cancelauto(self, irc, msg, args):
        """Cancels the auto announce."""
        if self.isAuto is True:
            if self.id is not None:
                try:
                    schedule.removeEvent(self.id)
                    self.isAuto = False
                    irc.reply('Auto announce is now disabled.')
                except:
                    irc.error('Invalid event id.')
            else:
                irc.error('Invalid event id.')
        else:
            irc.reply('Auto announce is not enabled.')

    def forcecancel(self, irc, msg, args):
        schedule.removeEvent(self.eventname)
        self.isAuto = False
        irc.reply('Auto should be of now :).')

    def np(self, irc, msg, args):
        """Returns the current song and album playing."""
        info = self._info('np')

        if info is not False:
            irc.reply(info)
        else:
            irc.reply('Cant fetch the info.')

    def count(self, irc, msg, args):
        """Returns the current listeners count."""
        info = self._info('count')

        if info is not False:
            irc.reply(info)
        else:
            irc.reply('Cant fetch the info.')

    def bindnp(self, irc, msg, args):
        """Returns the current song and album playing if the last song wasnt the same."""
        info = self._info('np')

        if info is not False:
            if self.lastSong == info:
                pass
            else:
                irc.reply(info)
                self.lastSong = info

Class = Radio


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
