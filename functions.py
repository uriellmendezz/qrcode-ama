# Librerias a utilizar
from reportlab.lib.pagesizes import landscape
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import pandas as pd
from io import BytesIO
import fitz
import math
import qrcode
from PIL import Image
import requests
from bs4 import BeautifulSoup

def drawParagraph_between_two_Ys(can, text, y_max, y_min, w, h, font, color, size, leading, alignment):
    p_style = ParagraphStyle(
        name = 'pstyle',
        fontName=font,
        fontSize=size,
        leading=leading,
        alignment=alignment,
        textColor=HexColor(color)
    )

    p = Paragraph(text = text, style=p_style)
    p_dimensions = p.wrapOn(None, w, h)

    p_x = (can._pagesize[0] - p_dimensions[0]) / 2
    p_y = ((y_min + y_max) - p_dimensions[1]) / 2

    p.wrapOn(can, w, h)
    p.drawOn(can, p_x, p_y)

    return p_dimensions

def calculate_y_middle(y_max, y_min):
    return (y_max + y_min) / 2

def stringHeight(font, font_size):
    face = pdfmetrics.getFont(font).face
    string_height = (face.ascent - face.descent) / 1000 * font_size
    return string_height

def stringHeight(can, text, fontName,fontSize):
    p_style = ParagraphStyle(
        name = 'pstyle',
        fontName=fontName,
        fontSize=fontSize)
    p = Paragraph(text, p_style)
    dimensions = p.wrapOn(None, 100, 100)
    return dimensions[1]

def save_open_pdf(packet, template, output_):
    # create a new PDF with Reportlab
    new_pdf = PdfReader(packet)
    # read your existing PDF
    existing_pdf = PdfReader(open(template, "rb"))
    output = PdfWriter()
    # add the "watermark" (which is the new pdf) on the existing page
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    # # finally, write "output" to a real file
    output_stream = open(output_, "wb")
    output.write(output_stream)
    output_stream.close()

def addFont(path, name):
    pdfmetrics.registerFont(TTFont(name, path))

addFont('Glacial Indifference/GlacialIndifference-Bold.ttf', 'Bold')
addFont('Glacial Indifference/GlacialIndifference-Regular.ttf', 'Regular')

def Convert_PDF_to_JPG(input, output):
    pdf_document = fitz.open(input)

    # Convierte la primera página del PDF a una imagen JPG
    page = pdf_document.load_page(0)  # Carga la primera página (índice 0)
    pix = page.get_pixmap()
    pix.save(output, "jpeg")
    pdf_document.close()

def convert_Y(y, alto_original, alto_nuevo):
    # Invertir la coordenada y
    y_invertida = alto_original - y

    # Convertir la coordenada y invertida a las nuevas dimensiones
    return ((y_invertida / alto_original) * alto_nuevo) + 7

def conseguir_nombre_producto(LINK_):
    response = requests.get(LINK_)
    soup = BeautifulSoup(response.content, 'html.parser')

    name = soup.find('h1',{'class':'product_name'}).text
    return name

def buscar_producto_en_pagina(codigo, producto):
    search = str(codigo) + ' ' + producto[:10]
    search = search.replace(' ','%20')
    link = f"https://www.amahogar.com.ar/busqueda?controller=search&s={search}"
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        articulo = soup.find_all('div', {'class':'pro_outer_box clearfix home_default'})[0]
        url = articulo.find('a', {'itemprop':'url'}).get_attribute_list('href')[0]
        return url
    except IndexError as e:
        return 'no-link'
    

def create_qr(PRODUCTO, CODIGO, LINK, LOGO_PATH):
    # Genera el código QR con un nivel de corrección de errores más alto
    qr = qrcode.QRCode(
        version=5,  # Puedes ajustar la versión del código QR aquí
        error_correction=qrcode.constants.ERROR_CORRECT_Q,  # Cambia el nivel de corrección de errores
        box_size=10,
        border=0,  # Ajusta el tamaño del borde del código QR
    
    )
    qr.add_data(LINK)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    logo = Image.open(LOGO_PATH)
    logo = logo.resize((qr_img.size[0] // 4, qr_img.size[1] // 4))  # Ajusta el tamaño del logo

    # Redondea los bordes del código QR
    qr_img = qr_img.convert("RGBA")
    
    qr_width, qr_height = qr_img.size
    logo_width, logo_height = logo.size
    position = ((qr_width - logo_width) // 2, (qr_height - logo_height) // 2)
    qr_img.paste(logo, position, logo)

    OUTPUT = f'codigos/{CODIGO}.png'
    qr_img.save(OUTPUT)

    template_width = 12.5 * 72
    template_height = 15.62 * 72

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(template_width, template_height))
    page_w, page_h = can._pagesize

    product = str(PRODUCTO)
    producto_text = product.upper()
    producto_font = 'Bold'
    producto_size = 50
    producto_w = 800
    producto_h = 250
    producto_style = ParagraphStyle(name='p2',
                        fontName=producto_font,
                        textColor=HexColor('#000000'),
                        fontSize=producto_size,
                        leading=50,
                        alignment=1)


    p2 = Paragraph(text=producto_text, style=producto_style)

    dimensiones = p2.wrapOn(None, producto_w,producto_h)
    producto_x = (page_w - dimensiones[0]) / 2
    producto_y = ((convert_Y(288.055384067738, 1500, page_h) + page_h) - dimensiones[1]) / 2

    p2.wrapOn(can, producto_w,producto_h)
    p2.drawOn(can, producto_x, producto_y)

    # Codigo Referencial
    codigo_string = str(CODIGO)
    codigo_w = 100
    codigo_h = 100
    codigo_size = 50
    codigo_len = can.stringWidth(codigo_string, 'Regular', codigo_size) + (len(codigo_string) - 1) * 3
    codigo_len_h = stringHeight(can, codigo_string, 'Regular', codigo_size)
    codigo_x = (page_w - codigo_len) / 2
    codigo_y = calculate_y_middle(convert_Y(296.2859044430252, 1500, page_h), convert_Y(391.57266178786523, 1500, page_h)) - 15
    can.setFont('Regular', codigo_size)
    can.setFillColor(HexColor('#000000'))
    can.drawString(x = codigo_x, y = codigo_y, text = codigo_string, charSpace=3)

    # Codigo QR
    qr_path = OUTPUT
    qr_w, qr_h = 600, 600
    can.drawImage(image = qr_path, x = (page_w - qr_w) / 2, y = 112, width=qr_w, height = qr_h)

    can.save()
    packet.seek(0)
    pdf_output_path = f'temporal/{CODIGO}.pdf'
    save_open_pdf(packet, 'pdf/ultima-plantilla.pdf', pdf_output_path)

    Convert_PDF_to_JPG(pdf_output_path, f'codigos_completos/{codigo_string}.jpg')
    os.remove(pdf_output_path)
    os.remove(OUTPUT)
    
def agregar_productos(productos):
    df_principal = pd.read_csv('productos.csv', sep=',')

    df_combinado = pd.concat([df_principal, productos], ignore_index=True, axis=0)
    df_combinado = df_combinado.drop_duplicates(subset='codigo').reset_index(drop=True)
    df_combinado.to_csv('productos.csv', index=False, sep=',')

def generate_pdf_with_multiple_images(image_paths, output_path, max_per_row):
    c = canvas.Canvas(output_path, pagesize=A4)

    width, height = A4
    padding = 5  # Separación entre imágenes

    image_width = (width - (max_per_row + 1) * padding) / max_per_row  # Ancho de la imagen en el PDF
    image_height = image_width + 40  # Alto de la imagen en el PDF (igual al ancho)

    images_drawn = 0
    page = 1

    while images_drawn < len(image_paths):
        c.drawString(10, height - 20, f'Page {page}')  # Añadir el número de página
        images_on_page = min(len(image_paths) - images_drawn, max_per_row * math.floor(height / (image_height + padding)))

        for i in range(images_on_page):
            image_path = image_paths[images_drawn + i]
            x = padding + (i % max_per_row) * (image_width + padding)
            y = height - padding - (math.floor(i / max_per_row) + 1) * (image_height + padding)
            c.drawImage(image_path, x, y, width=image_width, height=image_height)

        images_drawn += images_on_page
        if images_drawn < len(image_paths):
            c.showPage()  # Cambiar a la siguiente página
            page += 1

    c.save()