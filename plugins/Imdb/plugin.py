###
# Copyright (c) 2013, jbub
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

import re
import json
import requests

import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Imdb')
except:
    _ = lambda x:x

IMDB_REGEX = re.compile('http:\/\/www\.imdb\.com\/title\/tt(\d+)\/?')
SEPARATOR = u' :: '


class ImdbApi(object):
    url = None
    fields = None
    errors = {
        'connection': _('Error connecting to API.'),
        'response': _('Error loading API response.'),
    }

    def load_response(self, req):
        raise NotImplementedError

    def fetch(self, mid):
        response = requests.get(self.url.format(mid=mid))
        try:
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            return self.errors['connection']
        return self.load_response(response)

    def format_field(self, value, title):
        if isinstance(value, list):
            value = u', '.join(value)
        return u'\x02{0}:\x02 {1}'.format(title, value)

    def format_result(self, result):
        return SEPARATOR.join(self.format_field(result[key], title)
                              for title, key in self.fields if key in result)

    def reply(self, irc, mid):
        result = self.fetch(mid)
        if isinstance(result, dict):
            irc.reply(self.format_result(result))
        else:
            irc.reply(result)


class OmdbApi(ImdbApi):
    url = 'http://www.omdbapi.com/?i=tt{mid}'
    fields = (
        (u'Title', u'Title',),
        (u'Year', u'Year',),
        (u'Rated', u'Rated',),
        (u'Released', u'Released',),
        (u'Genre', u'Genre',),
        (u'Runtime', u'Runtime',),
        (u'Director', u'Director',),
        (u'Rating', u'imdbRating',),
        (u'Votes', u'imdbVotes',),
    )

    def load_response(self, response):
        try:
            response = json.loads(response.text)
        except ValueError:
            return self.errors['response']
        if response.get('Response') == 'False':
            return response['Error']
        return response


class DeanClatworthyApi(ImdbApi):
    url = 'http://deanclatworthy.com/imdb/?id=tt{mid}'
    fields = (
        (u'Title', u'title',),
        (u'Year', u'year',),
        (u'Genre', u'genres',),
        (u'Country', u'country',),
        (u'Runtime', u'runtime',),
        (u'Rating', u'rating',),
        (u'Votes', u'votes',),
    )

    def load_response(self, response):
        try:
            response = json.loads(response.text)
        except ValueError:
            return self.errors['response']
        if 'code' in response:
            return response['error']
        return response


class MyMovieApi(ImdbApi):
    url = 'http://mymovieapi.com/?id=tt{mid}&type=json&plot=none&episode=0'
    fields = (
        (u'Title', u'title',),
        (u'Year', u'year',),
        (u'Genre', u'genres',),
        (u'Country', u'country',),
        (u'Runtime', u'runtime',),
        (u'Rating', u'rating',),
        (u'Votes', u'rating_count',),
    )

    def load_response(self, response):
        try:
            response = json.loads(response.text)
        except ValueError:
            return self.errors['response']
        if 'code' in response:
            return response['error']
        return response


class Imdb(callbacks.Plugin):
    threaded = True

    def doPrivmsg(self, irc, msg):
        if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
            return
        channel = msg.args[0]
        if irc.isChannel(channel):
            if ircmsgs.isAction(msg):
                text = ircmsgs.unAction(msg)
            else:
                text = msg.args[1]
            mids = set(IMDB_REGEX.findall(text))
            if mids:
                api = MyMovieApi()
                for mid in mids:
                    api.reply(irc, mid)

Class = Imdb

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
