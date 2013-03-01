###
# Copyright (c) 2002-2004, Jeremiah Fincher
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
import supybot.dbi as dbi
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

class OnlyInChannels(object):
    def __init__(self, channels=[], silent_fail=False, channel_config=False):
        self.channels = channels
        self.config_channels = []
        self.silent_fail = silent_fail
        self.channel_config = channel_config

    def __call__(self, fn):
        def wrapped_fn(*args, **kwargs):
            try:
                # grab plugin and irc instances, get current channel also
                plugin, irc, channel = args[0], args[1], args[2].args[0]
            except IndexError:
                return
            config_channels = []
            if self.channel_config:
                # try to grab channels from plugin config
                from supybot.registry import NonExistentRegistryEntry
                try:
                    config_channels = plugin.registryValue('allowedChannels')
                except NonExistentRegistryEntry:
                    pass
            # merge config and passed channels
            for chan in config_channels:
                if chan not in self.channels:
                    self.channels.append(chan)
            # check whether the channel is in passed channels or plugin config
            if channel not in self.channels:
                if not self.silent_fail:
                    irc.reply('This command is not allowed in this channel.')
                return
            fn(*args, **kwargs)
        wrapped_fn.__name__ = fn.__name__
        wrapped_fn.__dict__.update(fn.__dict__)
        wrapped_fn.__doc__ = fn.__doc__
        wrapped_fn.__module__ = fn.__module__
        return wrapped_fn

class UrlRecord(dbi.Record):
    __fields__ = [
        ('url', eval),
        ('by', eval),
        ('near', eval),
        ('at', eval),
        ]

class DbiUrlDB(plugins.DbiChannelDB):
    class DB(dbi.DB):
        Record = UrlRecord
        def add(self, url, msg):
            record = self.Record(url=url, by=msg.nick,
                                 near=msg.args[1], at=msg.receivedAt)
            super(self.__class__, self).add(record)
        def urls(self, p):
            L = list(self.select(p))
            L.reverse()
            return L

URLDB = plugins.DB('URL', {'flat': DbiUrlDB})

class URL(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(URL, self)
        self.__parent.__init__(irc)
        self.db = URLDB()
        self.url_cache = None

    @OnlyInChannels(silent_fail=True, channel_config=True)
    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if irc.isChannel(channel):
            if ircmsgs.isAction(msg):
                text = ircmsgs.unAction(msg)
            else:
                text = msg.args[1]
            if self.url_cache is None:
                self.url_cache = self.db.urls(channel, lambda p: True)
            add = True
            for url in utils.web.urlRe.findall(text):
                r = self.registryValue('nonSnarfingRegexp', channel)
                if r and r.search(url):
                    self.log.debug('Skipping adding %u to db.', url)
                    continue
                for url_check in self.url_cache:
                    if url.lower() == url_check.url.lower():
                        add = False
                        break
                if add:
                    self.log.debug('Adding %u to db.', url)
                    self.db.add(channel, url, msg)
                    self.url_cache = self.db.urls(channel, lambda p: True)
                add = True

    def _filter(self, channel, url_from=None, url_near=None, url_with=None, url_without=None, url_limit=None):
        """ Url db filter. """
        limit = 5
        url_filters = []
        if url_from is not None:
            url_filters.append(lambda record, arg=url_from: ircutils.strEqual(record.by, arg))
        if url_near is not None:
            url_filters.append(lambda record, arg=url_near: arg.lower() in record.near.lower())
        if url_with is not None:
            url_filters.append(lambda record, arg=url_with: arg.lower() in record.url.lower())
        if url_without is not None:
            url_filters.append(lambda record, arg=url_without: arg.lower() not in record.url.lower())
        if url_limit is not None:
            try:
                limit = int(url_limit)
            except ValueError:
                pass
        def predicate(record):
            for url_filter in url_filters:
                if not url_filter(record):
                    return False
            return True
        urls = [record for record in self.db.urls(channel, predicate)]
        return urls[:limit]
    
    @OnlyInChannels(silent_fail=True, channel_config=True)
    def stats(self, irc, msg, args, channel):
        """[<channel>]

        Returns the number of URLs in the URL database.  <channel> is only
        required if the message isn't sent in the channel itself.
        """
        self.db.vacuum(channel)
        count = self.db.size(channel)
        irc.reply(format('I have %n in my database.', (count, 'URL')))
    stats = wrap(stats, ['channeldb'])

    @OnlyInChannels(silent_fail=True, channel_config=True)
    def urls(self, irc, msg, args, limit):
        """" Returns last [<limit>] urls."""
        channel = msg.args[0]
        urls = self._filter(channel=channel, url_limit=limit)
        if not urls:
            irc.reply('No URLs matched that criteria.')
        else:
            for url in urls:
                irc.reply(url.url)
    urls = wrap(urls, [additional('positiveInt')])

    @OnlyInChannels(silent_fail=True, channel_config=True)
    def urlfrom(self, irc, msg, args, author, limit):
        """ Returns urls from <author>. """
        channel = msg.args[0]
        urls = self._filter(channel=channel, url_from=author, url_limit=limit)
        if not urls:
            irc.reply('No URLs matched that criteria.')
        else:
            for url in urls:
                irc.reply(url.url)
    urlfrom = wrap(urlfrom, ['somethingWithoutSpaces', additional('positiveInt')])

    @OnlyInChannels(silent_fail=True, channel_config=True)
    def urlnear(self, irc, msg, args, near, limit):
        """ Returns urls near <near>. """
        channel = msg.args[0]
        urls = self._filter(channel=channel, url_near=near, url_limit=limit)
        if not urls:
            irc.reply('No URLs matched that criteria.')
        else:
            for url in urls:
                irc.reply(url.url)
    urlnear = wrap(urlnear, ['somethingWithoutSpaces', additional('positiveInt')])

    @OnlyInChannels(silent_fail=True, channel_config=True)
    def urlwith(self, irc, msg, args, url_with, limit):
        """ Returns urls with <url_with>. """
        channel = msg.args[0]
        urls = self._filter(channel=channel, url_with=url_with, url_limit=limit)
        if not urls:
            irc.reply('No URLs matched that criteria.')
        else:
            for url in urls:
                irc.reply(url.url)
    urlwith = wrap(urlwith, ['somethingWithoutSpaces', additional('positiveInt')])

    @OnlyInChannels(silent_fail=True, channel_config=True)
    def urlwithout(self, irc, msg, args, url_without, limit):
        """ Returns urls without <url_without>. """
        channel = msg.args[0]
        urls = self._filter(channel=channel, url_without=url_without, url_limit=limit)
        if not urls:
            irc.reply('No URLs matched that criteria.')
        else:
            for url in urls:
                irc.reply(url.url)
    urlwithout = wrap(urlwithout, ['somethingWithoutSpaces', additional('positiveInt')])

Class = URL

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
