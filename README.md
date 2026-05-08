# Dashboard Subastas BOE Euskadi — Auto-actualizable

Dashboard que muestra subastas judiciales del BOE en Euskadi (Bizkaia, Gipuzkoa, Álava) y se **actualiza solo cada 3 días** sin servidor de pago.

## Cómo funciona

1. Un script de Python (`scrape_boe.py`) descarga las subastas reales del BOE.
2. **GitHub Actions** ejecuta el script automáticamente cada 3 días, gratis.
3. Los datos se guardan en `docs/subastas.json`.
4. **GitHub Pages** publica `docs/index.html` como página web pública gratuita.
5. Tú abres la URL en favoritos. Siempre con datos frescos.

**Coste total: 0 €. Mantenimiento: 0.**

---

## Instalación (4 pasos · 10 minutos · sin saber programar)

### Paso 1 — Crea cuenta en GitHub
- Ve a https://github.com/signup y crea una cuenta gratis.
- No necesitas saber programar. Es como Google Drive pero para código.

### Paso 2 — Crea un repositorio nuevo
- Pulsa el botón verde **"New"** (arriba a la izquierda).
- Nombre: `subastas-boe` (o el que quieras).
- Marca **Public**.
- Pulsa **Create repository**.

### Paso 3 — Sube los archivos
- En la página de tu nuevo repositorio, busca el enlace **"uploading an existing file"** (suele estar en el centro).
- Arrastra TODOS los archivos y carpetas de esta plantilla manteniendo la estructura:
  ```
  scrape_boe.py
  README.md
  .github/workflows/actualizar.yml
  docs/index.html
  docs/subastas.json
  ```
- Pulsa **Commit changes** abajo de la página.

> ⚠️ **Importante**: la carpeta `.github/workflows/` debe mantenerse exactamente igual (con el punto delante).

### Paso 4 — Activa GitHub Pages
- En tu repositorio, pulsa **Settings** (arriba a la derecha).
- En el menú izquierdo, pulsa **Pages**.
- En "Source", selecciona **Deploy from a branch**.
- En "Branch", selecciona **main** y la carpeta **/docs**.
- Pulsa **Save**.
- Espera 1-2 minutos. Aparecerá tu URL: `https://TU_USUARIO.github.io/subastas-boe/`

### Paso 5 (opcional) — Lanza la primera actualización
Para no esperar 3 días al primer scrape:
- Ve a la pestaña **Actions** de tu repositorio.
- Pulsa **Actualizar Subastas BOE** en el menú izquierdo.
- Pulsa el botón **Run workflow** → **Run workflow** (verde).
- Espera 3-5 minutos. Cuando termine, recarga tu URL.

---

## ¿Y ahora qué?

- Guarda la URL de tu dashboard en favoritos del navegador y del móvil.
- Cada 3 días, GitHub Actions lanzará el scraper y actualizará los datos solo.
- En la pestaña **Actions** del repo puedes ver el historial de actualizaciones.

## Cambiar la frecuencia o las provincias

Edita `.github/workflows/actualizar.yml` y cambia el cron:
- `'0 7 */3 * *'` → cada 3 días
- `'0 7 * * *'` → cada día
- `'0 7 * * 1'` → cada lunes

Edita `scrape_boe.py` y modifica el diccionario `PROVINCIAS` para añadir/quitar provincias (los códigos son INE de 2 dígitos).

## Solución de problemas

**El JSON está vacío y no salen subastas:**
Lanza manualmente el workflow desde la pestaña Actions (Paso 5).

**El workflow falla:**
El BOE ha cambiado el HTML. Pega aquí el error en el chat de Claude y lo arreglo.

**Los datos no se actualizan en la web pero sí en el JSON:**
GitHub Pages tarda 5-10 minutos en propagar cambios. Espera o fuerza una recarga (Ctrl+F5).

---

## Aviso legal

Datos extraídos del Portal de Subastas del BOE (fuente pública). Esta herramienta no constituye asesoramiento legal ni financiero. Verifica siempre la información en el portal oficial: https://subastas.boe.es/
