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
from collections import namedtuple
import os.path
import re

SCRIPT_NAME = "logexport"
SCRIPT_AUTHOR = "Théophile 'tobast' Bastian <contact@tobast.fr>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Export part of a buffer to a nicely formatted HTML file"
SCRIPT_COMMAND = SCRIPT_NAME
SCRIPT_OPTIONS_DEFAULT = {
    'export_path':      '',
    'dark_theme':       'on',
}
SCRIPT_OPTIONS_PREFIX = 'plugins.var.python.{}.'.format(SCRIPT_NAME)


weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                 SCRIPT_DESC, "", "")

for option, default_value in SCRIPT_OPTIONS_DEFAULT.items():
    if not weechat.config_is_set_plugin(option):
        weechat.config_set_plugin(option, default_value)

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
    + "it is now 20:00:00, but to yesterday's if it is 03:00:00.\n"
    + "In a timestamp, any part but the first can be omitted, and will be "
    + "implicitly replaced by 0, as in 20:12 for 20:12:00. You can also add "
    + "a colon to make such an omission explicit, as in 20: for 20:00:00.",
    "export",
    "logexport_cmd",
    "")


''' ####### HTML ######## '''

""" Disclaimer:
    Part of this HTML code comes from
    <https://github.com/nguyentito/weechat-log-to-html> by Nguyễn Lê Thành Dũng
    released under MIT license. Thank you @nguyentito :)
"""


def wrapInHtml(wrapped):
    ''' Wraps the return value of `wrapped` in a HTML context (with CSS) '''

    DARKMODE_OPTION = 'dark_theme'

    def mkColorCSS(name, color):
        ''' Converts a `name` and `rgb` (any CSS format) to a few CSS lines '''
        return '.color-{} {{\n\tcolor: {}\n}}\n'.format(name, color)

    CSS_COLORS = {
        'white': 'Beige',
        'black': 'DarkSlateGrey',
        'blue': 'DarkSlateBlue',
        'green': 'ForestGreen',
        'lightred': 'Tomato',
        'red': 'Crimson',
        'magenta': 'MediumVioletRed',
        'brown': 'Chocolate',
        'yellow': 'GoldenRod',
        'lightgreen': 'LightGreen',
        'cyan': 'LightSeaGreen',
        'lightcyan': 'LightSkyBlue',
        'lightblue': 'RoyalBlue',
        'lightmagenta': 'HotPink',
        'darkgray': 'DimGrey',
        'gray': 'LightSlateGrey',
    }

    CSS_BASE = '''
          .non-human td:nth-child(3) {
            font-style: italic;
          }
          td {
            padding: 3px 10px;
          }
          td:nth-child(2) {
            font-weight: bold;
            text-align: right;
          }
          table, td:last-child {
            width: 100%;
          }
          table {
            border-collapse: collapse;
          }
          a, a:visited {
            color: #07a;
          }

          .nc-prefix-owner {
            color: red;
          }
          .nc-prefix-op {
            color: limegreen;
          }
          .nc-prefix-halfop {
            color: darkmagenta;
          }
          .nc-prefix-voice {
            color: orange;
          }
          .nc-prefix-none {
          } '''

    for color in CSS_COLORS:
        CSS_BASE += mkColorCSS(color, CSS_COLORS[color])

    HTML_HEADER = '''<!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8" />
        <title>IRC log</title>
        <style media="screen" type="text/css">
          {css}
        </style>
      </head>
      <body>
    '''

    HTML_FOOTER = '  </body>\n</html>'

    def wrapper(*args, **kwargs):
        if not weechat.config_is_set_plugin(DARKMODE_OPTION):
            raise (Exception
                   ("Option {} is not set. Set it to 'yes' or 'no'.".format(
                       SCRIPT_OPTIONS_PREFIX + DARKMODE_OPTION)))
        isDark = weechat.config_get_plugin(DARKMODE_OPTION) == 'on'
        bgColor = '#050505' if isDark else '#fafafa'
        fgColor = '#aaa' if isDark else '#555'
        defaultNickColor = CSS_COLORS['white' if isDark else 'black']
        dimmedLineColor = '#151515' if isDark else '#eeeeee'
        nonhumanColor = '#666' if isDark else '#505050'

        formattedCss = '''
          body {{
            font-family: monospace;
            background-color: {bgcolor};
            color: {fgcolor};
          }}
          .color-default {{
            color: {defaultNickColor};
          }}
          tr:nth-child(2n+1) {{
            background-color: {dimmedLineColor};
          }}
          .non-human {{
            color: {nonhumanColor};
          }}
        '''.format(
            bgcolor=bgColor,
            fgcolor=fgColor,
            defaultNickColor=defaultNickColor,
            dimmedLineColor=dimmedLineColor,
            nonhumanColor=nonhumanColor,
        )

        res = wrapped(*args, **kwargs)
        return (HTML_HEADER.format(css=(CSS_BASE + formattedCss))
                + res + HTML_FOOTER)

    return wrapper


''' ### END HTML ######## '''


def logError(err):
    weechat.prnt('', '=!=\t{} error: {}'.format(SCRIPT_NAME, err))


class BadlyFormattedTime(Exception):
    def __init__(self, s):
        Exception.__init__(self, "badly formatted time: '{}'".format(s))


LogLine = namedtuple('LogLine', ['timestamp', 'prefix', 'line'])


def timestampOfString(timestr):
    """ Converts a timestamp string HH:MM:SS to a weechat timestamp """
    spl = timestr.strip().split(':')
    if len(spl) > 3:
        raise BadlyFormattedTime(timestr)
    if len(spl) > 1 and spl[-1] == '':  # Allow eg. 18: for 6pm
        spl[-1] = '0'
    spl += ['0'] * (3 - len(spl))  # Allow 18:42 for 18:42:00

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


def formatFilePath(name):
    """ Transforms a log name into a log path, according to the config """
    def raise_unset():
        raise Exception(("{} is not set, I don't know where to save "
                        + "your log file! :c").format(
                            SCRIPT_OPTIONS_PREFIX + PATH_OPTION))
    PATH_OPTION = 'export_path'
    if not weechat.config_is_set_plugin(PATH_OPTION):
        raise_unset()  # exits
    outdir = weechat.config_get_plugin(PATH_OPTION)
    if not outdir:
        raise_unset()  # exits
    return os.path.normpath(os.path.expanduser(
        "{}/{}.html".format(outdir, name)))


def enhanceMessageLine(msg, regexpReplace):
    """ Applies various enhancements to <msg>, such as transforming URLs into
    clickable links and colorizing nicks.
    `regexpReplace` must be a list of (regexp, pattern) ready to be fed to
    `re.sub`. """

    def shieldTags(func):
        def splitAtMatchingTag(msg):
            opening = 0
            for pos in range(len(msg)):
                ch = msg[pos]
                if ch == '<':
                    opening += 1
                elif ch == '>':
                    opening -= 1
                    if opening < 0:
                        return msg[:pos], msg[pos+1:]
            return '', msg  # No tag closing found

        def decorated(msg):
            spl = msg.split('<')
            out = func(spl[0]) if len(spl) > 0 else ''
            for part in spl[1:]:
                inTag, afterTag = splitAtMatchingTag(part)
                out += '<' + inTag + '>' + func(afterTag)
            return out
        return decorated

    def clickableUrls(msg):
        ''' Makes URLs clickable links '''
        # This regex was originally taken from
        # http://stackoverflow.com/a/3809435 (but then modified a lot)
        URL_REGEX = re.compile(r"(\bhttps?://[-a-zA-Z0-9@:%._+~#=?&/]{2,}\b)")
        return re.sub(URL_REGEX, r'<a href="\1">\1</a>', msg)

    @shieldTags
    def applyRegexp(msg):
        ''' Colorizes the nicks in `msg` with their color in weechat '''
        # There should not be *that* many nicks, so we might as well match
        # every nick with a different regexp
        for (regexp, pattern) in regexpReplace:
            msg = regexp.sub(pattern, msg)
        return msg

    return applyRegexp(clickableUrls(msg))


@wrapInHtml
def renderHtml(lines, buff):
    """ Formats the given log <lines> into a HTML string. """
    def escape(s):
        s = weechat.string_remove_color(s, '')
        s = s.replace('&', '&amp;') \
             .replace('<', '&lt;') \
             .replace('>', '&gt;')
        return s

    NONHUMAN_PREFIXES = [escape(x) for x in ['--', '-->', '<--', '=!=', '']]

    def weechatNickColor(nick):
        return weechat.info_get('nick_color_name', nick)

    def nickColor(prefix):
        if prefix in NONHUMAN_PREFIXES:
            return 'default'
        return str(weechatNickColor(prefix))

    def nicksColorsForBuffer():
        ''' Returns a dictionary of nicks to match with their color.
        Thanks colorize_nicks.py for inspiration! '''
        nicks = {}
        bufferNicks = weechat.infolist_get('nicklist', buff, '')

        while weechat.infolist_next(bufferNicks):
            if weechat.infolist_string(bufferNicks, 'type') == 'nick':
                nick = weechat.infolist_string(bufferNicks, 'name')
                nicks[nick] = nickColor(nick)
        weechat.infolist_free(bufferNicks)

        return nicks

    def nickPrefixColor(nickPrefix):
        try:
            return {
                '!': 'owner',
                '@': 'op',
                '%': 'halfop',
                '~': 'owner',  # Depends on the IRC server used
                '+': 'voice',
            }[nickPrefix]
        except KeyError:
            return 'none'

    def isLineContinuation(prefix, lastPrefix):
        if prefix not in NONHUMAN_PREFIXES and prefix == lastPrefix:
            return True
        return False

    colorsForBuffer = nicksColorsForBuffer()
    colorsRegexForBuffer = [
        (re.compile(r'\b({})\b'.format(re.escape(nick))),
         r'<span class="color-{}">\1</span>'.format(colorsForBuffer[nick]))
        for nick in colorsForBuffer]

    def formatRow(time, prefix, line, lastPrefix=None):
        def nonhuman(prefix):
            return prefix in NONHUMAN_PREFIXES

        def splitPrefix(prefix):
            if nonhuman(prefix):
                return '', prefix
            if prefix and prefix[0] in ['!', '@', '~', '%', '+']:
                return prefix[0], prefix[1:]
            return '', prefix

        nickPrefix, nick = splitPrefix(prefix)
        lineContinuation = isLineContinuation(prefix, lastPrefix)

        return ('    <tr{}>'
                + '<td>{}</td>'
                + '<td class="color-{}">'
                + '<span class="nc-prefix-{}">{}</span>{}</td>'
                + '<td>{}</td>'
                + '</tr>\n').format(
                    ' class="non-human"' if nonhuman(prefix) else '',
                    time,
                    nickColor(nick),
                    nickPrefixColor(nickPrefix),
                    '' if lineContinuation else nickPrefix,
                    '↳' if lineContinuation else nick,
                    enhanceMessageLine(line, colorsRegexForBuffer))

    formatted = ""
    prevDate = datetime.fromtimestamp(0)
    lastPrefix = ""

    for line in lines:
        cDate = datetime.fromtimestamp(line.timestamp)
        if cDate.date() != prevDate.date():
            formatted += "{}    <h3>{}</h3>\n    <table>\n".format(
                "</table>\n" if formatted != "" else "",  # first iteration
                cDate.date().isoformat())
        formatted += formatRow(escape(cDate.time().isoformat()),
                               escape(line.prefix),
                               escape(line.line),
                               escape(lastPrefix))
        prevDate = cDate
        lastPrefix = line.prefix

    formatted += "    </table>\n"
    return formatted


def writeFile(content, path):
    """ Writes <content> to <path>, performing a few sanity checks. """
    if os.path.exists(path):
        raise Exception("File {} already exists.".format(path))

    with open(path, 'w') as handle:
        handle.write(content)


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

    outfile = formatFilePath(args[-1])

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
                gathered.append(LogLine(timestamp, prefix, msg))

        cLine = weechat.hdata_pointer(hdata_line, cLine, 'prev_line')

    html = renderHtml(gathered[::-1], buff)
    writeFile(html, outfile)


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
