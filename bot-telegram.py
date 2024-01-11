import telebot
import os
import functions
import pandas as pd
import datetime as dt
import time
import settings as stt

bot = telebot.TeleBot(stt.bot_telegram_token)
@bot.message_handler(content_types=['document'])

def handle_docs(message):
    START = time.time()
    bot.send_message(message.chat.id, 'Iniciando proceso.')
    file_id = message.document.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_name = f"{message.document.file_name}"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    productos = pd.read_excel(file_name, header=None)
    productos = productos.rename(columns={0:'codigo', 1:'producto'})
    bot.send_message(message.chat.id, f'{len(productos)} productos para procesar.')
    
    data = pd.read_csv('productos.csv', sep=',')

    productos_nuevos = {
        'producto':[],
        'linkproducto':[],
        'codigo':[],
        'categoria':[]
    }

    for row in range(len(productos)):
        if str(productos.iloc[row].codigo) not in data.codigo.astype(str).values:
            codigo_value = str(productos.iloc[row].codigo)
            producto_pre = str(productos.iloc[row].producto)
            link_value = functions.buscar_producto_en_pagina(codigo_value, producto_pre)
            producto_value = functions.conseguir_nombre_producto(link_value)
            categoria_value = link_value.split('/')[3]
            functions.create_qr(producto_value, codigo_value, link_value, 'logo.png')
            
            productos_nuevos['producto'].append(producto_value)
            productos_nuevos['linkproducto'].append(link_value)
            productos_nuevos['codigo'].append(codigo_value)
            productos_nuevos['categoria'].append(categoria_value)
        else:
            fila = int(data.loc[data.codigo.astype(str) == str(productos.iloc[row].codigo)].index[0])
            codigo_value = data.iloc[fila].codigo
            link_value = data.iloc[fila].linkproducto
            producto_value = data.iloc[fila].producto
            categoria_value = link_value.split('/')[3]
            functions.create_qr(producto_value, codigo_value, link_value, 'logo.png')

    # Cargo los nuevos productos el archivo CSV
    df_nuevos_productos = pd.DataFrame(productos_nuevos)
    functions.agregar_productos(df_nuevos_productos)
    
    bot.send_message(message.chat.id, '✅ Codigos QR creados.')
    imagenes_codigos = [f'codigos_completos/{cd}.jpg' for cd in list(productos.codigo.values)]

    d = dt.datetime.now()
    formatted_date = d.strftime('%d-%m-%Y-%H-%M-%S')
    output_user_file =  f'CODIGOS-QR-{formatted_date}.pdf'

    functions.generate_pdf_with_multiple_images(imagenes_codigos, output_user_file, 3)
    bot.send_message(message.chat.id, '✅ Documento PDF creado.')

    with open(output_user_file, 'rb') as file:
        bot.send_document(message.chat.id, file)

    FINISH = time.time()
    TOTAL_TIME = FINISH - START
    TOTAL_TIME_FORMATTED = str(dt.timedelta(seconds=TOTAL_TIME)).split(".")[0]
    bot.send_message(message.chat.id, f'✅ Proceso finalizado correctamente.\n⏱️ Tiempo total del proceso: {TOTAL_TIME_FORMATTED}')
    os.remove(output_user_file)
    os.remove(file_name)

    for f in os.listdir('codigos_completos/'):
        os.remove('codigos_completos/' + f)

bot.polling()