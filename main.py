import io
from functools import partial
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.dispatcher.filters import Text
from states import TransferOrder, MainOrder
from auth_data import TOKEN
from config import picture_url
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import asyncio

from model_main import style_transer

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

button1 = KeyboardButton('Transfer')
button2 = KeyboardButton('Help')
button3 = KeyboardButton('Styles')
button4 = KeyboardButton('Author')

keyboard_main = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False) \
    .add(button1) \
    .add(button2, button3, button4)


@dp.message_handler(state='*', commands=['start'])
async def welcome(message: types.Message):
    await MainOrder.main_menu.set()
    await message.answer('Hello! Happy using this brand new NST bot', reply_markup=keyboard_main)


@dp.message_handler(Text(equals='Transfer'), state=[MainOrder.main_menu])
async def start_upload(message: types.Message):
    await MainOrder.next()
    await TransferOrder.style_image.set()

    await message.answer('Upload an image you want to use as a style', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.TEXT],
                    state= [MainOrder.transfer, TransferOrder.style_image])
async def style_uploaded(message: types.Message, state=FSMContext):
    if message.content_type != types.ContentType.PHOTO:
        await message.answer('Your style must be a format of an image! ')
        return
    async with state.proxy() as data:
        data['style'] = message.photo
    await TransferOrder.next()
    buttons = [
        "Yes, surely!",
        "I have some doubts, I'd better change...",
    ]
    keyboard_conf = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add(*buttons)
    await message.reply('Are you really sure you want to use this image as a style', reply_markup=keyboard_conf)


@dp.message_handler(Text(equals=["Yes, surely!", "I have some doubts, I'd better change..."]),
                         state=[MainOrder.transfer, TransferOrder.style_conf])
async def assure_style(message: types.Message, state=FSMContext):
    if message.text == "Yes, surely!":
        await TransferOrder.next()
        await message.answer('Upload an image you want to transfer the style on', reply_markup=ReplyKeyboardRemove())
        button = KeyboardButton('Cancel')
        keyboard_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button)

    elif message.text == "I have some doubts, I'd better change...":
        await message.answer('Then upload another style as an image')
        await TransferOrder.previous()


@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.TEXT],
                    state=[MainOrder.transfer, TransferOrder.content_image])
async def content_uploaded(message: types.Message, state=FSMContext):
    if message.content_type != types.ContentType.PHOTO:
        await message.answer('Your content must be a format of a photo! ')
        return
    async with state.proxy() as data:
        data['image'] = message.photo
    await TransferOrder.next()

    buttons = [
        "Yes, surely!",
        "I have some doubts, I'd better change..."
    ]
    keyboard_conf = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)
    await message.reply('Are you really sure you want to use this image as a style', reply_markup=keyboard_conf)


@dp.message_handler(Text(equals=["Yes, surely!",
                                 "I have some doubts, I'd better change..."]),
                    state=[MainOrder.transfer, TransferOrder.content_conf])
async def assure_content(message: types.Message, state=FSMContext):
    if message.text == "Yes, surely!":
        await TransferOrder.next() #
        await message.answer('Style and content successfully uploaded', reply_markup=ReplyKeyboardRemove())
        buttons = [
            "Yeah",
            "Nope"
        ]
        keyboard_conf = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add(*buttons)
        await message.answer('Proceed style transfer? (it may take a while)', reply_markup=keyboard_conf)
    elif message.text == "I have some doubts, I'd better change...":
        await message.answer('Then upload another content')
        await TransferOrder.previous()


@dp.message_handler(Text(equals=['Yeah', 'Nope']), state=[MainOrder.transfer, TransferOrder.nst_run])
async def transfer_style(message: types.Message, state=FSMContext):
    if message.text == 'Yeah':
        async with state.proxy() as data:
            loop = asyncio.get_event_loop()
            await message.answer('Proceeding...', reply_markup=ReplyKeyboardRemove())
            content_img = io.BytesIO()
            style_img = io.BytesIO()
            style = await bot.download_file_by_id((data.get('style')[-1]['file_id']), destination=style_img)
            image = await bot.download_file_by_id((data.get('image')[-1]['file_id']), destination=content_img)
            trans_func = partial(style_transer, style_im=style_img.getvalue(), content_im=content_img.getvalue())
            img = await loop.run_in_executor(None, trans_func)
            await message.answer('Style has been successfully applied!', reply_markup=keyboard_main)
            await message.answer_photo(img)
            await state.finish()
            await MainOrder.main_menu.set()


@dp.message_handler(state=MainOrder.main_menu)
async def kb_answer(message: types.Message):
    if message.text == 'Styles':
        message.answer('You can use one (or several) of the following pictures as your style reference')
        await message.answer_photo(picture_url)
    elif message.text == 'Author':
        await message.reply('Egor Titov\ntg: @takiegor')
    elif message.text == 'Help':
        await message.reply('Bot allows to transfer style on an image. For this, use "Transfer" button. First, you have'
                             ' to upload a style image and verify it, then upload a content image, on which the style is '
                             'going to be transfered, then verify it. When the images are uploaded, start the '
                             'transformation by clicking "Yeap" button. Wait a while and get your brand new styled '
                             'image! The quality may vary from image to image and style to style but sometimes it returns '
                             'a greatly looking transformation!')


@dp.message_handler()
async def echo(message: types.Message):
    await message.reply(message.text)


executor.start_polling(dp)
