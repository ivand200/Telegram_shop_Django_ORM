from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.utils.request import Request
from telegram import Location, ChatLocation, User
import datetime
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import logging
import re
import datetime

from shop.models import Product
from shop.models import Cart
from shop.models import Customer
from shop.models import Order



def name(pk):
    name = Product.objects.filter(pk=pk).values_list("name")
    return name[0]

def price(title):
    price = Product.objects.filter(name=title).values_list("price")
    return price[0]


def checkout(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.from_user.id
    username = query.from_user.username
    customer = Customer.objects.filter(telegram_id=chat_id).values_list("pk")
    customer_id = str(customer[0]).replace('(','').replace(')','').replace(',','')
    cart_raw = Cart.objects.filter(customer=customer_id).values_list("product", "quantity")
    cart_dict = dict(cart_raw)
    price_ = list()
    list_clear = list()
    for key, val in cart_dict.items():
        name = Product.objects.filter(pk=key).values_list("name")
        quantity = val
        newtup = (name[0], quantity)
        list_clear.append(newtup)
        price = Product.objects.filter(pk=key).values_list("price")
        price_str = float(''.join(str(el) for el in price[0]))
        total = price_str * int(val)
        price_.append(total)
    total_ = 0
    for item in price_:
        total_ = total_ + item
    list_str = "\n".join(str(item) for item in list_clear)
    cart_clear = list_str.replace('(','').replace(')','').replace(',','')
    for item in cart_dict.items():
        q = item[1]
        p = item[0]
        o = Order(quantity=q, created_at=datetime.datetime.now(),
                  total=total_, customer_id=customer_id, product_id=p)
        o.save()
    context.bot.send_message(chat_id=update.effective_chat.id, text=
                             f"<b>*Checkout*"
                             f":</b>\n-------------\n"
                             f"<u>{cart_clear}</u>\nTotal = <b>{total_}</b>"
                             f"\n------------- \n Pay to SBER Account Number : 123123123",
                             parse_mode=telegram.ParseMode.HTML)

def del_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.from_user.id
    username = query.from_user.username
    customer = Customer.objects.filter(telegram_id=chat_id).values_list("pk")
    user_id = str(customer[0]).replace('(','').replace(')','').replace(',','')
    c = Cart.objects.filter(customer_id=user_id)
    c.delete()
    context.bot.send_message(chat_id=update.effective_chat.id, text=
                             f"<b>{username}</b> now your cart is empty\n",
                             parse_mode=telegram.ParseMode.HTML)


def cart(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    keyboard = [[
                 InlineKeyboardButton(f"Delete cart", callback_data="del_cart"),
                 InlineKeyboardButton(f"Proceed to checkout", callback_data="proceed_to")
                 ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    c, created = Customer.objects.get_or_create(telegram_id=chat_id,
                 defaults={'name': update.message.chat.username,})
    customer = Customer.objects.filter(telegram_id=chat_id).values_list("pk")
    customer_id = str(customer[0]).replace('(','').replace(')','').replace(',','')
    cart_raw = Cart.objects.filter(customer=customer_id).values_list("pk")
    #cart_ = str(cart_raw[0]).replace('(','').replace(')','').replace(',','')
    if cart_raw:
        cart_raw = Cart.objects.filter(customer=customer_id).values_list("product", "quantity")
        cart_list = list()
        price_ = list()
        cart_dict = dict(cart_raw)
        for key, val in cart_dict.items():
            price = Product.objects.filter(pk=key).values_list("price")
            price1 = float(''.join(str(el) for el in price[0]))
            price_sum = price1 * int(val)
            price_.append(price_sum)
            product = Product.objects.filter(pk=key).values_list("name")
            quantity = val
            newtup = (product[0], quantity)
            cart_list.append(newtup)
        cart1 = "\n".join(str(item) for item in cart_list)
        sum = 0
        for item in price_:
            sum = sum + item
        cart_clear = cart1.replace('(','').replace(')','').replace(',','')
        update.message.reply_text(f"Your cart <b>{username}</b>\n<u>{cart_clear}</u>\n\n<b>"
                                  f"Sub-total: {sum}</b>", reply_markup=reply_markup,
                                  parse_mode=telegram.ParseMode.HTML)
    else:
        update.message.reply_text(f"<b>{username}</b> nothing in your cart!\n\n",
                                  parse_mode=telegram.ParseMode.HTML)

def add_product(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.from_user.id
    username = query.from_user.username
    product_callback_raw = update.callback_query.message.caption
    product_callback_split = product_callback_raw.split("\n")
    p = Product.objects.filter(name=product_callback_split[0]).values_list("pk")
    product_callback_id = str(p[0]).replace('(','').replace(')','').replace(',','')
    c, created = Customer.objects.get_or_create(telegram_id=chat_id,
                                                defaults={'name': query.from_user.username,})
    user = Customer.objects.filter(name=username).values_list("pk")
    user_ = str(user[0]).replace('(','').replace(')','').replace(',','')
    cart_ = Cart.objects.filter(customer_id=user_, product_id=product_callback_id).values_list("quantity")
    if cart_:
        quantity_ = Cart.objects.filter(customer_id=user_, product_id=product_callback_id).values_list("quantity")
        new_quantity = str(quantity_[0]).replace('(','').replace(')','').replace(',','')
        update_cart = int(new_quantity) + 1
        c = Cart.objects.get(customer_id=user_, product_id=product_callback_id)
        c.quantity = update_cart
        c.save()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f" +1 {product_callback_split[0]}\n")
    else:
        c = Cart(customer_id=user_, product_id=product_callback_id, quantity=1)
        c.save()
        context.bot.send_message(chat_id=update.effective_chat.id, text=
                                 f"<b>{username}</b> {product_callback_split[0]} added to your cart",
                                 parse_mode=telegram.ParseMode.HTML)

def show_prod(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = update.callback_query.data
    title = name(data)
    price_ = price(title[0])
    keyboard = [[InlineKeyboardButton("Add to Cart", callback_data="add_to_cart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_photo(update.effective_chat.id, photo=open(f"{data}.png", "rb"),
    caption=f"<b>{title[0]}\n{price_}rub</b>", reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)

def catalog(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(f"{name(1)[0]}", callback_data="1")],
        [InlineKeyboardButton(f"{name(2)[0]}", callback_data="2")],
        [InlineKeyboardButton(f"{name(3)[0]}", callback_data="3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"<i><u>Please choose product</u></i>",
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)

def start(update, context):
    chat_id = update.effective_chat.id
    username = update.message.from_user.username
    c, created = Customer.objects.get_or_create(telegram_id=chat_id, defaults={'name': update.message.from_user.username,})
    custom_keyboard = [["Catalog"], ["Cart", "Contacts"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{username} your ID is {chat_id}", reply_markup=reply_markup)

class Command(BaseCommand):
    help = "Telegram-bot"

    def handle(self, *args, **options):
        request = Request( connect_timeout=0.5, read_timeout=0.5,)
        bot = Bot(request=request, token=settings.TOKEN)
        print(bot.get_me())

        updater = Updater(bot=bot, use_context=True,)


        start_handler = CommandHandler("start", start)
        updater.dispatcher.add_handler(start_handler)

        catalog_handler = MessageHandler(Filters.text("Catalog"), catalog)
        updater.dispatcher.add_handler(catalog_handler)

        show_prod_handler = CallbackQueryHandler(show_prod, pattern= '^[0-9]$')
        updater.dispatcher.add_handler(show_prod_handler)

        add_product_handler = CallbackQueryHandler(add_product, pattern="add_to_cart")
        updater.dispatcher.add_handler(add_product_handler)

        cart_handler = MessageHandler(Filters.text("Cart"), cart)
        updater.dispatcher.add_handler(cart_handler)

        del_cart_handler = CallbackQueryHandler(del_cart, pattern="del_cart")
        updater.dispatcher.add_handler(del_cart_handler)

        checkout_handler = CallbackQueryHandler(checkout, pattern="proceed_to")
        updater.dispatcher.add_handler(checkout_handler)

        updater.start_polling()
        updater.idle()

