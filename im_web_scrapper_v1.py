# Funcion de Descarga de Jerseys, Remeras, Playeras, Camisetas de futbol
# del Club Deportivo Guadalajara, Atletico de Madrid, Club Junior (col), Olympiacos
# Southampton, Sporting Gijon y Stoke City.
#  
# Autor: Ivan Morales 
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

# Funcion principal para iniciar el scrapping de las imagenes a traves de 
# el sitio web https://www.footballkitarchive.com/
def iniciar_scraping():
    # Configuración del navegador
    opciones = Options()
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
    
    driver = webdriver.Chrome(options=opciones)
    wait = WebDriverWait(driver, 10)
    
    carpeta_destino = "dataset_olympiacos"
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    try:
        # 1. Ir al catálogo principal
        print("Accediendo al catálogo principal de Olympiacos...")
        driver.get("https://www.footballkitarchive.com/olympiacos-piraeus-kits/")
        time.sleep(3) # Pausa inicial para que cargue la estructura básica

        # 2. Hacer Scroll hasta el final (previene el Lazy Loading)
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

        # 3. Recolectar solo las URLs de Local (Home)
        print("Recolectando EXCLUSIVAMENTE enlaces de playeras de local (Home)...")
        
        # Ajuste 1: El XPath ahora exige que el enlace contenga '-home-kit/'
        elementos_enlace = driver.find_elements(By.XPATH, "//a[contains(@href, '-home-kit/')]")
        
        lista_urls = []
        for elemento in elementos_enlace:
            href = elemento.get_attribute("href")
            
            # Ajuste 2: Doble validación en Python para asegurar que sea 'home-kit' y único
            if href and "-home-kit/" in href and href not in lista_urls:
                lista_urls.append(href)

        print(f"¡Se encontraron {len(lista_urls)} playeras únicas!")

        # 4. El Bucle Principal
        print("\nIniciando descarga de las imagenes..")
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
    iniciar_scraping()