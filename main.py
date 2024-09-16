from initialisation import *
from aiogram import types, executor
from aiogram.types import Message, CallbackQuery,  InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiofiles
import logging
import json

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(
        dp,
        skip_updates=True
    )

def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(
            text="Пиццы 🍕",
            callback_data="pizzas"
        ),
        InlineKeyboardButton(
            text="Напитки 🍾",
            callback_data="drinks"
        )
    ).add(
        InlineKeyboardButton(
            text="Наш чат 💬",
            url=CHAT_URL,
        )
    ).add(
        InlineKeyboardButton(
            text="Поддержка 👨‍💻",
            callback_data="support"
        ),
        InlineKeyboardButton(
            text="Корзина 🛍",
            callback_data="my_purchases"
        )
    )

def items_action_menu(id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Добавить в корзину",
            callback_data=f"add_product_{id}"
        )
    ).add(
        InlineKeyboardButton(
            text="<",
            callback_data=f"back_page_{id-1}"
        ),
        InlineKeyboardButton(
            text=f"{id}",
            callback_data="ignore",
        ),
        InlineKeyboardButton(
            text=">",
            callback_data=f"next_page_{id+1}"
        )
    ).add(
        InlineKeyboardButton(
            text="Назад",
            callback_data="menu"
        )
    )

class PizzasAction(StatesGroup):
    action = State()
    
class DrinksAction(StatesGroup):
    action = State()
    
def BaseUser(id: int) -> dict:
	return {
		"basket": {
			"items": [
				
			],
			"total_sum": 0,
			"total_items": 0
		}
	}

@dp.message_handler(commands=["start"])
async def start(message: Message, state: FSMContext) -> None:
    async with aiofiles.open("database.json", "r") as db:
    	base = json.loads(await db.read())
    user = base.get("users").get(str(message.from_user.id))
    base["users"][str(message.from_user.id)] = BaseUser(message.from_user.id)
    if not user:
    	async with aiofiles.open("database.json", "w") as db:
    		await db.write(json.dumps(base, indent=4, ensure_ascii=False))
    await state.finish()
    await message.answer("Приветствую вас в нашем боте-пицерии! Для вызова меню пропишите \"/menu\", через него происходит взаимодействие с ботом.")

@dp.message_handler(commands=["menu"])
async def get_menu(message: Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        "Вот ваше меню, пользуйтесь на здоровье! :0",
        reply_markup=menu()
    )
    
@dp.callback_query_handler(text="menu", state="*")
async def returning_menu(call: CallbackQuery, state: FSMContext) -> None:
	await state.finish()
	await call.message.delete()
	await call.message.answer(
        "Вот ваше меню, пользуйтесь на здоровье! :0",
        reply_markup=menu()
    )

@dp.callback_query_handler(text="pizzas")
async def get_pizzas(call: CallbackQuery, state: FSMContext) -> None:
    async with aiofiles.open("database.json", "r") as db:
        pizzas = json.loads(await db.read()).get("pizzas")
    await state.update_data(pizzas=pizzas)
    pizza = pizzas.get("1")
    await call.message.delete()
    await call.message.answer_photo(
        photo=pizza.get("image"),
        caption=f"Название: <b>{pizza.get('name')}</b>\n\nОписание: <blockquote>{pizza.get('description')}</blockquote>\n\nЦена: <u>{pizza.get('price')}₽</u>",
        reply_markup=items_action_menu(1)
    )
    await state.set_state(PizzasAction.action)

@dp.callback_query_handler(state=PizzasAction.action)
async def action_for_pizzas_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    pizzas = data.get("pizzas")
    if call.data.startswith("back") or call.data.startswith("next"):
        id = int(call.data.split("_")[-1])
        if id <= 0:
            await call.answer(
                "Там ничего нет :(",
                show_alert=True
            )
            return
        pizza = pizzas.get(f"{id}")
        if not pizza:
            await call.answer(
                "Дальше ничего нет :(",
                show_alert=True
            )
            return
        await call.message.delete()
        await call.message.answer_photo(                            photo=pizza.get("image"),
            caption=f"Название: <b>{pizza.get('name')}</b>\n\nОписание: <blockquote>{pizza.get('description')}</blockquote>\n\nЦена: <u>{pizza.get('price')}₽</u>",                  reply_markup=items_action_menu(id)                  )
        return
    elif call.data.startswith("add"):
        id = int(call.data.split("_")[-1])
        pizza = pizzas.get(str(id))
        async with aiofiles.open("database.json", "r") as db:
            base = json.loads(await db.read())

        user = base.get("users").get(f"{call.from_user.id}")
        if not user.get("basket").get("items"):
            user.get("basket").get("items").append(
                    {
                        "type": "pizza",
                        "id": str(id),
                        "total": 1,
                        "index": 0
                    }
            )
            user.get("basket").update({"total_sum": pizza.get('price'), "total_items": 1})
        else:
            total_sum = user.get("basket").get("total_sum")
            total_items = user.get("basket").get("total_items")      
            items = [item for item in user.get("basket").get("items") if item.get("type") == "pizza"]
            if all(item.get('id') != pizza.get('id') for item in items):
                user.get("basket").get("items").append({"type": "pizza", "id": str(id), "total": 1, "index": len(items) + 1})
                user.get("basket").update({"total_sum": total_sum + pizza.get('price'), "total_items": total_items + 1})
            else:
                for index, item in enumerate(items):
                    if item.get("id") == pizza.get("id") and item.get("type") == "pizza":
                        i = item.get("index")
                        break
                total = user.get("basket").get("items")[i].get("total")
                user.get("basket").get("items")[i].update({"total": total + 1})
                user.get("basket").update({"total_sum": total_sum + pizza.get('price'), "total_items": total_items + 1})
        base.get("users").get(f"{call.from_user.id}").update(user)
        async with aiofiles.open("database.json", "w") as db:
            await db.write(json.dumps(base, indent=4, ensure_ascii=False))
        await call.answer(
            "Товар успешно добавлен в корзину :)",
            show_alert=True
        )
        return
	
@dp.callback_query_handler(text="drinks")
async def get_drinks(call: CallbackQuery, state: FSMContext) -> None:
	async with aiofiles.open("database.json", "r") as db:
	   drinks = json.loads(await db.read()).get("drinks")
	await state.update_data(drinks=drinks)
	drink = drinks.get("1")
	await call.message.delete()
	await call.message.answer_photo(
        photo=drink.get("image"),
        caption=f"Название: <b>{drink.get('name')}</b>\n\nОписание: <blockquote>{drink.get('description')}</blockquote>\n\nЦена: <u>{drink.get('price')}₽</u>",
        reply_markup=items_action_menu(1)
    )
	await state.set_state(DrinksAction.action)
	
@dp.callback_query_handler(state=DrinksAction.action)
async def action_for_drinks_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    drinks = data.get("drinks")
    if call.data.startswith("back") or call.data.startswith("next"):
        id = int(call.data.split("_")[-1])
        if id <= 0:
            await call.answer(
                "Там ничего нет :(",
                show_alert=True
            )
            return
        drink = drinks.get(f"{id}")
        if not drink:
            await call.answer(
                "Дальше ничего нет :(",
                show_alert=True
            )
            return
        await call.message.delete()
        await call.message.answer_photo(                            photo=drink.get("image"),
            caption=f"Название: <b>{drink.get('name')}</b>\n\nОписание: <blockquote>{drink.get('description')}</blockquote>\n\nЦена: <u>{drink.get('price')}₽</u>",                  reply_markup=items_action_menu(id)                  )
        return
    elif call.data.startswith("add"):
        id = int(call.data.split("_")[-1])
        drink = drinks.get(str(id))
        async with aiofiles.open("database.json", "r") as db:
            base = json.loads(await db.read())

        user = base.get("users").get(f"{call.from_user.id}")
        if not user.get("basket").get("items"):
            user.get("basket").get("items").append(
                    {
                        "type": "drink",
                        "id": str(id),
                        "total": 1,
                        "index": 0
                    }
            )
            user.get("basket").update({"total_sum": drink.get('price'), "total_items": 1})
        else:
            total_sum = user.get("basket").get("total_sum")
            total_items = user.get("basket").get("total_items")      
            items = [item for item in user.get("basket").get("items") if item.get("type") == "drink"]
            if all(item.get('id') != drink.get('id') and item.get("type") != "drink" for item in items):
                user.get("basket").get("items").append({"type": "drink", "id": str(id), "total": 1, "index": len(items)})
                user.get("basket").update({"total_sum": total_sum + drink.get('price'), "total_items": total_items + 1})
            else:
                for index, item in enumerate(items):
                    if item.get("id") == drink.get("id") and item.get("type") == "drink":
                        i = item.get("index")
                        break
                total = user.get("basket").get("items")[i].get("total")
                user.get("basket").get("items")[i].update({"total": total + 1})
                user.get("basket").update({"total_sum": total_sum + drink.get('price'), "total_items": total_items + 1})
        base.get("users").get(f"{call.from_user.id}").update(user)
        async with aiofiles.open("database.json", "w") as db:
            await db.write(json.dumps(base, indent=4, ensure_ascii=False))
        await call.answer(
            "Товар успешно добавлен в корзину :)",
            show_alert=True
        )
        return


@dp.message_handler(content_types=["photo"])
async def echo_file_id(message: Message) -> None:
    await message.answer(f"<code>{message.photo[-1].file_id}</code>")


if __name__ == "__main__":
    main()
