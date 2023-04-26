from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton('/choose_region'))
    return kb


regions_dictionary_url = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Справочник регионов', url='https://www.binran.ru/resources/current/herbaria/citylist-rus.html')]
])

final_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Выбрать другой город', callback_data='another_city')],
    [InlineKeyboardButton('Выбрать другое направление', callback_data='another_vacancy')]
])


