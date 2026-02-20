import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# FUNCIÓN DE DESCARGA (Lo que hicimos antes)
# ==========================================
def descargar_playera(url_playera, driver, wait, carpeta_destino):
    try:
        print(f"\nProcesando: {url_playera}")
        driver.get(url_playera)

        # 1. Capturar Contexto (Título)
        elemento_titulo = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        nombre_archivo = elemento_titulo.text.lower().replace(" ", "_").replace("/", "-") + ".jpg"

        # 2. Localizar CDN
        elemento_imagen = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//img[contains(@src, 'cdn.footballkitarchive.com')]")
        ))
        url_cdn = elemento_imagen.get_attribute("src")

        # 3. Descargar y Guardar
        respuesta = requests.get(url_cdn)
        if respuesta.status_code == 200:
            ruta_final = os.path.join(carpeta_destino, nombre_archivo)
            with open(ruta_final, 'wb') as archivo:
                archivo.write(respuesta.content)
            print(f"Éxito: {nombre_archivo}")
        else:
            print(f"Error al descargar la imagen de: {url_playera}")

    except Exception as e:
        print(f"Error procesando {url_playera}: {e}")

# ==========================================
# SCRIPT PRINCIPAL (El Bucle Maestro)
# ==========================================
def iniciar_scraping_chivas():
    # Configuración del navegador
    opciones = Options()
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)
    wait = WebDriverWait(driver, 10)
    
    carpeta_destino = "dataset_chivas"
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    try:
        # 1. Ir al catálogo principal
        print("Accediendo al catálogo principal de Chivas...")
        driver.get("https://www.footballkitarchive.com/chivas-de-guadalajara-kits/")
        time.sleep(3) # Pausa inicial para que cargue la estructura básica

        # 2. Hacer Scroll hasta el final (Vencer el Lazy Loading)
        print("Haciendo scroll para cargar todas las playeras...")
        altura_anterior = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Bajar hasta el fondo de la página actual
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) # Esperar a que carguen las nuevas miniaturas
            
            # Calcular la nueva altura
            nueva_altura = driver.execute_script("return document.body.scrollHeight")
            if nueva_altura == altura_anterior:
                print("Se ha llegado al final del catálogo.")
                break
            altura_anterior = nueva_altura

        # 3. Recolectar todas las URLs
        # Buscamos todos los enlaces que contengan '-kit/' en su URL
        print("Recolectando enlaces de cada playera...")
        elementos_enlace = driver.find_elements(By.XPATH, "//a[contains(@href, '-kit/')]")
        
        # Filtramos para asegurarnos de que sean URLs válidas y únicas
        lista_urls = []
        for elemento in elementos_enlace:
            href = elemento.get_attribute("href")
            # Nos aseguramos de que sea un link de chivas y no lo hayamos repetido
            if href and "chivas" in href and href not in lista_urls:
                lista_urls.append(href)

        print(f"¡Se encontraron {len(lista_urls)} playeras únicas!")

        # 4. El Bucle Principal
        print("\nIniciando descarga masiva...")
        for url in lista_urls:
            descargar_playera(url, driver, wait, carpeta_destino)
            
            # GUARDARRAÍL ÉTICO Y TÉCNICO: Pausa aleatoria entre cada descarga
            # Esto evita que satures el servidor y que te bloqueen la IP
            time.sleep(2) 

    finally:
        print("\nProceso terminado. Cerrando navegador.")
        driver.quit()

# Ejecutar el script
if __name__ == "__main__":
    iniciar_scraping_chivas()