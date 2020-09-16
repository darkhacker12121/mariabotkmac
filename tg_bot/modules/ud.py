
from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

from requests import get

@run_async
def ud(bot: Bot, update: Update):
  message = update.effective_message
  text = message.text[len('/ud '):]
  results = get(f'http://api.urbandictionary.com/v0/define?term={text}').json()
  reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
  message.reply_text(reply_text)

__help__ = """
 - /ud:{word} ඔබට සෙවීමට අවශ්‍ය වචනය හෝ ප්‍රකාශනය ටයිප් කරන්න. මෙන් /ud telegram Word: විදුලි පණිවුඩ අර්ථ දැක්වීම: වරක් ජනප්‍රිය විදුලි සංදේශ පද්ධතියක් වන අතර, යවන්නා විදුලි පණිවුඩ සේවාව අමතා ඔවුන්ගේ කථා කරයි [message] උඩින් [phone]. පණිවුඩය ලබා ගන්නා පුද්ගලයා එය ටෙලි ටයිප් යන්ත්‍රයක් හරහා ග්‍රාහකයා අසල ඇති විදුලි පණිවුඩ කාර්යාලයකට යවනු ඇත [address]. පණිවිඩය ලිපිනකරුට භාර දෙනු ඇත. 1851 සිට 2006 දී සේවාව අත්හිටුවන තෙක් වෙස්ටර්න් යුනියන් යනු ලොව ප්‍රකට විදුලි පණිවුඩ සේවාවයි.
"""

__mod_name__ = "Urban dictionary"
  
ud_handle = DisableAbleCommandHandler("ud", ud)

dispatcher.add_handler(ud_handle)
