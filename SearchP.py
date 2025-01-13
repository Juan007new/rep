from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time

def telegram_bot_sendtext(bot_message):
    bot_token  = '7693801036:AAF8V_3EA74x-hfXk2DpRoY6hm2-_x9fx44'
    bot_chatID = '1507772195'
    enviar_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(enviar_text)
    return response.json()

# Configuración de Selenium con WebDriverManager y modo Headless
options = Options()
options.add_argument('--headless')  # Ejecutar en modo sin interfaz gráfica
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--remote-debugging-port=9222')  # Opcional, para depuración remota

# Inicializar el driver en modo headless
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL base de la página con los productos
base_urlshop = 'https://shopstar.pe'
base_url = 'https://shopstar.pe/telefonia/celulares/plazavea?initialMap=seller&initialQuery=plazavea&map=category-2,category-3,seller&order=OrderByPriceASC&page='

# Número de páginas a recorrer (puedes ajustarlo según sea necesario)
total_pages = 15

# Lista para almacenar productos extraídos
all_products = []

# Recorrer todas las páginas desde la 1 hasta total_pages
for page_number in range(1, total_pages + 1):
    url = base_url + str(page_number)
    driver.get(url)

    # Verificar si aparece el mensaje "No se encontró ningún producto"
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'No se encontró ningún producto')]")))
        print(f"No se encontraron productos en la página {page_number}. Terminando el proceso.")
        break  # Detener el ciclo si se encuentra el mensaje
    except:
        pass  # Continuar si no se encuentra el mensaje

    # Realizar un desplazamiento gradual
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_step = 500  # Desplazar 500px a la vez
    current_scroll_position = 0
    products_found = 0

    while True:
        driver.execute_script(f"window.scrollTo(0, {current_scroll_position + scroll_step});")
        current_scroll_position += scroll_step
        time.sleep(2)  # Esperar 2 segundos para permitir la carga de los productos

        # Obtener la nueva altura para verificar si hemos llegado al final de la página
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:  # Si no se cargaron nuevos productos
            break

        last_height = new_height

    # Esperar a que se terminen de cargar los productos
    WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'vtex-search-result-3-x-galleryItem')))

    # Obtener el contenido HTML
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Buscar todos los productos usando la clase correcta
    product_tags = soup.find_all('div', class_='vtex-search-result-3-x-galleryItem')

    print(f"Cantidad de productos en la página {page_number}: {len(product_tags)}")

    if product_tags:
        for product in product_tags:
            # Nombre del producto
            name_tag = product.find('span', class_='vtex-product-summary-2-x-productBrand')
            product_name = name_tag.text.strip() if name_tag else 'Nombre no disponible'

            # Enlace del producto
            product_link_tag = product.find('a', href=True)
            product_link = base_urlshop + product_link_tag['href'] if product_link_tag else 'Enlace no disponible'

            # Precio del producto
            price_tag = product.find('div', class_='mercury-interbank-components-0-x-summary_normalPricesContainer')

            if price_tag:
                price_span = price_tag.find('span', class_='mercury-interbank-components-0-x-listPrice')
                price_span2 = price_tag.find('span', class_='mercury-interbank-components-0-x-sellingPrice mercury-interbank-components-0-x-sellingPrice--hasListPrice')
                if price_span2:
                    product_price2 = price_span2.text.strip()
                    product_price2 = float(product_price2.replace("S/", "").replace(" ", "").replace(",", ""))
                else:
                    product_price2 = 9999
                if price_span:
                    product_price = price_span.text.strip()
                    product_price = float(product_price.replace("S/", "").replace(" ", "").replace(",", ""))
                else:
                    product_price = 1

            # Guardar producto
            all_products.append({
                'name': product_name,
                'price': product_price,
                'link': product_link,
                'priceoff': product_price2,
            })

            # Verificar si el producto tiene descuento y enviar alerta
            if product_price2 > 0:
                # Asegúrate de que no haya errores en los cálculos
                if (1 - product_price2 / product_price) > 0.4:
                    message = f"Producto: {product_name}\n % Dscto:{round((1 - product_price2 / product_price) * 100, 2)}%\n Precio con descuento: S/{product_price2}\nPrecio lista: S/{product_price}\nEnlace: {product_link}"
                    telegram_bot_sendtext(message)
            else:
                print("error")

        # Si no encontramos productos nuevos, detener el ciclo
        if len(product_tags) == 0:
            print("No hay más productos en esta página, terminando el proceso.")
            break

    else:
        print(f'No se encontraron productos en la página {page_number}.')
    
    time.sleep(3)  # Pausa para evitar demasiadas peticiones

# Mostrar todos los productos extraídos
print(f"Se han extraído {len(all_products)} productos.")
for product in all_products:
    print(f'Producto: {product["name"]}, Precio: {product["price"]},Precioff:{product["priceoff"]}, Enlace: {product["link"]}')

# Cerrar el navegador
driver.quit()

