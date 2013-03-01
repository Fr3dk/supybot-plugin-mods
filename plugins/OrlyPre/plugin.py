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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import urllib2
import re
import datetime
import BeautifulSoup

class OrlyPre(callbacks.Plugin):
    """Add the help for "@plugin help OrlyPre" here
    This should describe *how* to use this plugin."""
    threaded = True
    url_base = u'http://www.orlydb.com/'
    dupe_limit = 10
    pre_limit = 1
    time_reg = re.compile(r'(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2}) (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})')

    def __init__(self, irc):
        self.__parent = super(OrlyPre, self)
        self.__parent.__init__(irc)

    def _fix(self, qry):
        return qry.replace('-',' ')

    def pre(self, irc, msg, args, limit, query):
        """pre (<limit>) <query>"""
        query = self._fix(query)
        data = self._request(''.join(query or '').replace(' ','+'))
        if data is False:
            irc.reply(u'Error connecting to host.')
        elif data:
            releases = self._parse(data, 'pre', limit)
            if releases:
                for release in releases:
                    irc.reply(self._parseRelease(release))
            else:
                irc.reply(u'No results found.')
        else:
            irc.reply(u'Server returned no data.')
    pre = wrap(pre, [optional('positiveInt', 1) ,optional('text', '')])

    def dupe(self, irc, msg, args, query):
        """dupe <query>"""
        query = self._fix(query)
        data = self._request(''.join(query or '').replace(' ','+'))
        if data is False:
            irc.reply(u'Error connecting to host.')
        elif data:
            releases = self._parse(data, 'dupe', self.dupe_limit)
            if releases:
                irc.reply(u'Results are being queried to you.')
                for release in releases:
                    irc.reply(self._parseRelease(release), private=True)
            else:
                irc.reply(u'No results found.')
        else:
            irc.reply(u'Server returned no data.')
    dupe = wrap(dupe, ['text'])

    def _parseRelease(self, release):
        if not release['info']:
            release['info'] = ''
        else:
            release['info'] = ' \002[\002%s\002]\002' % release['info']
        if not release['nuke']:
            release['nuke'] = ''
        else:
            release['nuke'] = ' [\002%s\002]' % release['nuke']
        return u'\002[\002%s\002]\002 \002[\002%s\002]\002 \002[\002pred \002%s\002 ago\002]\002 \002[\002%s\002]\002%s%s' % (release['section'], release['name'], self._parseTime(release['time']), release['time'], release['info'], release['nuke'])

    def _parse(self, data, type, limit):
        try:
            limit = int(limit)
        except:
            if type == 'dupe':
                limit = self.dupe_limit
            else:
                limit = self.pre_limit
        soup = BeautifulSoup.BeautifulSoup(''.join(data))
        parent = soup.find('div', id='releases')
        if parent:
            releaseDivs = parent.findAll('div', id=None, limit=limit)
            if releaseDivs:
                returnData = []
                for releaseDiv in releaseDivs:
                    releaseTime = releaseDiv.find('span', { 'class' : 'timestamp' }).text
                    releaseSection = releaseDiv.find('span', { 'class' : 'section' }).find('a').text
                    releaseName = releaseDiv.find('span', { 'class' : 'release' }).text
                    releaseInfo = releaseDiv.find('span', { 'class' : 'info' })
                    if releaseInfo:
                        releaseInfo = releaseInfo.text
                    releaseNuke = releaseDiv.find('span', { 'class' : 'nuke' })
                    if releaseNuke:
                        releaseNuke = releaseNuke.text
                    returnData.append({
                        'time': releaseTime or u"",
                        'section': releaseSection or u"",
                        'name': releaseName or u"",
                        'info': releaseInfo or u"",
                        'nuke': releaseNuke or u""
                    })
                return returnData
        return None

    def _request(self, query):
        try:
            req = urllib2.urlopen('%s%s%s' % (self.url_base,u'?q=',str(query)))
        except:
            return False
        else:
            data = req.read()
        return data

    def _parseTime(self, timestamp):
        match = self.time_reg.match(timestamp)
        seconds = 0
        if match:
            date = match.groupdict()
            now = datetime.datetime.now()
            past = datetime.datetime(int(date['year']), int(date['month']), int(date['day']), int(date['hour']), int(date['minute']), int(date['second']))
            diff = now - past
            seconds = diff.days * 86400 + diff.seconds
        return self._elapsed(seconds)

    def _elapsed(self, seconds, suffixes=['y','w','d','h','m','s'], add_s=False, separator=' '):
        """
        Takes an amount of seconds and turns it into a human-readable amount of time.
        """
        # the formatted time string to be returned
        time = []
        # the pieces of time to iterate over (days, hours, minutes, etc)
        # - the first piece in each tuple is the suffix (d, h, w)
        # - the second piece is the length in seconds (a day is 60s * 60m * 24h)
        parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
              (suffixes[1], 60 * 60 * 24 * 7),
              (suffixes[2], 60 * 60 * 24),
              (suffixes[3], 60 * 60),
              (suffixes[4], 60),
              (suffixes[5], 1)]
        # for each time piece, grab the value and remaining seconds, and add it to
        # the time string
        for suffix, length in parts:
            value = seconds / length
            if value > 0:
                seconds = seconds % length
                time.append('%s%s' % (str(value), (suffix, (suffix, suffix + 's')[value > 1])[add_s]))
            if seconds < 1:
                break
        return separator.join(time)

Class = OrlyPre


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
