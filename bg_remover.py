import os
from PIL import Image
from rembg import remove, new_session
from tqdm import tqdm
import io

# --- CONFIGURACIÓN ---
# Cambia esto por la ruta donde están tus 300 imágenes originales
CARPETA_ENTRADA = "data/raw"

# Cambia esto por la ruta donde quieres guardar las nuevas imágenes
# (El script creará la carpeta si no existe)
CARPETA_SALIDA = "data/processed"

# Extensiones de archivo permitidas
EXTENSIONES_VALIDAS = ('.jpg', '.jpeg', '.png')
# ----------------------

session_cpu = new_session("u2net")

def procesar_imagen(ruta_imagen_entrada, carpeta_salida):
    nombre_archivo = os.path.basename(ruta_imagen_entrada)
    nombre_base = os.path.splitext(nombre_archivo)[0]
    ruta_imagen_salida = os.path.join(carpeta_salida, nombre_base + "_black_bg.png")

    try:
        # 1. Abrir la imagen original
        img_original = Image.open(ruta_imagen_entrada).convert("RGBA")

        # 2. Quitar el fondo usando la sesión de CPU definida arriba
        # rembg acepta directamente objetos PIL.Image, no hace falta convertir a bytes
        img_sin_fondo = remove(img_original, session=session_cpu) # <--- CAMBIO: Más eficiente

        # 3. Crear fondo negro
        fondo_negro = Image.new("RGBA", img_sin_fondo.size, (0, 0, 0, 255))

        # 4. Componer
        fondo_negro.paste(img_sin_fondo, (0, 0), img_sin_fondo)

        # 5. Guardar
        fondo_negro.save(ruta_imagen_salida, format="PNG")

    except Exception as e:
        print(f"\nError procesando {nombre_archivo}: {e}")

def main():
    # Verificar si la carpeta de entrada existe
    if not os.path.isdir(CARPETA_ENTRADA):
        print(f"Error: La carpeta de entrada '{CARPETA_ENTRADA}' no existe.")
        return

    # Crear la carpeta de salida si no existe
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    print(f"Iniciando proceso...")
    print(f"Leyendo desde: {CARPETA_ENTRADA}")
    print(f"Guardando en: {CARPETA_SALIDA}")

    # Obtener lista de archivos de imagen
    archivos_imagen = [
        f for f in os.listdir(CARPETA_ENTRADA)
        if f.lower().endswith(EXTENSIONES_VALIDAS) and os.path.isfile(os.path.join(CARPETA_ENTRADA, f))
    ]

    total_imagenes = len(archivos_imagen)
    print(f"Se encontraron {total_imagenes} imágenes para procesar.\n")

    if total_imagenes == 0:
        print("No se encontraron imágenes válidas en la carpeta de entrada.")
        return

    # Bucle principal con barra de progreso (tqdm)
    for nombre_archivo in tqdm(archivos_imagen, desc="Procesando imágenes"):
        ruta_completa = os.path.join(CARPETA_ENTRADA, nombre_archivo)
        procesar_imagen(ruta_completa, CARPETA_SALIDA)

    print(f"\n¡Proceso completado! Revisa la carpeta: {CARPETA_SALIDA}")

if __name__ == "__main__":
    # Nota: La primera vez que ejecutes esto, rembg descargará
    # un modelo de IA (aprox 170MB). Ten paciencia.
    main()