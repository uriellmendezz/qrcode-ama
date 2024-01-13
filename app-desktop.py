import os
import tkinter as tk
from tkinter import filedialog, messagebox, font, PhotoImage
import pandas as pd
from reportlab.pdfgen import canvas
import time
import functions
import datetime as dt
import os

class ExcelToPdfConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Creador de Codigos QR - AMAHOGAR")
        bg = self.imagen_fondo = PhotoImage(file="backg.png")
        label1 = tk.Label( root, image = bg) 
        label1.place(x = 0, y = 0) 

        # Configurar el tamaño de la ventana
        self.root.geometry("700x400")

        self.root.resizable(width=False, height=False)

        self.root.configure(bg="#ffffff")

        self.file_path = tk.StringVar()

        browse_button = tk.Button(
            self.root,
            text="BUSCAR ARCHIVO",
            command=self.browse_file,
            font=("Helvetica", 16),
            bd=0,                      # Grosor del borde
            relief=tk.FLAT,            # Estilo de relieve (flat para sin relieve)
            bg="#ff0016",                # Color de fondo negro
            fg="#ffffff",                # Color de letra blanco
            activebackground="#ffffff",   # Color de fondo al presionar
            activeforeground="#ff0016",  # Color de letra al presionar
            padx=20,
            pady=10
        )
        browse_button.pack(pady=30)

        tk.Label(root, text="ARCHIVO SELECCIONADO:", bg=None, fg="#ff0016", font=("Helvetica", 12)).pack(pady=10)

        tk.Entry(root, textvariable=str(self.file_path).split('/')[-1], width=40, font=('Helvetica', 12), justify='center').pack(pady=10)

        # Botón "Convertir y Abrir PDF" con borde redondeado
        convert_button = tk.Button(
            self.root,
            text="CONVERTIR Y ABRIR PDF",
            command=self.start_process,
            font=("Helvetica", 16),
            bd=0,
            relief=tk.FLAT,
            bg="#ff0016",                # Color de fondo negro
            fg="#ffffff",                # Color de letra blanco
            activebackground="#ffffff",   # Color de fondo al presionar
            activeforeground="#ff0016",
            padx=20,
            pady=10
        )
        convert_button.pack(pady=30)

        self.success_label = tk.Label(self.root, text="", bg="#ffffff", fg="green", font=("Helvetica", 12))
        self.success_label.pack()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx;*.xls")])
        self.file_path.set(file_path)

    def start_process(self):
        self.success_label.config(text="El proceso se realizo con exito.", fg="green")
        self.convert_to_pdf()

    def convert_to_pdf(self):
        excel_file_path = self.file_path.get()

        if not excel_file_path:
            tk.messagebox.showerror("Error", "Por favor, seleccione un archivo Excel.")
            return

        try:
            START = time.time()

            productos = pd.read_excel(excel_file_path, header=None)
            productos = productos.rename(columns={0:'codigo', 1:'producto'})
            data = pd.read_csv('productos.csv', sep=',')

            productos_nuevos = {
                'producto':[],
                'linkproducto':[],
                'codigo':[],
                'categoria':[]
            }

            failed_codes = {
                'codigo':[],
                'producto':[]
            }

            funcionan = []

            for row in range(len(productos)):
                try:
                    fila = int(data.loc[data.codigo.astype(str) == str(productos.iloc[row].codigo)].index[0])
                    codigo_value = data.iloc[fila].codigo
                    link_value = data.iloc[fila].linkproducto
                    producto_value = data.iloc[fila].producto
                    categoria_value = link_value.split('/')[3]
                    functions.create_qr(producto_value, codigo_value, link_value, 'logo.png')
                    funcionan.append(str(codigo_value))
                    
                except IndexError as e:
                    codigo_value = str(productos.iloc[row].codigo)
                    producto_pre = str(productos.iloc[row].producto)
                    link_value = functions.buscar_producto_en_pagina(codigo_value, producto_pre)

                    if link_value == 'no-link':
                        failed_codes['codigo'].append(codigo_value)
                        failed_codes['producto'].append(producto_pre)
                    
                    else:
                        producto_value = functions.conseguir_nombre_producto(link_value)
                        categoria_value = link_value.split('/')[3]
                        functions.create_qr(producto_value, codigo_value, link_value, 'logo.png')
                        productos_nuevos['producto'].append(producto_value)
                        productos_nuevos['linkproducto'].append(link_value)
                        productos_nuevos['codigo'].append(codigo_value)
                        productos_nuevos['categoria'].append(categoria_value)
                        funcionan.append(str(codigo_value))

            df_nuevos_productos = pd.DataFrame(productos_nuevos)
            functions.agregar_productos(df_nuevos_productos)
            
            imagenes_codigos = [f'codigos_completos/{cd}.jpg' for cd in funcionan]

            d = dt.datetime.now()
            formatted_date = d.strftime('%d-%m-%Y-%H-%M-%S')
            output_user_file =  f'CODIGOS-QR-{formatted_date}.pdf'

            functions.generate_pdf_with_multiple_images(imagenes_codigos, output_user_file, 3)

            FINISH = time.time()
            TOTAL_TIME = FINISH - START
            TOTAL_TIME_FORMATTED = str(dt.timedelta(seconds=TOTAL_TIME)).split(".")[0]
            

            for f in os.listdir('codigos_completos/'):
                os.remove('codigos_completos/' + f)

            tk.messagebox.showinfo("Éxito", "La conversión a PDF se completó con éxito.")
            os.system(f'start {output_user_file}')

            # os.remove(output_user_file)
            # os.remove(excel_file_path)

        except Exception as e:
            tk.messagebox.showerror("Error", f"Error durante la conversión: {str(e)}")
            print(e)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToPdfConverter(root)
    root.mainloop()

