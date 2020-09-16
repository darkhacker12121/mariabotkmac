from typing import Optional, List

from telegram import ParseMode
from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.connection_sql as sql
from tg_bot import dispatcher, LOGGER, SUDO_USERS
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time

# from tg_bot.modules.translations.strings import tld

from tg_bot.modules.keyboard import keyboard

@user_admin
@run_async
def allow_connections(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            print(var)
            if (var == "no"):
                sql.set_allow_connect_to_chat(chat.id, False)
                update.effective_message.reply_text("පරිශීලකයින් සඳහා මෙම කතාබහට අක්‍රීය සම්බන්ධතා")
            elif(var == "yes"):
                sql.set_allow_connect_to_chat(chat.id, True)
                update.effective_message.reply_text("පරිශීලකයින් සඳහා මෙම කතාබස් වෙත සම්බන්ධතා සබල කර ඇත")
            else:
                update.effective_message.reply_text("කරුණාකර ඇතුලත් කරන්න on/yes/off/no කණ්ඩායමේ!")
        else:
            update.effective_message.reply_text("කරුණාකර ඇතුලත් කරන්න on/yes/off/no කණ්ඩායමේ!")
    else:
        update.effective_message.reply_text("කරුණාකර ඇතුලත් කරන්න on/yes/off/no කණ්ඩායමේ!")


@run_async
def connect_chat(bot, update, args):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    if update.effective_chat.type == 'private':
        if len(args) >= 1:
            try:
                connect_chat = int(args[0])
            except ValueError:
                update.effective_message.reply_text("අවලංගු චැට් හැඳුනුම්පත ලබා දී ඇත!")
            if (bot.get_chat_member(connect_chat, update.effective_message.from_user.id).status in ('administrator', 'creator') or 
                                     (sql.allow_connect_to_chat(connect_chat) == True) and 
                                     bot.get_chat_member(connect_chat, update.effective_message.from_user.id).status in ('member')) or (
                                     user.id in SUDO_USERS):

                connection_status = sql.connect(update.effective_message.from_user.id, connect_chat)
                if connection_status:
                    chat_name = dispatcher.bot.getChat(connected(bot, update, chat, user.id, need_admin=False)).title
                    update.effective_message.reply_text("සමඟ සාර්ථකව සම්බන්ධ වී ඇත*{}*".format(chat_name), parse_mode=ParseMode.MARKDOWN)

                    #Add chat to connection history
                    history = sql.get_history(user.id)
                    if history:
                        #Vars
                        if history.chat_id1:
                            history1 = int(history.chat_id1)
                        if history.chat_id2:
                            history2 = int(history.chat_id2)
                        if history.chat_id3:
                            history3 = int(history.chat_id3)
                        if history.updated:
                            number = history.updated

                        if number == 1 and connect_chat != history2 and connect_chat != history3:
                            history1 = connect_chat
                            number = 2
                        elif number == 2 and connect_chat != history1 and connect_chat != history3:
                            history2 = connect_chat
                            number = 3
                        elif number >= 3 and connect_chat != history2 and connect_chat != history1:
                            history3 = connect_chat
                            number = 1
                        else:
                            print("Error")
                    
                        print(history.updated)
                        print(number)

                        sql.add_history(user.id, history1, history2, history3, number)
                        print(history.user_id, history.chat_id1, history.chat_id2, history.chat_id3, history.updated)
                    else:
                        sql.add_history(user.id, connect_chat, "0", "0", 2)
                    #Rebuild user's keyboard
                    keyboard(bot, update)
                    
                else:
                    update.effective_message.reply_text("සම්බන්ධතාවය අසාර්ථක විය!")
            else:
                update.effective_message.reply_text("මෙම කතාබහට සම්බන්ධ වීමට අවසර නැත!")
        else:
            update.effective_message.reply_text("සම්බන්ධ වීමට චැට් හැඳුනුම්පත ඇතුළත් කරන්න!")
            history = sql.get_history(user.id)
            print(history.user_id, history.chat_id1, history.chat_id2, history.chat_id3, history.updated)

    else:
        update.effective_message.reply_text("භාවිතය PM වලට පමණක් සීමා වේ!")


def disconnect_chat(bot, update):
    if update.effective_chat.type == 'private':
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = update.effective_message.reply_text("කතාබස් වලින් විසන්ධි විය!")
            #Rebuild user's keyboard
            keyboard(bot, update)
        else:
           update.effective_message.reply_text("විසන්ධි කිරීම අසාර්ථකයි!")
    else:
        update.effective_message.reply_text("භාවිතය PM වලට පමණක් සීමා වේ")


def connected(bot, update, chat, user_id, need_admin=True):
    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):
        conn_id = sql.get_connected_chat(user_id).chat_id
        if (bot.get_chat_member(conn_id, user_id).status in ('administrator', 'creator') or 
                                     (sql.allow_connect_to_chat(connect_chat) == True) and 
                                     bot.get_chat_member(user_id, update.effective_message.from_user.id).status in ('member')) or (
                                     user_id in SUDO_USERS):
            if need_admin == True:
                if bot.get_chat_member(conn_id, update.effective_message.from_user.id).status in ('administrator', 'creator') or user_id in SUDO_USERS:
                    return conn_id
                else:
                    update.effective_message.reply_text("ඔබ සම්බන්ධිත කණ්ඩායමක පරිපාලකයෙකු විය යුතුය!")
                    exit(1)
            else:
                return conn_id
        else:
            update.effective_message.reply_text("කණ්ඩායම් අයිතිවාසිකම් සම්බන්ධතාවය වෙනස් කර හෝ ඔබ තවදුරටත් පරිපාලක නොවේ.\nමම ඔබව විසන්ධි කරන්නම්.")
            disconnect_chat(bot, update)
            exit(1)
    else:
        return False



__help__ = """
🔰*සම්බන්ධිත කණ්ඩායම් සමඟ ක්‍රියා ලබා ගත හැකිය*:
 🔅 සටහන් බලන්න සහ සංස්කරණය කරන්න
 🔅 පෙරහන් බලන්න සහ සංස්කරණය කරන්න
 🔅 අනාගතයේදී තවත්!

 - /connect <chatid>: දුරස්ථ කතාබස් වෙත සම්බන්ධ වන්න
 - /disconnect: කතාබස් වලින් විසන්ධි කරන්න
 - /allowconnect on/yes/off/no: කණ්ඩායම් වලට සම්බන්ධ වීමට පරිශීලකයින්ට ඉඩ දෙන්න
"""

__mod_name__ = "Connections"

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, allow_edited=True, pass_args=True)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat, allow_edited=True)
ALLOW_CONNECTIONS_HANDLER = CommandHandler("allowconnect", allow_connections, allow_edited=True, pass_args=True)

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
