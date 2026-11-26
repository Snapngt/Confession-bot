import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = '8414057858:AAFLHvY42wsCDO8a5NX-kC08QI4DoBLSNwE'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Stores comments in memory by hashtag: {hashtag: [comment1, comment2, ...]}
comments_db = {}

class CommentStates(StatesGroup):
    waiting_for_hashtag = State()
    waiting_for_comment = State()

class ViewStates(StatesGroup):
    waiting_for_view_hashtag = State()

def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ያስተያየት/ኮሜንት ይስጡ")],
            [KeyboardButton(text="ሪፕላይ የተደረጉትን ለማየት")],
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "እንኳን ደህና መጡ!\n\n"
        "እዚህ ቦት ላይ በቻናል ላይ ወይም በኮሜንቶች ስር ለተጻፉ ነገሮች በሃሽታግ "
        "ሪፕላይ ወይም አስተያየት መስጠት እና የተሰጡ አስተያየቶችን ማንነት ሳይታወቅ "
        "ማየት ይችላሉ። ከታች ያሉትን አማራጮች ይጠቀሙ።"
    )
    await message.answer(welcome_text, reply_markup=main_keyboard())

# 1. Give a comment / reply under a hashtag
@dp.message(F.text == "ያስተያየት/ኮሜንት ይስጡ")
async def ask_comment_hashtag(message: types.Message, state: FSMContext):
    await message.answer("እባኮትን አስተያየት ለመስጠት የፈለጉትን ሃሽታግ ያስቀምጡልን።")
    await state.set_state(CommentStates.waiting_for_hashtag)

@dp.message(CommentStates.waiting_for_hashtag)
async def receive_comment_hashtag(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("እባኮትን የሃሽታግ ጽሁፍ ወይም ቁጥር ያስቀምጡ።")
        return

    hashtag = message.text.strip()
    if not hashtag.startswith("#"):
        hashtag = f"#{hashtag}"

    await state.update_data(hashtag=hashtag)
    await message.answer(
        f"እባኮትን በዚህ ሃሽታግ ({hashtag}) ስር መስጠት የሚፈልጉትን ኮሜንት ይጻፉ።"
    )
    await state.set_state(CommentStates.waiting_for_comment)

@dp.message(CommentStates.waiting_for_comment)
async def save_comment(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("እባኮትን የጽሁፍ አስተያየት ያስገቡ።")
        return

    data = await state.get_data()
    hashtag = data.get("hashtag")
    comment_text = message.text.strip()

    comments_db.setdefault(hashtag, []).append(comment_text)

    await message.answer("አስተያየቱ በሚገባ ተልኳል።", reply_markup=main_keyboard())
    await state.clear()

# 2. View comments under a hashtag anonymously
@dp.message(F.text == "ሪፕላይ የተደረጉትን ለማየት")
async def ask_view_hashtag(message: types.Message, state: FSMContext):
    await message.answer("እባኮትን አስተያየት ለማየት የሚፈልጉትን ሃሽታግ ቁጥር ይጻፉ።")
    await state.set_state(ViewStates.waiting_for_view_hashtag)

@dp.message(ViewStates.waiting_for_view_hashtag)
async def show_comments(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("እባኮትን የሃሽታግ ቁጥር ወይም ሃሽታግ ይጻፉ።")
        return

    hashtag = message.text.strip()
    if not hashtag.startswith("#"):
        hashtag = f"#{hashtag}"

    entries = comments_db.get(hashtag)
    if entries:
        lines = [f"በ {hashtag} ሃሽታግ ስር የተጻፉ አስተያየቶች፡\n"]
        for i, item in enumerate(entries, start=1):
            lines.append(f"{i}. {item}")
        await message.answer("\n".join(lines), reply_markup=main_keyboard())
    else:
        await message.answer("በዚህ ሃሽታግ የተጻፈ ኮሜንት የለም።", reply_markup=main_keyboard())

    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
