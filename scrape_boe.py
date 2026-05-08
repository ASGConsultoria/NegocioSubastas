"""
Descarga subastas reales del BOE para Euskadi y genera un JSON.
Se ejecuta automáticamente cada 3 días vía GitHub Actions.
"""
import json
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlencode
import urllib.request
from html.parser import HTMLParser

# Provincias de Euskadi en el sistema del BOE
PROVINCIAS = {
    "01": "Álava",
    "20": "Gipuzkoa",
    "48": "Bizkaia",
}

# Tipos de bien (códigos del BOE)
TIPOS = {
    "BIEN-INMUEBLE-VIVIENDA": "Vivienda",
    "BIEN-INMUEBLE-LOCAL-COMERCIAL": "Local comercial",
    "BIEN-INMUEBLE-GARAJE": "Garaje",
    "BIEN-INMUEBLE-TRASTERO": "Trastero",
    "BIEN-INMUEBLE-SOLAR": "Solar",
    "BIEN-INMUEBLE-FINCA-RUSTICA": "Finca rústica",
    "BIEN-INMUEBLE-NAVE-INDUSTRIAL": "Nave industrial",
    "BIEN-INMUEBLE-OTROS": "Otros inmuebles",
}

BASE_URL = "https://subastas.boe.es/subastas_ava.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def fetch(url, timeout=30):
    """Descarga una URL respetando el servidor."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build_search_url(prov_code, page=1):
    """Construye URL de búsqueda en BOE para inmuebles en una provincia."""
    params = {
        "campo[0]": "SUBASTA.ESTADO",
        "dato[0]": "EJ",  # En ejecución (subasta abierta para pujas)
        "campo[1]": "BIEN.TIPO",
        "dato[1]": "B",   # Inmuebles
        "campo[2]": "DIRECCION.CODPROV",
        "dato[2]": prov_code,
        "campo[3]": "",
        "dato[3]": "",
        "page_hits": "100",
        "sort_field[0]": "SUBASTA.FECHA_FIN_YMD",
        "sort_order[0]": "desc",
        "accion": "Buscar",
    }
    if page > 1:
        params["page"] = page
    return f"{BASE_URL}?{urlencode(params)}"


def parse_listing(html):
    """Extrae los IDs de subasta del listado.

    Cada subasta en el HTML aparece como un enlace tipo:
    /subastas_ava.php?accion=Mas&idBus=SUB-JA-2025-XXXXXX
    """
    # Buscar todos los IDs de subasta (formato SUB-XX-YYYY-NNNNNN)
    ids = re.findall(r'idBus=(SUB-[A-Z]{1,3}-\d{4}-\d+)', html)
    return list(dict.fromkeys(ids))  # eliminar duplicados manteniendo orden


def parse_subasta(html, subasta_id):
    """Extrae datos de la página de detalle de una subasta."""
    data = {
        "id": subasta_id,
        "url": f"https://subastas.boe.es/detalleSubasta.php?idSub={subasta_id}",
        "url_busqueda": f"https://subastas.boe.es/subastas_ava.php?accion=Mas&idBus={subasta_id}",
    }

    # Quitar tags pero conservar texto
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()

    # Patrones para campos importantes
    patterns = {
        "valor_subasta": r'Valor [Ss]ubasta[:\s]*([0-9.,]+)\s*€',
        "valor_tasacion": r'Valor [Ss]ubasta[:\s]*([0-9.,]+)\s*€',
        "deposito": r'(?:Importe del )?[Dd]ep[óo]sito[:\s]*([0-9.,]+)\s*€',
        "tipo_subasta": r'Tipo de subasta[:\s]*([0-9.,]+)\s*€',
        "puja_minima": r'Puja m[íi]nima[:\s]*([0-9.,]+)\s*€',
        "fecha_inicio": r'Fecha de inicio[:\s]*([0-9/]+\s*[0-9:]*)',
        "fecha_fin": r'Fecha de conclusi[óo]n[:\s]*([0-9/]+\s*[0-9:]*)',
        "localidad": r'Localidad[:\s]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s\-]+?)(?:\s{2,}|Provincia|C[óo]digo|$)',
        "provincia": r'Provincia[:\s]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s/]+?)(?:\s{2,}|C[óo]digo|Direcci|$)',
        "direccion": r'Direcci[óo]n[:\s]*([^,]+?)(?:\s{2,}|Localidad|C[óo]digo|$)',
        "cp": r'C[óo]digo [Pp]ostal[:\s]*(\d{5})',
        "ref_catastral": r'Referencia [Cc]atastral[:\s]*([A-Z0-9]{14,20})',
        "tipo_bien": r'Tipo de [Bb]ien[:\s]*([A-Za-zÁÉÍÓÚáéíóú\s]+?)(?:\s{2,}|Subtipo|Direcc|$)',
    }

    for field, pattern in patterns.items():
        m = re.search(pattern, text)
        if m:
            value = m.group(1).strip()
            # Convertir importes a número
            if field in ("valor_subasta", "valor_tasacion", "deposito", "tipo_subasta", "puja_minima"):
                try:
                    value = float(value.replace(".", "").replace(",", "."))
                except ValueError:
                    value = None
            data[field] = value

    # Descripción del bien (suele ser el bloque más largo)
    desc_match = re.search(r'Descripci[óo]n[:\s]*([^.]{50,500}\.)', text)
    if desc_match:
        data["descripcion"] = desc_match.group(1).strip()
    else:
        # Fallback: buscar texto descriptivo después de "URBANA" o "RUSTICA"
        desc_match = re.search(r'(URBANA[:\.\s][^.]{20,400}\.)', text, re.IGNORECASE)
        if desc_match:
            data["descripcion"] = desc_match.group(1).strip()

    return data


def scrape_provincia(prov_code, prov_name, max_subastas=40):
    """Descarga subastas de una provincia."""
    print(f"  → {prov_name} ({prov_code})...", flush=True)
    listing_url = build_search_url(prov_code)
    try:
        html = fetch(listing_url)
    except Exception as e:
        print(f"    ✗ Error al cargar listado: {e}", flush=True)
        return []

    ids = parse_listing(html)
    print(f"    {len(ids)} subastas encontradas", flush=True)

    subastas = []
    for i, sid in enumerate(ids[:max_subastas]):
        try:
            detail_url = f"https://subastas.boe.es/detalleSubasta.php?idSub={sid}"
            detail_html = fetch(detail_url)
            data = parse_subasta(detail_html, sid)
            data["provincia"] = prov_name
            data["provincia_code"] = prov_code
            subastas.append(data)
            time.sleep(0.5)  # respetar el servidor
            if (i + 1) % 10 == 0:
                print(f"    procesadas {i+1}/{min(len(ids), max_subastas)}", flush=True)
        except Exception as e:
            print(f"    ✗ Error en {sid}: {e}", flush=True)
            continue

    return subastas


def main():
    print(f"Descargando subastas BOE para Euskadi...")
    print(f"Fecha: {datetime.now().isoformat()}")

    todas = []
    for code, name in PROVINCIAS.items():
        subs = scrape_provincia(code, name)
        todas.extend(subs)

    output = {
        "actualizado": datetime.now().isoformat(),
        "fecha_legible": datetime.now().strftime("%d de %B de %Y"),
        "total": len(todas),
        "fuente": "https://subastas.boe.es",
        "subastas": todas,
    }

    output_path = "docs/subastas.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Guardadas {len(todas)} subastas en {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR FATAL: {e}", file=sys.stderr)
        sys.exit(1)
