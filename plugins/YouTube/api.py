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
    _ = PluginInternationalization('YouTube')
except ImportError:
    _ = lambda x:x


class YouTubeApi(object):
    url = 'http://gdata.youtube.com/feeds/api/videos/{yid}?alt=json&v=2'
    errors = {
        'connection': _('Error connecting to API.'),
        'response': _('Error loading API response.'),
    }

    def load_response(self, response):
        try:
            response = json.loads(response.text)
        except ValueError:
            return self.errors['response']
        return response['entry']

    def fetch(self, yid):
        response = requests.get(self.url.format(yid=yid))
        try:
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            return self.errors['connection']
        return self.load_response(response)

    def clean_value(self, value, bold=False):
        value = supybot.ircutils.safeArgument(value)
        if bold:
            value = supybot.ircutils.bold(value)
        return value

    def format_time(self, seconds):
        seconds = int(seconds)
        mins = seconds // 60
        secs = seconds % 60
        together = '{0}:{1}'.format(str(mins).zfill(2), str(secs).zfill(2))
        return '[{0}]'.format(supybot.ircutils.bold(together))

    def format_likes(self, result):
        if 'yt$rating' in result:
            likes = int(result['yt$rating']['numLikes'])
            dislikes = int(result['yt$rating']['numDislikes'])
        elif 'gd$rating' in result:
            likes = int(result['gd$rating']['numLikes'])
            dislikes = int(result['gd$rating']['numDislikes'])
        else:
            likes = 0
            dislikes = 0
        return supybot.ircutils.bold(likes), supybot.ircutils.bold(dislikes)

    def format_result(self, result):
        title = self.clean_value(result['title']['$t'])
        author = self.clean_value(result['author'][0]['name']['$t'], bold=True)
        views = self.clean_value(result['yt$statistics']['viewCount'], bold=True)
        time = self.format_time(result['media$group']['yt$duration']['seconds'])
        likes, dislikes = self.format_likes(result)

        res = (supybot.ircutils.bold('[YouTube]'), title, '-', 'By:', author, time, '-',
               likes, 'Likes', '-', dislikes, 'Dislikes', '-', views, 'Views',)

        return ' '.join(res)

    def reply(self, irc, yid):
        result = self.fetch(yid)
        if isinstance(result, dict):
            irc.reply(self.format_result(result))
        else:
            irc.reply(result)

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
