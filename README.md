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

### 5. 🪞 4-Way Collage
Toma **una sola imagen** y construye un **mosaico 2×2 en espejo** (original, volteo
horizontal, volteo vertical y ambos). Después divide ese mosaico en **secciones** que
se intercalan de afuera hacia adentro, generando un collage simétrico de aspecto
caleidoscópico. Es el port de los cuadernos `4waycollage` / `collage_mix` (y del
script `live_collage.py`), integrado desde el proyecto
[4way_collage](https://github.com/elivasquezhdz/4way_collage).

Hay dos secciones:
- **Collage:** ajusta el número de **secciones** (2–60). A mayor número, la simetría
  es más fina e intrincada. El resultado se renderiza a partir de un mosaico 2× y se
  escala de vuelta al tamaño original, así que no hay distorsión.
- **Collage Animación:** recorre el número de secciones desde un inicio hasta un fin
  con un incremento y reproduce el barrido como un bucle. Orden **forward**,
  **reverse** o **bounce** (ida y vuelta). Exporta a **GIF animado** (con
  [`gif.js`](docs/vendor/gif.js)) o a **vídeo** (`MediaRecorder`, prefiriendo MP4), y
  permite guardar el **cuadro visible como PNG** para navegadores sin grabación de
  canvas (p. ej. algunos iOS).

### 6. 🧛 Vampire
Port al navegador del script [`vampire_filter.py`](vampire_filter.py): un preset tipo
**Lightroom Mobile** («vampire») que aplica toda una cadena de revelado — exposición,
altas luces / sombras / blancos / negros, balance de blancos cálido, contraste, dehaze,
textura y claridad, curva de tonos, intensidad y saturación, mezcla de color
(rojo/naranja), reducción de ruido de color, **viñeta** y **grano** de película. Todo
corre localmente en el navegador; el port de JavaScript reproduce el resultado de Python
con una diferencia inapreciable (< 0,03 de un nivel 0–255).

Hay dos secciones:
- **Vampire Filter:** los controles vienen precargados con los valores del preset,
  agrupados en **Luz**, **Color**, **Efectos**, **Viñeta**, **Grano** y **General**
  (intensidad global 0–100 %). Interruptores para activar/desactivar **grano** y
  **viñeta**. Ajusta y pulsa **Apply** (también se re-aplica al soltar un deslizador).
  Las imágenes muy grandes se procesan hasta 2000 px en el lado largo para mantener el
  navegador ágil.
- **Vampire Animación:** anima **un parámetro** (Strength, Exposición, Temperatura,
  Saturación, Viñeta, Grano, etc.) desde un valor de **inicio** hasta uno de **fin** a lo
  largo de un número de **cuadros**, y lo reproduce a los **FPS** elegidos. El resto de
  controles conserva los valores del filtro, así que puedes, por ejemplo, revelar el
  efecto animando *Strength* de 0 → 100. Orden **forward**, **reverse** o **bounce**.
  Los cuadros se renderizan de uno en uno a tamaño reducido (lado largo ≤ 480 px, hasta
  60 cuadros); el grano usa una semilla fija para no parpadear. Exporta a **vídeo**
  (`MediaRecorder`, prefiriendo MP4) o guarda el **cuadro visible como PNG**.

### 7. 🎬 Slideshow
Selecciona **hasta 10 imágenes** y crea un **vídeo** con ellas: cada imagen es un cuadro
que se reproduce en el orden elegido a los **FPS** indicados. Todo corre localmente en el
navegador.

Parámetros:
- **Velocidad (FPS):** cuadros por segundo (1–30).
- **Ajuste (Fit):** *Contain* (encaja la imagen completa con bordes) o *Cover* (rellena el
  cuadro recortando). Los cuadros toman el tamaño de la primera imagen (limitado a 1280 px
  en el lado largo, con dimensiones pares para los codificadores).
- **Bucle «ida y vuelta» (bounce):** reproduce las imágenes hacia delante y luego hacia
  atrás para un ciclo continuo.

Exportación:
- **Vídeo:** graba la reproducción con `MediaRecorder`, prefiriendo **MP4** (H.264) por su
  compatibilidad al compartir; si el navegador no puede grabar MP4 usa WebM.
- **Cuadro (PNG):** guarda el fotograma visible (útil en navegadores sin soporte de
  grabación de canvas, p. ej. algunos iOS).

### 8. 🧍 Person / Background
Detecta a la **persona** en una foto con un modelo de segmentación que corre **en el
navegador** ([MediaPipe Selfie Segmentation](https://google.github.io/mediapipe/solutions/selfie_segmentation),
alojado localmente en `docs/vendor/selfie/`) y permite operar sobre la **persona** o sobre
el **fondo**. La imagen nunca se sube a ningún servidor.

Parámetros:
- **Operar sobre (Operate on):** `person` o `background`.
- **Operación:** por ahora **invertir colores** sobre la zona seleccionada (más adelante se
  podrán añadir otras operaciones).
- **Umbral de máscara (threshold):** cuánta parte de la máscara suave cuenta como «persona».
- **Ver máscara (Show mask):** previsualiza la región detectada (blanco = persona).

El modelo (~6 MB) se descarga solo la **primera vez** que se usa esta pestaña. Requiere un
navegador con **WebAssembly SIMD** (todos los navegadores actuales). Las imágenes grandes se
procesan hasta 1600 px en el lado largo.

## Script de Python: filtro vampire

`vampire_filter.py` aplica el preset «vampire» a una imagen o a una carpeta (lote).

```bash
python vampire_filter.py entrada.jpg -o salida.jpg
python vampire_filter.py entrada.jpg -o salida.jpg --strength 0.7
python vampire_filter.py carpeta/ -o salida/          # lote
```

Opciones: `--strength 0..1`, `--no-grain`, `--no-vignette`, `--seed`, `--quality`.
Requiere `numpy` y `pillow`.

## Script de Python: relleno combinado

`combined_fill.py` implementa la combinación de relleno horizontal + vertical
que faltaba en los cuadernos.

```bash
python combined_fill.py entrada.jpg salida.png \
    --h-direction right --h-percent 0.4 \
    --v-direction down  --v-percent 0.3
```

Requiere `opencv-python` (o `opencv-python-headless`) y `numpy`.

## Script de Python: collage en vivo (webcam)

`live_collage.py` aplica el efecto **4-Way Collage** en tiempo real a la cámara con
OpenCV (la misma lógica de mosaico + secciones que la web).

```bash
python live_collage.py   # pulsa 'q' o Esc para salir
```

Requiere `opencv-python` (o `opencv-python-headless`) y `numpy`.

## Estructura del proyecto

```
docs/index.html      → aplicación web (se publica en GitHub Pages)
docs/vendor/         → gif.js (GIF del collage) y selfie/ (MediaPipe Selfie
                       Segmentation, modelo de persona/fondo alojado localmente)
combined_fill.py     → script de relleno combinado horizontal + vertical
live_collage.py      → collage 4-way en vivo desde la webcam (OpenCV)
vampire_filter.py    → preset «vampire» tipo Lightroom (numpy + pillow)
*.ipynb              → cuadernos originales con los algoritmos
    4waycollage*.ipynb, collage_mix.ipynb → algoritmo del 4-Way Collage
.github/workflows/   → workflow que publica docs/ en GitHub Pages
```

## Desarrollo local

La web son archivos estáticos sin build ni dependencias externas (`docs/index.html`
más `docs/vendor/gif.js`). Puedes abrir `docs/index.html` directamente en el
navegador, o servirlo localmente:

```bash
cd docs && python3 -m http.server 8000
# abre http://localhost:8000
```

## Publicación (GitHub Pages)

El sitio se publica automáticamente con GitHub Actions cada vez que se hace push
a `main` (ver [`.github/workflows/pages.yml`](.github/workflows/pages.yml)).
