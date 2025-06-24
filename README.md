# Uv3Sub - Reconocimiento de Subdominios

Uv3Sub es una herramienta de reconocimiento de subdominios escrita en Python. Realiza una búsqueda pasiva para descubrir subdominios y luego los sondea activamente para determinar si alojan un servidor web, presentando los resultados de una manera limpia, ordenada y priorizada.

## Características Principales

- **Búsqueda Pasiva:** Utiliza `crt.sh` para descubrir subdominios sin enviar tráfico directo al objetivo.
    
- **Sondeo Activo:** Intenta conectarse a cada subdominio encontrado a través de `HTTP` y `HTTPS`.
    
- **Recolección de Datos:** Para cada subdominio activo, extrae:
    
    - Código de estado HTTP (200, 403, 301, etc.).
        
    - Dirección IP del servidor.
        
    - Título de la página web.
        
    - Cabecera del Servidor (Nginx, Apache, etc.).
        
- **Salida Clara y Organizada:**
    
    - Muestra los resultados en tablas agrupadas por código de estado (2xx, 3xx, 4xx, 5xx).
        
    - Aplica colores para una fácil identificación de los resultados.
        
    - Deduplica los resultados para mostrar solo las URLs finales únicas.
        
    - Filtra el "ruido" de resultados poco interesantes (como errores 400 de Akamai).
        

## Instalación

1. **Clona el repositorio desde GitHub:**
    
    ```
    git clone [https://github.com/uv3doble/Uv3Sub.git](https://github.com/uv3doble/Uv3Sub.git)
    cd Uv3Sub
    ```
    
2. **Crea un entorno virtual (muy recomendado):**
    
    ```
    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    
    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```
    
3. **Instala las dependencias:** El archivo `requirements.txt` contiene todas las librerías necesarias. Instálalas con un solo comando:
    
    ```
    pip install -r requirements.txt
    ```
    

## Modo de Uso

El uso de la herramienta es sencillo. Simplemente ejecuta el script seguido del dominio que deseas analizar.

**Sintaxis básica:**

```
python Uv3Sub.py <dominio_objetivo>
```

**Ejemplo:**

```
python Uv3Sub.py tesla.com
```

### Opciones

- `-t` o `--threads`: Especifica el número de hilos a utilizar para el sondeo web, lo que puede acelerar significativamente el escaneo. El valor por defecto es 50.
    

**Ejemplo con más hilos:**

```
python Uv3Sub.py google.com -t 100
```

## Entendiendo la Salida

La herramienta presentará los resultados en tablas separadas para facilitar el análisis:

- **`2xx SUCCESS` (Verde):** Los hallazgos más importantes. Son sitios web activos que respondieron correctamente. ¡Aquí es donde debes centrar tu atención primero!
    
- **`3xx REDIRECTION` (Amarillo):** Subdominios que redirigen a otra URL. La tabla mostrará la URL final. Es útil para entender el flujo del tráfico.
    
- **`4xx CLIENT ERROR` (Azul):** ¡Resultados muy interesantes! Indican que el servidor está activo pero el acceso está restringido (`403 Forbidden`, `401 Unauthorized`) o no se encontró la página (`404 Not Found`). Confirma la existencia de un servicio web en ese subdominio.
    
- **`5xx SERVER ERROR` (Rojo):** El servidor está en línea pero experimenta errores internos. Esto puede indicar una mala configuración o una oportunidad para investigar más a fondo.
