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
import requests

import supybot.ircutils

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Insult')
except ImportError:
    _ = lambda x:x

INSULT_REGEX = re.compile(r'<TR align=center><TD>([^<]+)<\/TD><\/TR>')


class InsultApi(object):
    url = 'http://insultgenerator.org/'
    errors = {
        'connection': _('Error connecting to API.'),
        'response': _('Error loading API response.'),
    }

    def load_response(self, response):
        res = INSULT_REGEX.search(response.text)
        if not res:
            return self.errors['response']
        return {'message': res.group(1)}

    def fetch(self):
        response = requests.get(self.url)
        try:
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            return self.errors['connection']
        return self.load_response(response)

    def clean_value(self, value, bold=False):
        value = value.strip()
        value = supybot.ircutils.safeArgument(value)
        if bold:
            value = supybot.ircutils.bold(value)
        return value

    def format_result(self, result, user):
        return '{0}: {1}'.format(user, self.clean_value(result['message']))

    def reply(self, irc, user):
        result = self.fetch()

        if isinstance(result, dict):
            irc.reply(self.format_result(result, user))
        else:
            irc.reply(result)

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
