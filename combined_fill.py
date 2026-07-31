#!/usr/bin/env python3
"""
combined_fill.py
================

Relleno combinado horizontal + vertical.

En los cuadernos originales (``horizontal_fill*.ipynb``) el relleno se hace en
UNA sola direccion: se toma la columna (o fila) que esta en el borde del
porcentaje elegido y se replica hacia el borde de la imagen. La funcion de
COMBINAR las dos direcciones (horizontal Y vertical al mismo tiempo) nunca se
implemento; este script la agrega.

El resultado es un relleno "en esquina": primero se rellena en el eje
horizontal (left/right) y sobre ese resultado se rellena en el eje vertical
(up/down), produciendo un efecto de barrido en forma de L.

Uso:
    python combined_fill.py entrada.jpg salida.png \
        --h-direction right --h-percent 0.4 \
        --v-direction down  --v-percent 0.3

Tambien se puede importar la funcion ``combined_fill`` desde otro modulo.
"""

import argparse
import cv2
import numpy as np


def fill_with_edge_color(img, fill_percent=0.5, fill_direction="left"):
    """Rellena la imagen en una sola direccion replicando la columna/fila del borde.

    Es la misma logica de ``fill_with_edge_color`` de los cuadernos, pero opera
    sobre un arreglo de numpy en lugar de una ruta, para poder encadenarla.

    Parameters
    ----------
    img : numpy.ndarray
        Imagen BGR (se modifica una copia, no la original).
    fill_percent : float
        Porcentaje (0-1) donde inicia el relleno.
    fill_direction : str
        'left', 'right', 'up' o 'down'.
    """
    img = img.copy()
    height, width = img.shape[:2]
    fill_percent = max(0.0, min(1.0, fill_percent))  # clamp 0-1

    if fill_direction == "left":
        fill_width = int(width * fill_percent)
        source_col = min(fill_width, width - 1)
        column = img[:, source_col:source_col + 1]
        for col in range(fill_width):
            img[:, col:col + 1] = column

    elif fill_direction == "right":
        fill_width = int(width * fill_percent)
        source_col = max(width - fill_width - 1, 0)
        column = img[:, source_col:source_col + 1]
        for col in range(width - fill_width, width):
            img[:, col:col + 1] = column

    elif fill_direction == "up":
        fill_height = int(height * fill_percent)
        source_row = min(fill_height, height - 1)
        row = img[source_row:source_row + 1, :]
        for row_idx in range(fill_height):
            img[row_idx:row_idx + 1, :] = row

    elif fill_direction == "down":
        fill_height = int(height * fill_percent)
        source_row = max(height - fill_height - 1, 0)
        row = img[source_row:source_row + 1, :]
        for row_idx in range(height - fill_height, height):
            img[row_idx:row_idx + 1, :] = row

    else:
        raise ValueError("fill_direction debe ser: 'left', 'right', 'up' o 'down'.")

    return img


def combined_fill(image_path, h_direction="right", h_percent=0.4,
                  v_direction="down", v_percent=0.3):
    """Aplica relleno horizontal y vertical sobre la misma imagen.

    Primero rellena en el eje horizontal (``h_direction`` debe ser 'left' o
    'right') y luego, sobre ese resultado, rellena en el eje vertical
    (``v_direction`` debe ser 'up' o 'down').

    Parameters
    ----------
    image_path : str
        Ruta a la imagen de entrada.
    h_direction : str
        Direccion horizontal: 'left' o 'right'.
    h_percent : float
        Porcentaje (0-1) de inicio del relleno horizontal.
    v_direction : str
        Direccion vertical: 'up' o 'down'.
    v_percent : float
        Porcentaje (0-1) de inicio del relleno vertical.

    Returns
    -------
    numpy.ndarray
        Imagen BGR resultante.
    """
    if h_direction not in ("left", "right"):
        raise ValueError("h_direction debe ser 'left' o 'right'.")
    if v_direction not in ("up", "down"):
        raise ValueError("v_direction debe ser 'up' o 'down'.")

    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    # descartar canal alfa si existe
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, 0:3]

    img = fill_with_edge_color(img, h_percent, h_direction)
    img = fill_with_edge_color(img, v_percent, v_direction)
    return img


def _parse_args():
    p = argparse.ArgumentParser(description="Relleno combinado horizontal + vertical.")
    p.add_argument("input", help="Imagen de entrada")
    p.add_argument("output", help="Imagen de salida")
    p.add_argument("--h-direction", default="right", choices=["left", "right"],
                   help="Direccion horizontal (default: right)")
    p.add_argument("--h-percent", type=float, default=0.4,
                   help="Porcentaje 0-1 de inicio horizontal (default: 0.4)")
    p.add_argument("--v-direction", default="down", choices=["up", "down"],
                   help="Direccion vertical (default: down)")
    p.add_argument("--v-percent", type=float, default=0.3,
                   help="Porcentaje 0-1 de inicio vertical (default: 0.3)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = combined_fill(args.input, args.h_direction, args.h_percent,
                           args.v_direction, args.v_percent)
    cv2.imwrite(args.output, result)
    print(f"Guardado: {args.output}")
