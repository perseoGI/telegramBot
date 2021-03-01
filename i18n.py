# Import gettext module
import gettext

# Set the local directory
localedir = './locale'

# Set up your magic function
translate = gettext.translation('base', localedir, fallback=True)
_ = translate.gettext

es = gettext.translation('base', localedir, languages=['es'])
es.install()

# en = gettext.translation('base', localedir, languages=['en'])
# en.install()

de = gettext.translation('base', localedir, languages=['de'])
de.install()

languages = {
    'es': es,
    'de': de
}

def install_user_language(update):
    lang = update['_effective_user']['language_code']
    print (lang)
    # languages[lang].install()
    _ = languages[lang].gettext


