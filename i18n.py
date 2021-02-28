# Import gettext module
import gettext

# Set the local directory
localedir = './locale'

# Set up your magic function
translate = gettext.translation('telegramBot', localedir, fallback=True)
_ = translate.gettext
