import gettext

t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
