#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import argparse
import socket
import sys
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
# Ignoramos las advertencias de certificados SSL auto-firmados, etc.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: La librería 'BeautifulSoup' no está instalada. Por favor, instálala con: pip install beautifulsoup4")
    sys.exit(1)

# --- Clases para colores en la terminal ---
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

# --- Banner de la herramienta ---
def print_banner():
    banner = f"""
{Colors.BLUE}
 {Colors.GREEN}v3.1{Colors.BLUE}
 
 _____  _____      ______               __        
|_   _||_   _|    / ____ `.            [  |       
  | |    | |_   __`'  __) |.--. __   _  | |.--.   
  | '    ' [ \ [  _  |__ '( (`\[  | | | | '/'`\ \ 
   \ \__/ / \ \/ | \____) |`'.'.| \_/ |,|  \__/ | 
    `.__.'   \__/ \______.[\__) '.__.'_[__;.__.'           {Colors.YELLOW}By Uv3doble - Subdominios de forma pasiva {Colors.RESET}
"""
    print(banner)

# --- Búsqueda pasiva ---
def search_crtsh(domain):
    print(f"{Colors.CYAN}[*] Buscando subdominios pasivamente en crt.sh para: {domain}{Colors.RESET}")
    subdomains = set()
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        for entry in response.json():
            name_value = entry.get('name_value', '')
            if name_value:
                for sub in name_value.split('\n'):
                    if sub.strip().endswith(f".{domain}") and not sub.strip().startswith('*'):
                        subdomains.add(sub.strip())
    except Exception as e:
        print(f"{Colors.RED}[!] Error durante la búsqueda pasiva: {e}{Colors.RESET}")
    
    if not subdomains:
        print(f"{Colors.RED}[-] No se encontraron subdominios.{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}[+] Búsqueda completada. Encontrados {len(subdomains)} subdominios únicos.{Colors.RESET}")
    
    return list(subdomains)

# --- Sondeo web ---
def probe_subdomain(subdomain):
    protocols = ['https', 'http']
    for protocol in protocols:
        url = f"{protocol}://{subdomain}"
        try:
            response = requests.get(url, timeout=10, allow_redirects=True, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
            final_url = response.url
            hostname = urlparse(final_url).hostname
            ip_address = "N/A"
            try:
                ip_address = socket.gethostbyname(hostname)
            except socket.gaierror: pass
            
            title = "N/A"
            if 'text/html' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag: title = " ".join(title_tag.get_text().strip().split())

            return {
                "url": final_url, "status_code": response.status_code, "ip": ip_address,
                "title": title, "server": response.headers.get('Server', 'N/A')
            }
        except (requests.exceptions.RequestException):
            continue
    return None

def get_status_color(status_code):
    if 200 <= status_code < 300: return Colors.GREEN
    if 300 <= status_code < 400: return Colors.YELLOW
    if 400 <= status_code < 500: return Colors.BLUE
    if 500 <= status_code < 600: return Colors.RED
    return Colors.RESET

# --- Nueva función para imprimir las tablas de resultados ---
def print_results_table(title, results, color):
    if not results:
        return
    
    print(f"\n {color}╔═══ [ {title.upper()} ] ═══════════════════════════════════════════════════════════╗{Colors.RESET}")
    
    # Cabecera
    print(f" {color}║ {'URL'.ljust(60)} {'STATUS'.ljust(8)} {'IP'.ljust(16)} {'SERVER'.ljust(20)} {'TITLE'} {'║'}{Colors.RESET}")
    print(f" {color}╟{'─'*61}╢{'─'*9}╢{'─'*17}╢{'─'*21}╢{'─'*30}╢{Colors.RESET}")

    for r in results:
        url_display = (r['url'][:57] + '...') if len(r['url']) > 60 else r['url']
        server_display = str(r.get('server') or 'N/A') # Asegurarse de que no sea None
        server_display = (server_display[:18] + '..') if len(server_display) > 20 else server_display
        title_display = (r['title'][:27] + '...') if len(r['title']) > 30 else r['title']
        
        status_str = f"{get_status_color(r['status_code'])}{r['status_code']}{color}"

        print(f" {color}║ {url_display.ljust(60)} {status_str.ljust(18)} {r['ip'].ljust(16)} {server_display.ljust(20)} {title_display.ljust(29)} ║{Colors.RESET}")

    print(f" {color}╚{'═'*143}╝{Colors.RESET}")

# --- Nueva barra de progreso ---
def print_progress(processed, total, counts):
    progress = processed / total
    bar = f"[{int(progress * 40) * '='}>{(40 - int(progress * 40)) * ' '}]"
    
    status_summary = " | ".join([f"{get_status_color(k)}{k}:{v}{Colors.CYAN}" for k, v in sorted(counts.items())])
    
    sys.stdout.write(f"\r{Colors.CYAN}Progreso: {bar} {progress:.1%} | Encontrados: {sum(counts.values())} | {status_summary}      ")
    sys.stdout.flush()

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Herramienta avanzada para encontrar y sondear subdominios activos.")
    parser.add_argument("domain", help="El dominio objetivo para escanear (ej: example.com)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Número de hilos para el sondeo web (default: 50)")
    args = parser.parse_args()

    potential_subdomains = search_crtsh(args.domain)
    if not potential_subdomains:
        sys.exit(0)

    print(f"\n{Colors.CYAN}[*] Iniciando sondeo en {len(potential_subdomains)} subdominios con {args.threads} hilos...{Colors.RESET}")
    
    all_results = []
    status_counts = {}
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_to_subdomain = {executor.submit(probe_subdomain, sub): sub for sub in potential_subdomains}
        
        for i, future in enumerate(as_completed(future_to_subdomain)):
            result = future.result()
            if result:
                all_results.append(result)
                status = result['status_code']
                status_counts[status] = status_counts.get(status, 0) + 1
            print_progress(i + 1, len(potential_subdomains), status_counts)

    print("\n\n" + "-" * 60)
    print(f"{Colors.GREEN}[✔] Fase de sondeo finalizada. Procesando y deduplicando resultados...{Colors.RESET}")

    # --- INICIO DEL CAMBIO CLAVE: DEDUPLICACIÓN ---
    unique_results = []
    seen_urls = set()
    for result in all_results:
        if result['url'] not in seen_urls:
            unique_results.append(result)
            seen_urls.add(result['url'])
    # --- FIN DEL CAMBIO CLAVE ---
    
    # Filtrar resultados poco interesantes
    filtered_results = [r for r in unique_results if not (r['status_code'] == 400 and 'Invalid URL' in r['title'])]
    
    # Agrupar resultados
    results_2xx = sorted([r for r in filtered_results if 200 <= r['status_code'] < 300], key=lambda x: x['url'])
    results_3xx = sorted([r for r in filtered_results if 300 <= r['status_code'] < 400], key=lambda x: x['url'])
    results_4xx = sorted([r for r in filtered_results if 400 <= r['status_code'] < 500], key=lambda x: (x['status_code'], x['url']))
    results_5xx = sorted([r for r in filtered_results if 500 <= r['status_code'] < 600], key=lambda x: (x['status_code'], x['url']))
    
    # Imprimir tablas
    print_results_table("2xx SUCCESS", results_2xx, Colors.GREEN)
    print_results_table("3xx REDIRECTION", results_3xx, Colors.YELLOW)
    print_results_table("4xx CLIENT ERROR", results_4xx, Colors.BLUE)
    print_results_table("5xx SERVER ERROR", results_5xx, Colors.RED)

    print(f"\n{Colors.GREEN}[✔] Análisis completo. Total de sitios web únicos encontrados: {len(filtered_results)}.{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}[!] Escaneo interrumpido por el usuario. Saliendo.{Colors.RESET}")
        sys.exit(0)
