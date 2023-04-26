from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from DataAnalysis import create_data_frame, analysis, api_get_region
import keyboards
import texts

# Подключение к боту по токену
bot = Bot('Какой-то токен') # Чтобы получить токен, в телеграме нужно найти @BotFather и запросить свой токен
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

vacancy = None
region_id = None
region_name = None


class MessageStateGroup(StatesGroup):   # Машина состояний
    enter_region = State()
    enter_vacancy = State()


@dp.callback_query_handler()
async def callback_message(callback: types.CallbackQuery):
    if callback.data == 'another_city':
        await callback.message.answer('Вводите другой регион!')
        await callback.answer('Вводите другой регион!')
        await MessageStateGroup.enter_region.set()
    if callback.data == 'another_vacancy':
        await callback.message.answer('Вводите другое направление для поиска!')
        await callback.answer('Вводите другое направление для поиска!')
        await MessageStateGroup.enter_vacancy.set()
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )


@dp.message_handler(commands=['start'], state='*')
async def command_start(message: types.Message, state: FSMContext):
    await message.answer(f'{message.from_user.first_name}, чтобы начать анализ нажмите на кнопку ниже или напишите: \n'
                         f'<b>/choose_region</b>',
                         reply_markup=keyboards.get_keyboard(), parse_mode='html')
    await state.finish()


@dp.message_handler(commands=['choose_region'], state='*')
async def command_choose_region(message: types.Message):
    await message.answer(texts.enter_name_of_the_region, reply_markup=keyboards.regions_dictionary_url)
    await MessageStateGroup.enter_region.set()
    await message.delete()


@dp.message_handler(state=MessageStateGroup.enter_region)
async def choose_region(message: types.Message):
    global region_name, region_id
    region_name = str(message.text.strip()).lower()
    region_id, region_name = api_get_region(region_name)
    if region_id is not None:
        await message.answer(f'Отлично! Ваш регион: <b>{region_name}</b>\n'
                             + texts.enter_name_of_the_vacancy, parse_mode='html')
        await MessageStateGroup.enter_vacancy.set()
    else:
        await message.reply(texts.error_region, reply_markup=keyboards.regions_dictionary_url, parse_mode='html')


@dp.message_handler(state=MessageStateGroup.enter_vacancy)
async def choose_vacancy(message: types.Message, state: FSMContext):
    global vacancy, region_id, region_name
    vacancy = str(message.text.strip()).lower()
    msg = await message.answer('Собираю информацию...')
    df = create_data_frame(vacancy, region_id, message)
    if len(df) > 10:
        await state.finish()
        await analysis(message, df, vacancy, region_name)
        await msg.delete()
    else:
        await message.reply(texts.error_vacancy)
    await message.delete()


@dp.message_handler()
async def check_idiot(message: types.Message):
    await message.answer('Сначала нажмите на /choose_region, чтобы ввести регион поиска!')

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
