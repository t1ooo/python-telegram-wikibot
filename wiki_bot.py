from dotenv import dotenv_values
from functools import wraps
import logging
from typing import Awaitable, Callable, List
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import wiki

# logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# helpers
def get_command_arg(context: ContextTypes.DEFAULT_TYPE) -> str:
    if context.args is None:
        return ""
    arg = " ".join(filter(len, map(str.strip, context.args)))
    return arg


def get_current_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    if user is not None:
        lang = (context.user_data or {}).get("lang", "")
        if lang != "":
            logger.info(f"context.user_data lang: {lang}")
            return lang.lower()

        code = user.language_code
        if code is not None and code != "":
            logger.info(f"user.language_code: {code}")
            return code.lower()

    return ""


def set_current_lang(lang: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if context.user_data is not None:
        context.user_data["lang"] = lang
        logger.info(f"set context.user_data lang: {lang}")
        return True

    return False


# handlers
def handler_decorator(
    f: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[List[str]]],
):
    @wraps(f)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            reply = await f(update, context)
            await update.message.reply_text("\n".join(reply))
        except wiki.WikiException as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            logger.error(e, exc_info=True)
            await update.message.reply_text("Something went wrong :(")

    return wrapper


@handler_decorator
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> List[str]:
    return [
        "I can help you get access to Wikipedia pages.",
        "",
        "You can control me by sending these commands:",
    ] + [str(cmd) for cmd in COMMANDS]


@handler_decorator
async def search_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> List[str]:
    query = get_command_arg(context)
    lang = get_current_lang(update, context)
    logger.info(f"search_handler: {query} {lang}")

    return wiki.search(query, lang)


@handler_decorator
async def suggest_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> List[str]:
    query = get_command_arg(context)
    lang = get_current_lang(update, context)
    logger.info(f"suggest_handler: {query} {lang}")

    return [wiki.suggest(query, lang)]


@handler_decorator
async def summary_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> List[str]:
    query = get_command_arg(context)
    lang = get_current_lang(update, context)
    logger.info(f"summary_handler: {query} {lang}")

    return [wiki.summary(query, lang)]


@handler_decorator
async def set_lang_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> List[str]:
    lang = get_command_arg(context)
    logger.info(f"set_lang_handler: {lang}")

    lang_code = wiki.get_lang_code(lang)
    if lang_code is None:
        return [f"Sorry, {lang} language is not supported."]

    set_current_lang(lang_code, context)
    return [f"Language successful changed to {lang_code}."]


@handler_decorator
async def get_lang_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> List[str]:
    logger.info(f"get_lang_handler")

    return [get_current_lang(update, context)]


@handler_decorator
async def languages_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> List[str]:
    logger.info(f"wikipedia_languages")

    return [
        "List of supported language codes:",
        "",
        "https://meta.wikimedia.org/wiki/List_of_Wikipedias",
    ]


class Command:
    def __init__(self, cmd: str, arg: str, fn: Callable, help: str):
        self.cmd = cmd
        self.arg = arg
        self.fn = fn
        self.help = help

    def __str__(self) -> str:
        return f"/{self.cmd} {self.arg} - {self.help}"


COMMANDS = [
    Command("start", "", help_handler, "show start message"),
    Command("help", "", help_handler, "show help message"),
    Command("search", "[query]", search_handler, "do a wikipedia search for query"),
    Command(
        "suggest",
        "[query]",
        suggest_handler,
        "get a wikipedia search suggestion for query",
    ),
    Command("summary", "[query]", summary_handler, "plain text summary of the page"),
    Command(
        "setlang",
        "[language|language_code]",
        set_lang_handler,
        "change the language of the api being requested",
    ),
    Command(
        "getlang",
        "",
        get_lang_handler,
        "get current language",
    ),
    Command(
        "languages",
        "",
        languages_handler,
        "list all the currently supported language prefixes",
    ),
]


def read_token() -> str:
    return dotenv_values(".env").get("TELEGRAM_API_TOKEN", "") or ""


def main() -> None:
    token = read_token()
    if token == "":
        raise Exception("token is empty")

    application = Application.builder().token(token).build()

    for cmd in COMMANDS:
        application.add_handler(CommandHandler(cmd.cmd, cmd.fn))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, help_handler)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
