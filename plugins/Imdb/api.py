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

import json
import requests

import supybot.ircutils

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Imdb')
except ImportError:
    _ = lambda x:x


class ImdbApi(object):
    name = None
    url = None
    fields = None
    errors = {
        'connection': _('Error connecting to API.'),
        'response': _('Error loading API response.'),
    }

    def __init__(self, plugin):
        self.plugin = plugin

    def load_response(self, req):
        raise NotImplementedError

    def fetch(self, mid):
        response = requests.get(self.url.format(mid=mid))
        try:
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            return self.errors['connection']
        return self.load_response(response)

    def clean_value(self, value):
        return supybot.ircutils.safeArgument(value)

    def format_field(self, value, title):
        if isinstance(value, list):
            value = ', '.join(self.clean_value(v) for v in value)
        else:
            value = self.clean_value(value)
        return '{0} {1}'.format(supybot.ircutils.bold(title), value)

    def format_result(self, result):
        separator = self.plugin.registryValue('resultSeparator')
        return separator.join(self.format_field(result[key], title)
                              for title, key in self.fields if key in result)

    def reply(self, irc, mid):
        result = self.fetch(mid)
        if isinstance(result, dict):
            irc.reply(self.format_result(result))
        else:
            irc.reply(result)


class OmdbApi(ImdbApi):
    name = 'omdb'
    url = 'http://www.omdbapi.com/?i=tt{mid}'
    fields = (
        ('[\x0305iMDB\x03]', 'Title',),
        ('Year', 'Year',),
        ('Rated', 'Rated',),
        ('Released', 'Released',),
        ('Genre', 'Genre',),
        ('Runtime', 'Runtime',),
        ('Director', 'Director',),
        ('Rating', 'imdbRating',),
        ('Votes', 'imdbVotes',),
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
    name = 'deanclatworthy'
    url = 'http://deanclatworthy.com/imdb/?id=tt{mid}'
    fields = (
        ('[\x0305iMDB\x03]', 'title',),
        ('Year:', 'year',),
        ('Genre:', 'genres',),
        ('Country:', 'country',),
        ('Language:', 'languages',),
        ('Rating:', 'rating',),
        ('Votes:', 'votes',),
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
    name = 'mymovie'
    url = 'http://mymovieapi.com/?id=tt{mid}&type=json&plot=none&episode=0'
    fields = (
        ('[\x0305iMDB\x03]', 'title',),
        ('Year:', 'year',),
        ('Genre:', 'genres',),
        ('Country:', 'country',),
        ('Language:', 'language',),
        ('Rating:', 'rating',),
        ('Votes:', 'rating_count',),
    )

    def load_response(self, response):
        try:
            response = json.loads(response.text)
        except ValueError:
            return self.errors['response']
        if 'code' in response:
            return response['error']
        return response

choices = {s.name: s for s in ImdbApi.__subclasses__()}

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
