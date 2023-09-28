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
