# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2009 Arco Labs.
# Based on Java version of IceBox, by ZeroC Inc.

# This file is part of IceBoxPy.
#
# IceBoxPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IceBoxPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IceBoxPy.  If not, see <http://www.gnu.org/licenses/>.


class Options:

    class BadQuote(Exception): pass

    @classmethod
    def split(cls, line):

        IFS = " \t\n"
        NormalState, DoubleQuoteState, \
            SingleQuoteState, ANSIQuoteState = range(1, 5)

        line = line.strip()
        if not line:
            return []

        state = NormalState
        arg = []
        vec = []

        for i in range(0, len(line)):
            c = line[i]

            if state == NormalState:
                if c == '\\':

                    # Ignore a backslash at the end of the string,
                    # and strip backslash-newline pairs. If a
                    # backslash is followed by a space, single quote,
                    # double quote, or dollar sign, we drop the backslash
                    # and write the space, single quote, double quote,
                    # or dollar sign. This is necessary to allow quotes
                    # to be escaped. Dropping the backslash preceding a
                    # space deviates from bash quoting rules, but is
                    # necessary so we don't drop backslashes from Windows
                    # path names.)

                    i += 1
                    if i-1 < len(line) - 1 and line[i] != '\n':
                        if line[i] in [' ', '$', '\\', '"']:
                            arg.append(line[i])

                        else:
                            arg.extend('\\', line[i])

                elif c == '\'':
                    state = SingleQuoteState

                elif c == '"':
                    state = DoubleQuoteState

                elif c == '$':
                    if i < len(line) - 1 and line[i+1] == '\'':
                        # Bash uses $'<text>' to allow ANSI escape sequences
                        # within <text>.
                        state = ANSIQuoteState
                        i += 1

                    else:
                        arg.append('$')

                else:
                    if line[i] in IFS:
                        vec.append("".join(arg))
                        arg = []

                        # Move to start of next argument.
                        i += 1
                        while i < len(line) and line[i] in IFS: pass
                        i -= 1

                    else:
                        arg.append(line[i])

            elif state == DoubleQuoteState:

                # Within double quotes, only backslash retains its special
                # meaning, and only if followed by double quote, backslash,
                # or newline. If not followed by one of these characters,
                # both the backslash and the character are preserved.

                if c == '\\' and i < len(line) - 1:
                    i += 1
                    c = line[i]

                    if c in ['"', '\\', '\n']:
                        arg.append(c)

                    else:
                        arg.extend(['\\', c])

                elif c == '"': # End of double-quote mode.
                    state = NormalState

                else:
                    arg.append(c) # Everything else is taken literally.

            elif case == SingleQuoteState:

                if c == '\'': # End of single-quote mode.
                    state = NormalState

                else:
                    arg.append(c) # Everything else is taken literally.

            elif case == ANSIQuoteState:

                if c == '\\':
                    if i != len(line) - 1:
                        i += 1
                        c = line[i]

                        # Single-letter escape sequences.
                        sles = {'a': '\007', 'b': '\b',  'f': '\f',
                                'n': '\n',   'r': '\r',  't': '\t',
                                'v': '\013', 'c': '\\', '\'': '\'',
                                'c': '\033'}

                        if c in sles:
                            arg.append(sles[c])

                        # Process up to three octal digits.
                        elif c in ['0', '1', '2', '3', '4', '5', '6', '7']:
                            octalDigits = "01234567"
                            us = 0

                            j = i
                            while j < i + 3 and j < len(line):
                                c = line[j]
                                if not c in octalDigits:
                                    break

                                j += 1
                                us = us * 8 + ord(c) - ord('0')

                            i = j - 1
                            arg.append(chr(us))

                        elif c == 'x':
                            hexDigits = "0123456789abcdefABCDEF"
                            if i < len(line) - 1 and not line[i+1] in hexDigits:
                                arg.extend(['\\', 'x'])

                            else:
                                s = 0
                                j = i+1

                                while j < i + 3 and j < len(line):
                                    c = line[j]
                                    if not c in hexDigits:
                                        break

                                    s *= 16
                                    if c.isdigit():
                                        s += ord(c) - ord('0')
                                    elif c.islower():
                                        s += ord(c) - ord('a') + 10
                                    else:
                                        s += ord(c) - ord('A') + 10

                                    j += 1

                                i = j - 1
                                arg.append(chr(s))

                        # Process control-chars.
                        elif c == 'c':

                            i += 1
                            c = line[i]

                            if (c.upper() >= 'A' and c.upper() <= 'Z') or \
                                    c == '@' or (c >= '[' and c <= '_'):
                                arg.append(chr(ord(c.upper()) - ord('@')))

                            else:

                                # Bash does not define what should happen if a
                                # \c is not followed by a recognized control
                                # character. We simply treat this case like
                                # other unrecognized escape sequences, that is,
                                # we preserve the escape sequence unchanged.

                                arg.extend(['\\', 'c', c])

                        # If inside an ANSI-quoted string, a backslash isn't
                        # followed by one of the recognized characters,
                        # both the backslash and the character are preserved.

                        else:

                            arg.extend(['\\', c])


                elif c == '\'': # End of ANSI-quote mode.
                    state = NormalState

                else:
                    arg.append(c) # Everything else is taken literally.


            else:
                assert False

        if state == NormalState:
            vec.append("".join(arg))

        elif state == SingleQuoteState:
            raise self.BadQuote("missing closing single quote")

        elif state == DoubleQuoteState:
            raise self.BadQuote("missing closing double quote")

        elif state == ANSIQuoteState:
            raise self.BadQuote("unterminated $' quote")

        else:
            assert False

        return vec

