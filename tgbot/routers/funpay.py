# - *- coding: utf- 8 - *-
import asyncio

from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.database import Funpayx, Itemx, Positionx, Purchasesx
from tgbot.keyboards.inline_admin import close_finl
from tgbot.keyboards.inline_user import refill_method_buy_finl
from tgbot.utils.const_functions import ded, get_unix, gen_id, ikb
from tgbot.utils.misc.bot_models import FSM, ARS

# Создаем роутер
router = Router(name=__name__)


# Активация FunPay кода
@router.message(F.text.startswith('/start fp_'))
async def funpay_activate(message: Message, bot: Bot, state: FSM, arSession: ARS):
    if len(message.text.split('fp_')) < 2:
        return await message.answer(
            "<b>❌ Неверный формат кода</b>\n"
            "❗ Проверьте правильность ссылки"
        )
        
    funpay_code = message.text.split('fp_')[1]
    
    await state.clear()
    
    get_funpay = Funpayx.get(funpay_code=funpay_code)
    
    if get_funpay is None:
        return await message.answer(
            "<b>❌ Код не найден или был уже использован</b>\n"
            "❗ Проверьте правильность кода и попробуйте снова"
        )
    
    if get_funpay.funpay_used == 1:
        return await message.answer(
            "<b>❌ Этот код уже был использован</b>\n"
            "❗ Один код можно использовать только один раз"
        )
    
    get_position = Positionx.get(position_id=get_funpay.position_id)
    
    if get_position is None:
        return await message.answer(
            "<b>❌ Позиция не найдена</b>\n"
            "❗ Свяжитесь с поддержкой"
        )
        
    get_items = Itemx.gets(position_id=get_funpay.position_id)
    
    if len(get_items) == 0:
        return await message.answer(
            "<b>❌ Товары в этой позиции закончились</b>\n"
            "❗ Свяжитесь с поддержкой для возврата средств"
        )
    
    # Получаем товары для выдачи
    get_buy_items = get_items[:1]  # Берем первый товар
    
    # Создаем чек покупки
    purchase_receipt = gen_id(10)
    purchase_data = "\n".join([item.item_data for item in get_buy_items])
    
    # Добавляем покупку
    Purchasesx.add(
        user_id=message.from_user.id,
        user_balance_before=0,
        user_balance_after=0,
        purchase_receipt=purchase_receipt,
        purchase_data=purchase_data,
        purchase_count=1,
        purchase_price=0,
        purchase_price_one=0,
        purchase_position_id=get_position.position_id,
        purchase_position_name=get_position.position_name,
        purchase_category_id=get_position.category_id,
        purchase_category_name="FunPay",
    )
    
    # Удаляем выданные товары
    for item in get_buy_items:
        Itemx.delete(item_id=item.item_id)
    
    # Помечаем код как использованный
    Funpayx.update(get_funpay.funpay_code, funpay_used=1, funpay_user_id=message.from_user.id)
    
    # Отправляем товар
    await message.answer(
        ded(f"""
            <b>🎁 Ваш товар:</b>
            ➖➖➖➖➖➖➖➖➖➖
            {purchase_data}
            ➖➖➖➖➖➖➖➖➖➖
            📦 Чек: <code>#{purchase_receipt}</code>
            💰 Стоимость: <code>0₽ (Оплачено через FunPay)</code>
        """)
    )
    
    # Показываем рекламное сообщение
    await asyncio.sleep(1)
    
    await message.answer(
        ded(f"""
            <b>🎉 Добро пожаловать в наш магазин!</b>

            <b>🚀 Почему стоит покупать напрямую у нас:</b>
            ✅ <b>Цены НИЖЕ</b> чем на FunPay
            ✅ <b>Мгновенная выдача</b> товара 24/7
            ✅ <b>Автоматическое пополнение</b> без ожидания
            ✅ <b>Система бонусов</b> и кэшбэка
            ✅ <b>Гарантия</b> на все товары
            ✅ <b>Поддержка онлайн</b> 24/7

            <b>💎 Эксклюзивные предложения только в боте:</b>
            ▪️ Скидки до 30% при пополнении от 500₽
            ▪️ Бесплатные товары за отзывы
            ▪️ Реферальная программа - до 15% с друзей
            ▪️ Ежедневные акции и розыгрыши

            <b>💰 Баланс в боте пополняется мгновенно:</b>
            🔷 CryptoBot - 0% комиссии
            🔮 ЮMoney - от 0.5% комиссии

            <b>🎁 Более 1000 товаров в наличии!</b>
            • Игры Steam, Origin, Uplay
            • Программы и софт
            • Подписки и ключи
            • Цифровые товары

            <i>💫 Присоединяйтесь к тысячам довольных клиентов!</i>
        """),
        reply_markup=refill_method_buy_finl()
    )


# Клавиатура FunPay
def funpay_links_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        ikb("📦 Создать ссылку", data="funpay_create"),
    ).row(
        ikb("📊 Статистика", data="funpay_stats"),
        ikb("🎫 Активные ссылки", data="funpay_list"),
    ).row(
        ikb("🔙 Главное меню", data="close_this"),
    )
    
    return keyboard.as_markup()


# Обработчики для админ-панели (добавляем в существующий admin_products роутер)
@router.callback_query(F.data == "funpay_create")
async def funpay_create_start(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    await state.set_state("here_funpay_position")
    
    await call.message.edit_text(
        "<b>🎫 Создание FunPay ссылки</b>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "▪️ Введите ID позиции для создания ссылки\n"
        "▪️ ID можно узнать в разделе редактирования позиций"
    )


# Принятие ID позиции
@router.message(F.text, StateFilter('here_funpay_position'))
async def funpay_create_position_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    if not message.text.isdigit():
        return await message.answer(
            "<b>❌ ID позиции должен быть числом</b>\n"
            "▪️ Введите ID позиции для создания ссылки"
        )
    
    position_id = int(message.text)
    get_position = Positionx.get(position_id=position_id)
    
    if get_position is None:
        return await message.answer(
            "<b>❌ Позиция с таким ID не найдена</b>\n"
            "▪️ Введите ID позиции для создания ссылки"
        )
    
    await state.update_data(here_funpay_position_id=position_id)
    await state.set_state("here_funpay_amount")
    
    await message.answer(
        "<b>🎫 Создание FunPay ссылки</b>\n"
        f"▪️ Позиция: <code>{get_position.position_name}</code>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "▪️ Введите стоимость товара на FunPay\n"
        "▪️ Цена в рублях (только число)"
    )


# Принятие стоимости
@router.message(F.text, StateFilter('here_funpay_amount'))
async def funpay_create_amount_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    from tgbot.utils.const_functions import is_number, to_number
    
    if not is_number(message.text):
        return await message.answer(
            "<b>❌ Стоимость должна быть числом</b>\n"
            "▪️ Введите стоимость товара на FunPay"
        )
    
    amount = to_number(message.text)
    state_data = await state.get_data()
    position_id = state_data['here_funpay_position_id']
    
    get_position = Positionx.get(position_id=position_id)
    
    # Создаем FunPay код
    funpay_code = Funpayx.add(position_id, amount)
    
    # Получаем username бота
    get_bot = await bot.get_me()
    funpay_link = f"https://t.me/{get_bot.username}?start=fp_{funpay_code}"
    
    await state.clear()
    
    await message.answer(
        ded(f"""
            <b>🎫 FunPay ссылка создана!</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Товар: <code>{get_position.position_name}</code>
            ▪️ Стоимость: <code>{amount}₽</code>
            ▪️ Ссылка: <code>{funpay_link}</code>
            ➖➖➖➖➖➖➖➖➖➖
            <b>📋 Для использования:</b>
            1. Разместите товар на FunPay
            2. В описание добавьте ссылку
            3. После оплаты покупатель получит товар автоматически
        """),
        reply_markup=close_finl()
    )