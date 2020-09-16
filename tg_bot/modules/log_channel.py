from functools import wraps
from typing import Optional

from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Bot, Update, ParseMode, Message, Chat
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, run_async
    from telegram.utils.helpers import escape_markdown

    from tg_bot import dispatcher, LOGGER
    from tg_bot.modules.helper_funcs.chat_status import user_admin
    from tg_bot.modules.sql import log_channel_sql as sql


    def loggable(func):
        @wraps(func)
        def log_action(bot: Bot, update: Update, *args, **kwargs):
            result = func(bot, update, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]
            if result:
                if chat.type == chat.SUPERGROUP and chat.username:
                    result += "\n<b>Link:</b> " \
                              "<a href=\"http://telegram.me/{}/{}\">click here</a>".format(chat.username,
                                                                                           message.message_id)
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(bot, log_chat, chat.id, result)
            elif result == "":
                pass
            else:
                LOGGER.warning("%s ලොග් විය හැකි ලෙස සකසා ඇති නමුත් ආපසු ප්‍රකාශයක් නොතිබුණි.", func)

            return result

        return log_action


    def send_log(bot: Bot, log_chat_id: str, orig_chat_id: str, result: str):
        try:
            bot.send_message(log_chat_id, result, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            if excp.message == "චැට් හමු නොවීය":
                bot.send_message(orig_chat_id, "මෙම ලොග් නාලිකාව මකා දමා ඇත - සැකසීම.")
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(log_chat_id, result + "\n\nඅනපේක්ෂිත දෝෂයක් හේතුවෙන් ආකෘතිකරණය අක්‍රීය කර ඇත.")


    @run_async
    @user_admin
    def logging(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                "මෙම කණ්ඩායමට එහි සියලුම ල logs ු-සටහන් යවා ඇත: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                         log_channel),
                parse_mode=ParseMode.MARKDOWN)

        else:
            message.reply_text("මෙම කණ්ඩායම සඳහා ලොග් නාලිකාවක් සකසා නොමැත!")


    @run_async
    @user_admin
    def setlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == chat.CHANNEL:
            message.reply_text("දැන්, ඔබට මෙම නාලිකාව සම්බන්ධ කිරීමට අවශ්‍ය කණ්ඩායමට / setlog යොමු කරන්න!")

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "මැකීමට පණිවිඩය හමු නොවීය":
                    pass
                else:
                    LOGGER.exception("ලොග් නාලිකාවේ පණිවිඩය මැකීමේ දෝෂයකි. කෙසේ වෙතත් වැඩ කළ යුතුය.")

            try:
                bot.send_message(message.forward_from_chat.id,
                                 "මෙම නාලිකාව ලොග් නාලිකාව ලෙස සකසා ඇත {}.".format(
                                     chat.title or chat.first_name))
            except Unauthorized as excp:
                if excp.message == "තහනම්: බොට් නාලිකා සංවාදයේ සාමාජිකයෙක් නොවේ":
                    bot.send_message(chat.id, "ලොග් නාලිකාව සාර්ථකව සකසන්න!")
                else:
                    LOGGER.exception("ලොග් නාලිකාව සැකසීමේදී දෝෂයකි.")

            bot.send_message(chat.id, "ලොග් නාලිකාව සාර්ථකව සකසන්න!")

        else:
            message.reply_text("ලොග් නාලිකාවක් සැකසීමේ පියවර:\n"
                               " - අපේක්ෂිත නාලිකාවට බොට් එක් කරන්න\n"
                               " - යවන්න /setlog නාලිකාවට\n"
                               " - ඉදිරියට /setlog කණ්ඩායමට\n")


    @run_async
    @user_admin
    def unsetlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(log_channel, "නාලිකාව සම්බන්ධ කර නොමැත {}".format(chat.title))
            message.reply_text("ලොග් නාලිකාව සකසා නොමැත.")

        else:
            message.reply_text("ලොග් නාලිකාවක් තවම සකසා නැත!")


    def __stats__():
        return "{} log channels set.".format(sql.num_logchannels())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return "මෙම කණ්ඩායමට එහි සියලුම ල logs ු-සටහන් යවා ඇත:{} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                            log_channel)
        return "මෙම කණ්ඩායම සඳහා ලොග් නාලිකාවක් සකසා නැත!"


    __help__ = """
*පරිපාලක පමණි:*
- /logchannel: ලොග් නාලිකා තොරතුරු ලබා ගන්න
- /setlog: ලොග් නාලිකාව සකසන්න.
- /unsetlog:ලොග් නාලිකාව සකසන්න.

ලොග් නාලිකාව සැකසීම සිදු කරනු ලබන්නේ:
- අපේක්ෂිත නාලිකාවට බොට් එක් කිරීම (පරිපාලකයෙකු ලෙස!)
- යැවීම/setlog නාලිකාවේ
- ඉදිරියට යැවීම /setlog කණ්ඩායමට
"""

    __mod_name__ = "Log Channels"

    LOG_HANDLER = CommandHandler("logchannel", logging)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func
