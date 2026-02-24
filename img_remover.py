import os
import cv2 # <--- Usaremos OpenCV

CARPETA_OBJETIVO = "data/processed"
EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png')

def limpiar_directorio(ruta_carpeta):
    archivos = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(EXTENSIONES_IMAGEN)]
    
    for nombre_archivo in archivos:
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        
        # Leer y mostrar la imagen en una ventana de OpenCV
        img = cv2.imread(ruta_completa)
        if img is None: continue

        # Redimensionar solo para la vista previa si es muy grande
        # (Para que no ocupe toda la pantalla)
        vista_previa = cv2.resize(img, (800, 600)) if img.shape[1] > 800 else img
        
        cv2.imshow("Revisando: " + nombre_archivo, vista_previa)
        cv2.waitKey(1) # Forzar el refresco de la ventana

        decision = input(f"¿Borrar {nombre_archivo}? (y/Enter/q): ").lower()

        # CERRAR LA VENTANA antes de procesar la respuesta
        cv2.destroyAllWindows()

        if decision == 'y':
            os.remove(ruta_completa)
            print(f"--- [ELIMINADO]")
        elif decision == 'q':
            break

if __name__ == "__main__":
    limpiar_directorio(CARPETA_OBJETIVO)