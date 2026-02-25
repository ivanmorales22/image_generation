import cv2
import numpy as np
import os
from pathlib import Path

def letterbox_image(image, size=(256, 256)):
    """Aplica el redimensionamiento manteniendo proporción y centrando en fondo negro."""
    ih, iw = image.shape[:2]
    w, h = size
    
    # 1. Calcular el factor de escala manteniendo el aspecto
    scale = min(w/iw, h/ih)
    nw, nh = int(iw * scale), int(ih * scale)
    
    # 2. Redimensionar con interpolación de área (mejor para reducir tamaño)
    image_resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)
    
    # 3. Crear lienzo negro (fondo normalizado)
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    
    # 4. Calcular coordenadas para centrar la imagen
    dx = (w - nw) // 2
    dy = (h - nh) // 2
    
    # 5. Pegar la imagen en el centro del canvas
    canvas[dy:dy+nh, dx:dx+nw] = image_resized
    return canvas

# --- CONFIGURACIÓN DE CARPETAS ---
input_folder = 'data/processed'
output_folder = 'data/interim'
target_size = (256, 256)  # El tamaño que usará tu VAE

# Crear carpeta de salida si no existe
Path(output_folder).mkdir(parents=True, exist_ok=True)

# Extensiones permitidas
valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')

print(f"Iniciando procesamiento en: {input_folder}")

# --- BUCLE DE PROCESAMIENTO ---
for filename in os.listdir(input_folder):
    if filename.lower().endswith(valid_extensions):
        img_path = os.path.join(input_folder, filename)
        
        # Leer imagen
        img = cv2.imread(img_path)
        
        if img is not None:
            # Procesar
            processed_img = letterbox_image(img, size=target_size)
            
            # Guardar en la nueva carpeta
            save_path = os.path.join(output_folder, filename)
            cv2.imwrite(save_path, processed_img)
        else:
            print(f"Error al leer: {filename}")

print(f"¡Listo! Imágenes guardadas en: {output_folder}")