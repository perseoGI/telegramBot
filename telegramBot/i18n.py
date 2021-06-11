# Import gettext module

import gettext
from os import walk

# Set the local directory
localedir = "./locale"

# Set up magic function
en = gettext.translation("base", localedir, fallback=True)
_ = en.gettext

languages = {}


def setup_locales():
    for locale in next(walk(localedir))[1]:
        languages[locale] = gettext.translation("base", localedir, languages=[locale])
        languages[locale].install()


def install_user_language(update):
    if not update:
        return en.gettext

    lang = update["_effective_user"]["language_code"]
    return languages[lang].gettext
