
import html
from telegram import Message, Update, Bot, User, Chat, ParseMode
from typing import List, Optional
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GKICK_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි",
    "මූලික කණ්ඩායමකින් එය පයින් ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
    "සුපිරි කණ්ඩායම් සහ නාලිකා කතාබස් සඳහා පමණක් ක්‍රමය තිබේ",
    "පිළිතුරු පණිවිඩය හමු නොවීය"
}

@run_async
def gkick(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    user_id = extract_user(message, args)
    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in GKICK_ERRORS:
            pass
        else:
            message.reply_text("පරිශීලකයාට ගෝලීයව kick ගැසිය නොහැක: {}".format(excp.message))
            return
    except TelegramError:
            pass

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ")
        return
    if int(user_id) in SUDO_USERS or int(user_id) in SUPPORT_USERS:
        message.reply_text("ඔහ්! කවුරුහරි සූඩෝ / ආධාරක පරිශීලකයෙකුට පහර දීමට උත්සාහ කරයි!😨 *පොප්කෝන් අල්ලා ගනී*")
        return
    if int(user_id) == OWNER_ID:
        message.reply_text("වාව්! කවුරුහරි කොතරම් මෝඩද කියනවා නම් ඔහුට මගේ අයිතිකරුට පහර දීමට අවශ්‍යයි!😕 *අර්තාපල් චිප්ස් අල්ලා ගනී😂*")
        return
    if int(user_id) == bot.id:
        message.reply_text("ඔහ් ... 😩මට පයින් ගහන්න දෙන්න.. නැහැ🥺...")
        return
    chats = get_all_chats()
    message.reply_text("Globally kicking user @{}".format(user_chat.username))
    for chat in chats:
        try:
             bot.unban_chat_member(chat.chat_id, user_id)  # Unban_member = kick (and not ban)
        except BadRequest as excp:
            if excp.message in GKICK_ERRORS:
                pass
            else:
                message.reply_text("User cannot be Globally kicked because: {}".format(excp.message))
                return
        except TelegramError:
            pass

GKICK_HANDLER = CommandHandler("gkick", gkick, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
dispatcher.add_handler(GKICK_HANDLER)                              
