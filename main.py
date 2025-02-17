import aiogram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Message, ContentType, CallbackQuery, FSInputFile
import asyncio
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from keyboards.inline_kbs import create_plot

TOKEN = 'TOKEN'
bot = Bot(token=TOKEN)
dp = Dispatcher()


df = None
user_id = 0
plot_type = ''
col = []
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    global user_id
    user_id = message.from_user.id
    await message.reply("Привет! Я бот, который может помочь тебе нарисовать график!📊\nОтправь мне данные в формате CSV или XLSX.")

@dp.message(F.content_type == ContentType.DOCUMENT)
async def get_doc(message: types.Message):
    global df
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    local_file_path = f'temp.{file_name.split(".")[-1]}'
    await bot.download_file(file_path, local_file_path)

    if file_name.endswith('.csv'):
        df = pd.read_csv(local_file_path)
        df.drop(columns='Unnamed: 0', inplace=True)
    elif file_name.endswith('.xlsx'):
        df = pd.read_excel(local_file_path)
    else:
        await message.reply("Неподдерживаемый формат файла. Пожалуйста, загрузите CSV или XLSX.")
        return

    await message.answer("Данные получены! Выберите график:", reply_markup=create_plot())

@dp.callback_query(F.data == 'draw_pie')
async def draw_pie(call: CallbackQuery):
    global plot_type
    plot_type = 'pie'
    print(plot_type)
    await get_columns(call.message, plot_type)
@dp.callback_query(F.data == 'draw_scatterPlot')
async def draw_scatter_plot(call: CallbackQuery):
    global plot_type
    plot_type = 'scatter'
    print(plot_type)
    await get_columns(call.message, plot_type)
@dp.callback_query(F.data == 'draw_barPlot')
async def draw_bar_plot(call: CallbackQuery):
    global plot_type
    plot_type = 'bar'

    await get_columns(call.message, plot_type)
@dp.callback_query(F.data == 'draw_histPlot')
async def draw_hist_plot(call: CallbackQuery):
    global plot_type
    plot_type = 'hist'
    await get_columns(call.message, plot_type)
@dp.callback_query(F.data == 'back_to_start')
async def back_to_start(call: CallbackQuery):
    global plot_type
    plot_type = ''
    print(plot_type)
    await call.message.answer("Выберите график:", reply_markup=create_plot())

async def get_columns(message: Message, plot_type: str):
    global df, col
    col = df.columns.tolist()
    await message.answer(
        "Теперь выбери столбцы, которые ты хочешь включить в график. В формате x,y:\nВот список всех доступных столбцов:\n" + ", ".join(col)
    )

@dp.message()
async def columns_select(message: Message):
    selected_col = message.text.split(',')
    selected_col = [col.strip() for col in selected_col]

    if all(item in col for item in selected_col) and len(selected_col) == 2:
        await message.answer(f"Вы выбрали столбцы: {', '.join(selected_col)}")
        await send_plot(selected_col[0], selected_col[1], plot_type)
    else:
        await message.answer("Некорректный выбор столбцов. Пожалуйста, попробуйте снова.")

async def send_plot(col_x, col_y, plot_type):
    global df
    plt.figure()

    if plot_type == 'pie':
        data = df[col_x].value_counts()
        plt.pie(data, labels=data.index, autopct='%1.1f%%')
        plt.title("Круговая диаграмма")

    elif plot_type == 'bar':
        sns.barplot(x=col_x, y=col_y, data=df)
        plt.title("Столбчатая диаграмма")
        plt.xlabel(col_x)
        plt.ylabel(col_y)

    elif plot_type == 'scatter':
        sns.scatterplot(x=col_x, y=col_y, data=df)
        plt.title("Точечная диаграмма")
        plt.xlabel(col_x)
        plt.ylabel(col_y)

    elif plot_type == 'hist':
        plt.hist(df[col_x], bins=30, alpha=0.7, label=col_x)
        plt.hist(df[col_y], bins=30, alpha=0.7, label=col_y)
        plt.title("Гистограмма")
        plt.xlabel("Значения")
        plt.ylabel("Частота")
        plt.legend()


    file_path = 'plot.png'
    plt.savefig(file_path)
    plt.close()


    photo = FSInputFile(file_path)
    await bot.send_photo(chat_id=user_id, photo=photo, caption="Вот ваш график!")

    os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())