# -*- coding: utf-8 -*-

""" Logexport
    Weechat plugin by Théophile "tobast" Bastian

    Exports a specified part of a Weechat buffer to a nicely formatted HTML
    file.
"""

# Copyright (C) 2017 Théophile Bastian
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import weechat
import time
from datetime import timedelta
from datetime import date
from datetime import time as dtime
from datetime import datetime

SCRIPT_NAME = "logexport"
SCRIPT_AUTHOR = "Théophile 'tobast' Bastian <contact@tobast.fr>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Export part of a buffer to a nicely formatted HTML file"
SCRIPT_COMMAND = SCRIPT_NAME


weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                 SCRIPT_DESC, "", "")

weechat.hook_command(
    SCRIPT_COMMAND,
    "Export the specified buffer part to HTML",
    "export <start-timestamp> [<end-timestamp>] <filename>",
    "  start-timestamp: timestamp (inclusive) at which the export starts.\n"
    + "    end-timestamp: timestamp (inclusive) at which the export ends. If "
    + "omitted, exports until the buffer's end.\n"
    + "         filename: a file name for the export. The exported file path "
    + "will be '$(logexport.export_path)/$(filename).html'.\n"
    + "\n"
    + "A timestamp is formatted as HH:MM:SS, and refers to the last time the "
    + "described time occured: eg. 12:42:00 refers to today's lunch time if "
    + "it is now 20:00:00, but to yesterday's if it is 03:00:00.",
    "export",
    "logexport_cmd",
    "")


def logError(err):
    weechat.prnt('', '=!=\t{} error: {}'.format(SCRIPT_NAME, err))


class BadlyFormattedTime(Exception):
    def __init__(self, s):
        Exception.__init__(self, "badly formatted time: '{}'".format(s))


def timestampOfString(timestr):
    """ Converts a timestamp string HH:MM:SS to a weechat timestamp """
    spl = timestr.strip().split(':')
    if len(spl) != 3:
        raise BadlyFormattedTime(timestr)
    try:
        h, m, s = map(int, spl)
    except ValueError:
        raise BadlyFormattedTime(timestr)

    for (v, bound) in ((h, 24), (m, 60), (s, 60)):
        if v < 0 or v >= bound:
            raise BadlyFormattedTime(timestr)

    curDatetime = datetime.now()
    reqTime = dtime(h, m, s)
    reqDatetime = datetime.combine(date.today(), reqTime)

    if curDatetime < reqDatetime:
        # described time is yesterday
        reqDatetime -= timedelta(days=1)
    return time.mktime(reqDatetime.timetuple())


def catchWeechatFail(f):
    def wrap(*args, **kwargs):
        try:
            f(*args, **kwargs)
            return weechat.WEECHAT_RC_OK
        except Exception as e:
            logError(str(e))
            return weechat.WEECHAT_RC_ERROR
    return wrap


@catchWeechatFail
def logexport_export_cmd(buff, args):
    """ Called upon `/logexport export`. Args is already split. """

    if len(args) not in [2, 3]:
        raise Exception("missing or trailing parameters for 'export'.")

    cBuffer = weechat.hdata_get('buffer')
    lines = weechat.hdata_pointer(cBuffer, buff, 'lines')
    # 'lines' and not 'own_lines': match what the user sees.

    start_time = timestampOfString(args[0])
    if len(args) == 2:  # No end timestamp provided
        end_time = time.time()
    else:
        end_time = timestampOfString(args[1])

    outfile = args[-1]

    cLine = weechat.hdata_pointer(weechat.hdata_get('lines'),
                                  lines, 'last_line')
    hdata_line = weechat.hdata_get('line')
    hdata_line_data = weechat.hdata_get('line_data')

    gathered = []
    while cLine:
        data = weechat.hdata_pointer(hdata_line, cLine, 'data')
        if data:
            timestamp = weechat.hdata_time(hdata_line_data, data, 'date')
            prefix = weechat.hdata_string(hdata_line_data, data, 'prefix')
            msg = weechat.hdata_string(hdata_line_data, data, 'message')

            if timestamp < start_time:
                break
            if timestamp <= end_time:
                gathered.append((timestamp, prefix, msg))

        cLine = weechat.hdata_pointer(hdata_line, cLine, 'prev_line')

    for (ts, prefix, msg) in gathered[::-1]:
        weechat.prnt('', '<{}> <{}> <{}>'.format(ts, prefix, msg))


def logexport_cmd(data, buff, rawArgs):
    """ Command called by weechat upon /logexport """

    ACTION_OF_ARG = {
        'export': logexport_export_cmd,
    }

    args = rawArgs.strip().split()
    if len(args) < 1:
        logError("expected at least one argument.")
        return weechat.WEECHAT_RC_ERROR

    try:
        return ACTION_OF_ARG[args[0]](buff, args[1:])
    except KeyError:
        logError("unkwown action {}.".format(args[0]))
        return weechat.WEECHAT_RC_ERROR
