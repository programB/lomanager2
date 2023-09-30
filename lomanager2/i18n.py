"""
Copyright (C) 2023 programB

This file is part of lomanager2.

lomanager2 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3
as published by the Free Software Foundation.

lomanager2 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lomanager2.  If not, see <http://www.gnu.org/licenses/>.
"""
import gettext

# t = gettext.translation("lomanager2", localedir="./locales", fallback=True)

# When localedir is not specified gettext will, by default, look for
# translation files (.mo) in /usr/share/locale/<lang code>/LC_MESSAGES
# where lang code is searched for in the environment variables:
# LANGUAGE, LC_ALL, LC_MESSAGES, and LANG respectively. First found is picked.
# Fallback is to other existing translations that exist an were set in
# environment variables. eg. if LANGUAGE = de_DE;it_IT and German .mo
# is not present in LC_MESSAGES but Italian was found it will be used as
# fallback. The ultimate fallback are the raw, untranslated strings.
t = gettext.translation("lomanager2", fallback=True)
_ = t.gettext
