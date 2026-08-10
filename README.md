# image-filters

Colección de algoritmos de manipulación de imágenes desarrollados originalmente
en cuadernos de Jupyter y transcritos a una aplicación **web (HTML + JavaScript)**
que corre completamente en el navegador — las imágenes nunca se suben a ningún
servidor.

🌐 **Página en vivo:** https://elivasquezhdz.github.io/image-filters/

## Filtros incluidos en la web

Todos los filtros permiten **descargar** la imagen modificada.

### 1. 🧩 Boxes
Acepta **de 2 a 5 imágenes** y las combina en una sola. Divide cada imagen en
una rejilla `N×N` y toma una sección de píxeles de cada imagen, intercalando las
celdas cíclicamente entre todas las imágenes.

Hay dos secciones:
- **Por divisiones (N×N):** la rejilla se define por el número de divisiones.
  - **Divisiones de la rejilla (N):** cuántas filas/columnas de celdas (2–40).
- **Por tamaño de bloque:** se elige el tamaño de los bloques de forma independiente en
  horizontal y vertical, en **píxeles o porcentaje**.

Parámetros comunes:
- **Orden:** normal o invertido.
- **Ajuste de tamaño:** al tamaño de la primera imagen o al mínimo común.

### 2. 🎞️ Boxes Animación
Anima el filtro **Boxes** recorriendo el número de divisiones `N` de la rejilla
desde un mínimo hasta un máximo. Cada valor de `N` genera un cuadro y, al
reproducirlos en secuencia, el mosaico se afina (o se engruesa) progresivamente
mientras intercala las imágenes. Lleva al navegador la idea de los cuadernos
`boxes-frames` / `boxes-frames-multiple`.

Parámetros:
- **N mínimo / N máximo / Paso:** el rango de divisiones que se recorre.
- **Velocidad (FPS):** cuadros por segundo de la reproducción.
- **Orden** y **Ajuste de tamaño:** igual que en Boxes.
- **Bucle «ida y vuelta» (ping-pong):** reproduce la secuencia hacia delante y
  luego hacia atrás para un ciclo continuo.

Exportación:
- **Vídeo:** graba un ciclo completo de la animación con `MediaRecorder`,
  prefiriendo **MP4** (H.264) por su compatibilidad al compartir (WhatsApp,
  Fotos de iOS, redes). Si el navegador no puede grabar MP4 (p. ej. Firefox)
  se descarga en WebM.
- **Cuadro (PNG):** guarda el fotograma visible (útil en navegadores sin
  soporte de grabación de canvas, p. ej. algunos iOS).

Para no agotar la memoria del navegador, el número de cuadros y el tamaño de la
animación se limitan automáticamente.

### 3. 🪣 Horizontal / Vertical Fill
Selecciona una imagen y, a partir de un **porcentaje de inicio** y una
**dirección**, replica la fila o columna de ese borde para rellenar el resto de
la imagen.

Parámetros:
- **Dirección:** `left`, `right`, `up`, `down`.
- **Inicio del relleno:** porcentaje (0–100 %).
- **Modo diagonal (nuevo):** rellena a lo largo de una recta diagonal definida por un
  punto de inicio en **X (%)**, en **Y (%)** y una **pendiente**. Los píxeles de esa
  recta se replican sobre el semiplano del lado de relleno, generando franjas diagonales.
- **Modo combinado (nuevo):** aplica relleno horizontal **y** vertical al mismo
  tiempo, produciendo un relleno en forma de esquina. Esta combinación no existía
  en los cuadernos originales y se implementó tanto en la web como en un nuevo
  script de Python (ver [`combined_fill.py`](combined_fill.py)).

### 4. 🌈 Chroma Shift
Toma una imagen y desplaza **2 canales de color** en una dirección, produciendo
un efecto de aberración cromática / glitch RGB.

Parámetros:
- **Canal A** y **Canal B:** los dos canales (R/G/B) a desplazar.
- **Eje:** horizontal o vertical.
- **Desplazamiento:** porcentaje del ancho de la imagen.
- **Sentido:** opuestos (uno hacia cada lado) o el mismo.

## Script de Python: relleno combinado

`combined_fill.py` implementa la combinación de relleno horizontal + vertical
que faltaba en los cuadernos.

```bash
python combined_fill.py entrada.jpg salida.png \
    --h-direction right --h-percent 0.4 \
    --v-direction down  --v-percent 0.3
```

Requiere `opencv-python` (o `opencv-python-headless`) y `numpy`.

## Estructura del proyecto

```
docs/index.html      → aplicación web (se publica en GitHub Pages)
combined_fill.py     → script de relleno combinado horizontal + vertical
*.ipynb              → cuadernos originales con los algoritmos
.github/workflows/   → workflow que publica docs/ en GitHub Pages
```

## Desarrollo local

La web es un único archivo estático sin dependencias. Puedes abrir
`docs/index.html` directamente en el navegador, o servirlo localmente:

```bash
cd docs && python3 -m http.server 8000
# abre http://localhost:8000
```

## Publicación (GitHub Pages)

El sitio se publica automáticamente con GitHub Actions cada vez que se hace push
a `main` (ver [`.github/workflows/pages.yml`](.github/workflows/pages.yml)).
