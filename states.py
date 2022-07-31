from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class MainOrder(StatesGroup):
    main_menu = State()
    transfer = State()


class TransferOrder(StatesGroup):
    style_image = State()
    style_conf = State()
    content_image = State()
    content_conf = State()
    nst_run = State()
