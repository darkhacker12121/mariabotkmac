import json
from io import BytesIO
from typing import Optional

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.__main__ import DATA_IMPORT
from tg_bot.modules.helper_funcs.chat_status import user_admin


@run_async
@user_admin
def import_data(bot: Bot, update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc
    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text("ආයාත කිරීමට පෙර ගොනුව බාගත කර නැවත පූරණය කිරීමට උත්සාහ කරන්න - මෙය පෙනේ"
                           "iffy වීමට!")
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text("මෙම ගොනුවේ එක් කණ්ඩායමකට වඩා වැඩි ගණනක් සිටින අතර කිසිවෙකුට මෙම කණ්ඩායමට සමාන චැට් හැඳුනුම්පතක් නොමැත"
                           "- ආනයනය කළ යුතු දේ මා තෝරා ගන්නේ කෙසේද??")
            return

        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]['hashes']
        else:
            data = data[list(data.keys())[0]]['hashes']

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text("ඔබගේ දත්ත ප්‍රතිස්ථාපනය කිරීමේදී ව්‍යතිරේකයක් සිදුවිය. ක්‍රියාවලිය සම්පූර්ණ නොවිය හැක. නම් "
                           "ඔබට මේ සමඟ ගැටළු තිබේ නම්, ඔබගේ උපස්ථ ගොනුව සමඟ @cyberwordk පණිවිඩය එවන්න"
                           "ගැටළුව නිදොස්කරණය කළ හැකිය. මගේ අයිතිකරුවන් උදව් කිරීමට සතුටු වනු ඇත, සහ සෑම දෝෂයක්ම"
                           "වාර්තා කිරීම මට වඩා හොඳ කරයි! ස්තූතියි! :)")
            LOGGER.exception("සඳහා ආයාත කරන්න chatid %s නම සමඟ %s failed.", str(chat.id), str(chat.title))
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        msg.reply_text("උපස්ථය සම්පූර්ණයෙන්ම ආනයනය කර ඇත. ආපසු සාදරයෙන් පිළිගනිමු! :D")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    msg.reply_text("")


__mod_name__ = "Backups"

__help__ = """
*Admin only:*
 - /import: හැකිතාක් ආනයනය කිරීම සඳහා කණ්ඩායම් බට්ලර් උපස්ථ ගොනුවකට පිළිතුරු දෙන්න, මාරුවීම සරල කරයි! සටහන \
ගොනු/ඡායාරූප විදුලි පණිවුඩ සීමාවන් නිසා ආනයනය කළ නොහැක.
 - /export: !!! මෙය තවමත් විධානයක් නොවේ, නමුත් ඉක්මනින් පැමිණෙනු ඇත!
"""
IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data)

dispatcher.add_handler(IMPORT_HANDLER)
# dispatcher.add_handler(EXPORT_HANDLER)
