###
# Copyright (c) 2005, Brian Pankey
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

import os
import popen2
import sys

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class Sysinfo(callbacks.Plugin):
    """Add the help for "@plugin help Sysinfo" here
    This should describe *how* to use this plugin."""
    def system(self, irc, msg, args):
        """takes no arguments
        
        Displays the output of 'uname -a' to the channel
        """
        uname = popen2.Popen4('uname -a')
        (r, w) = (uname.fromchild, uname.tochild)
        response = r.readline().strip()
        try:
            irc.reply(response)
        finally:
            r.close()
            w.close()
            uname.wait()
    system = wrap(system)

    def sload(self, irc, msg, args):
        """takes no arguments

        Displays the systems uptime (not the bots)
        """
        uptime = popen2.Popen4('uptime')
        (r, w) = (uptime.fromchild, uptime.tochild)
        response = r.readline().strip()
        try:
            irc.reply(response)
        finally:
            r.close()
            w.close()
            uptime.wait()
    sload = wrap(sload)

Class = Sysinfo


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79: