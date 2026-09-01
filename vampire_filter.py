#!/usr/bin/env python3
"""
vampire_filter.py
=================

Aplica un preset tipo Lightroom Mobile ("vampire") a una imagen.

Ajustes replicados desde las capturas:

  Básicos      Exposición -0.79 | Contraste +53 | Altas luces -100
               Sombras -27 | Blancos -100 | Negros -55
  Color        Temp +100 | Matiz -10 | Intensidad +24 | Saturación +100
  Efectos      Textura -10 | Claridad +15 | Neblina +10
  Viñeta       -45 | Punto medio 64 | Redondez +15
  Grano        48 | Tamaño 34 | Aspereza 46
  Ruido color  Reducción 21 | Detalle 50 | Suavizado 50
  Curva        (0,0) (74,85) (184,135) (255,230)
  Color grade  Medios naranja | Altas luces rojo | Global rojo

Uso:
    python vampire_filter.py entrada.jpg -o salida.jpg
    python vampire_filter.py entrada.jpg -o salida.jpg --strength 0.7
    python vampire_filter.py carpeta/ -o salida/          # lote

Requisitos: numpy, pillow
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

# ----------------------------------------------------------------------------
# Parámetros del preset (escala de Lightroom, editable)
# ----------------------------------------------------------------------------


@dataclass
class VampirePreset:
    # --- Luz ---
    exposure: float = -0.79      # pasos (stops)
    contrast: float = 53.0       # -100..100
    highlights: float = -100.0
    shadows: float = -27.0
    whites: float = -100.0
    blacks: float = -55.0

    # --- Color ---
    temp: float = 100.0          # -100..100 (+ = cálido)
    tint: float = -10.0          # -100..100 (+ = magenta)
    vibrance: float = 24.0
    saturation: float = 100.0

    # --- Efectos ---
    texture: float = -10.0
    clarity: float = 15.0
    dehaze: float = 10.0

    # --- Viñeta ---
    vignette: float = -45.0
    vignette_midpoint: float = 64.0
    vignette_roundness: float = 15.0
    vignette_feather: float = 50.0

    # --- Grano ---
    grain: float = 48.0
    grain_size: float = 34.0
    grain_roughness: float = 46.0

    # --- Reducción de ruido de color ---
    color_noise: float = 21.0
    color_noise_detail: float = 50.0
    color_noise_smooth: float = 50.0

    # --- Curva de tonos: puntos (entrada, salida) en 0..255 ---
    curve: list = field(default_factory=lambda: [
        (0, 0), (74, 85), (184, 135), (255, 230)
    ])

    # --- Mezcla de color: (tono_grados, saturación 0..100, luminancia -100..100)
    grade_shadows: tuple = (0.0, 0.0, 0.0)
    grade_midtones: tuple = (35.0, 80.0, 0.0)    # naranja
    grade_highlights: tuple = (8.0, 85.0, 0.0)   # rojo
    grade_global: tuple = (5.0, 85.0, 0.0)       # rojo
    grade_blending: float = 50.0                 # 0..100


LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------


def luminance(img: np.ndarray) -> np.ndarray:
    return img @ LUMA


def _box_blur(a: np.ndarray, r: int) -> np.ndarray:
    """Desenfoque de caja separable con sumas acumuladas (O(1) por píxel)."""
    if r < 1:
        return a
    for axis in (0, 1):
        a = np.moveaxis(a, axis, 0)
        pad = np.pad(a, [(r + 1, r)] + [(0, 0)] * (a.ndim - 1), mode="edge")
        cs = np.cumsum(pad, axis=0, dtype=np.float32)
        a = (cs[2 * r + 1:] - cs[:-(2 * r + 1)]) / (2 * r + 1)
        a = np.moveaxis(a, 0, axis)
    return a


def gaussian_blur(a: np.ndarray, radius: float) -> np.ndarray:
    """Gaussiana aproximada con tres cajas sucesivas."""
    if radius <= 0.5:
        return a.copy()
    r = max(1, int(round(radius / 3.0)))
    out = a.astype(np.float32, copy=True)
    for _ in range(3):
        out = _box_blur(out, r)
    return out


def smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def hsl_to_rgb(h_deg: float, s: float, l: float) -> np.ndarray:
    """h en grados, s y l en 0..1."""
    h = (h_deg % 360.0) / 60.0
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs(h % 2.0 - 1.0))
    m = l - c / 2.0
    table = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)]
    r, g, b = table[int(h) % 6]
    return np.array([r + m, g + m, b + m], dtype=np.float32)


def monotone_curve_lut(points, size: int = 1024) -> np.ndarray:
    """LUT desde puntos de control con interpolación cúbica monótona (PCHIP)."""
    pts = sorted(points)
    x = np.array([p[0] for p in pts], dtype=np.float64) / 255.0
    y = np.array([p[1] for p in pts], dtype=np.float64) / 255.0

    n = len(x)
    h = np.diff(x)
    delta = np.diff(y) / h
    m = np.zeros(n)
    m[1:-1] = (delta[:-1] + delta[1:]) / 2.0
    m[0], m[-1] = delta[0], delta[-1]

    # Filtro de Fritsch–Carlson para conservar la monotonía
    for i in range(n - 1):
        if delta[i] == 0:
            m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / delta[i], m[i + 1] / delta[i]
            t = a * a + b * b
            if t > 9.0:
                s = 3.0 / np.sqrt(t)
                m[i], m[i + 1] = s * a * delta[i], s * b * delta[i]

    xs = np.linspace(0.0, 1.0, size)
    idx = np.clip(np.searchsorted(x, xs) - 1, 0, n - 2)
    dx = x[idx + 1] - x[idx]
    t = (xs - x[idx]) / dx
    t2, t3 = t * t, t * t * t
    lut = ((2 * t3 - 3 * t2 + 1) * y[idx]
           + (t3 - 2 * t2 + t) * dx * m[idx]
           + (-2 * t3 + 3 * t2) * y[idx + 1]
           + (t3 - t2) * dx * m[idx + 1])
    return np.clip(lut, 0.0, 1.0).astype(np.float32)


def apply_lut(img: np.ndarray, lut: np.ndarray) -> np.ndarray:
    x = np.clip(img, 0.0, 1.0) * (len(lut) - 1)
    i0 = np.floor(x).astype(np.int32)
    i1 = np.minimum(i0 + 1, len(lut) - 1)
    f = (x - i0).astype(np.float32)
    return lut[i0] * (1.0 - f) + lut[i1] * f


# ----------------------------------------------------------------------------
# Etapas del filtro
# ----------------------------------------------------------------------------


def apply_exposure(img, ev):
    return img * (2.0 ** ev)


def apply_contrast(img, amount):
    if amount == 0:
        return img
    a = amount / 100.0
    factor = 1.0 + 0.6 * a if a > 0 else 1.0 + 0.9 * a
    return (img - 0.5) * factor + 0.5


def apply_tone_regions(img, highlights, shadows, whites, blacks):
    """Altas luces / sombras / blancos / negros con máscaras de luminancia."""
    L = luminance(img)[..., None]

    m_high = smoothstep((L - 0.45) / 0.55)
    m_shad = smoothstep((0.55 - L) / 0.55)
    m_white = smoothstep((L - 0.65) / 0.35)
    m_black = smoothstep((0.35 - L) / 0.35)

    out = img.copy()
    out += m_high * (highlights / 100.0) * 0.45
    out += m_shad * (shadows / 100.0) * 0.35
    out += m_white * (whites / 100.0) * 0.30
    out += m_black * (blacks / 100.0) * 0.25
    return out


def apply_white_balance(img, temp, tint):
    t = temp / 100.0
    g = tint / 100.0
    gains = np.array([
        1.0 + 0.22 * t,          # rojo   (temp +)
        1.0 - 0.16 * g,          # verde  (tint - => más verde)
        1.0 - 0.22 * t,          # azul   (temp -)
    ], dtype=np.float32)
    out = img * gains
    # Renormaliza para no perder brillo global
    return out * (luminance(img).mean() / max(luminance(out).mean(), 1e-6))


def apply_vibrance_saturation(img, vibrance, sat):
    L = luminance(img)[..., None]
    chroma = img - L
    mx = np.max(img, axis=-1, keepdims=True)
    mn = np.min(img, axis=-1, keepdims=True)
    cur_sat = np.clip(mx - mn, 0.0, 1.0)

    factor = np.ones_like(L)
    if vibrance != 0:
        v = vibrance / 100.0
        factor = factor + v * 0.9 * (1.0 - cur_sat) ** 2
    if sat != 0:
        s = sat / 100.0
        factor = factor * (1.0 + 0.85 * s)
    return L + chroma * factor


def apply_local_contrast(img, texture, clarity, w, h):
    """Textura (radio corto) y claridad (radio medio) sobre la luminancia."""
    if texture == 0 and clarity == 0:
        return img
    base = max(w, h) / 1000.0
    L = luminance(img)
    out = img.copy()

    if texture != 0:
        blur = gaussian_blur(L, max(1.5, 2.5 * base))
        out = out + ((L - blur) * (texture / 100.0) * 1.2)[..., None]

    if clarity != 0:
        blur = gaussian_blur(L, max(6.0, 30.0 * base))
        detail = L - blur
        # Protege luces y sombras extremas
        mask = 1.0 - np.abs(2.0 * np.clip(L, 0, 1) - 1.0) ** 2
        out = out + (detail * mask * (clarity / 100.0) * 1.5)[..., None]

    return out


def apply_dehaze(img, amount):
    if amount == 0:
        return img
    a = amount / 100.0
    dark = np.min(img, axis=-1, keepdims=True)
    veil = np.percentile(dark, 5).astype(np.float32)
    out = (img - a * veil) / max(1.0 - a * veil, 1e-3)
    L = luminance(out)[..., None]
    return L + (out - L) * (1.0 + 0.3 * a)


def apply_color_grading(img, preset: VampirePreset):
    L = np.clip(luminance(img), 0.0, 1.0)[..., None]
    blend = preset.grade_blending / 100.0

    masks = {
        "shadows": smoothstep((0.5 - L) / 0.5) ** 1.5,
        "midtones": 1.0 - np.abs(2.0 * L - 1.0) ** 1.5,
        "highlights": smoothstep((L - 0.5) / 0.5) ** 1.5,
        "global": np.ones_like(L),
    }
    zones = {
        "shadows": preset.grade_shadows,
        "midtones": preset.grade_midtones,
        "highlights": preset.grade_highlights,
        "global": preset.grade_global,
    }

    out = img.copy()
    for name, (hue, sat, lum) in zones.items():
        if sat == 0 and lum == 0:
            continue
        color = hsl_to_rgb(hue, 1.0, 0.5)
        tint = (color - color.mean()) * (sat / 100.0) * 0.28 * blend
        weight = masks[name] * (0.6 if name == "global" else 1.0)
        out = out + weight * tint
        if lum != 0:
            out = out + weight * (lum / 100.0) * 0.2
    return out


def apply_vignette(img, preset: VampirePreset):
    if preset.vignette == 0:
        return img
    h, w = img.shape[:2]
    yy = (np.linspace(-1.0, 1.0, h, dtype=np.float32))[:, None]
    xx = (np.linspace(-1.0, 1.0, w, dtype=np.float32))[None, :]

    # Redondez: 0 = elipse ajustada al encuadre, +100 = círculo
    r = preset.vignette_roundness / 100.0
    ar = w / h
    sx = 1.0 / (1.0 + r * (ar - 1.0)) if ar >= 1 else 1.0
    sy = 1.0 / (1.0 + r * (1.0 / ar - 1.0)) if ar < 1 else 1.0
    d = np.sqrt((xx * sx) ** 2 + (yy * sy) ** 2)

    mid = np.clip(preset.vignette_midpoint / 100.0, 0.05, 1.0)
    feather = max(preset.vignette_feather / 100.0, 0.05)
    t = smoothstep((d - mid) / feather)

    amount = preset.vignette / 100.0
    if amount < 0:
        factor = 1.0 + amount * t
    else:
        factor = 1.0 + amount * t * 0.8
    return img * factor[..., None]


def apply_grain(img, preset: VampirePreset, seed=None):
    if preset.grain <= 0:
        return img
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed)

    # Tamaño: genera el ruido en menor resolución y lo escala
    size = 1.0 + (preset.grain_size / 100.0) * 4.0
    nh, nw = max(2, int(h / size)), max(2, int(w / size))
    noise = rng.standard_normal((nh, nw), dtype=np.float32)
    noise = np.asarray(
        Image.fromarray(noise, mode="F").resize((w, h), Image.BILINEAR),
        dtype=np.float32,
    )

    # Aspereza: modula la amplitud con ruido de baja frecuencia
    rough = preset.grain_roughness / 100.0
    if rough > 0:
        low = rng.standard_normal((max(2, nh // 6), max(2, nw // 6))).astype(np.float32)
        low = np.asarray(
            Image.fromarray(low, mode="F").resize((w, h), Image.BILINEAR),
            dtype=np.float32,
        )
        noise = noise * (1.0 + rough * 0.8 * low)

    amount = (preset.grain / 100.0) * 0.12
    L = np.clip(luminance(img), 0.0, 1.0)
    falloff = (1.0 - np.abs(2.0 * L - 1.0)) ** 0.5      # más grano en medios tonos
    return img + (noise * amount * falloff)[..., None]


def apply_color_noise_reduction(img, preset: VampirePreset):
    if preset.color_noise <= 0:
        return img
    L = luminance(img)[..., None]
    chroma = img - L
    radius = 1.0 + (preset.color_noise / 100.0) * 6.0
    radius *= 0.5 + preset.color_noise_smooth / 100.0
    blurred = np.stack(
        [gaussian_blur(chroma[..., c], radius) for c in range(3)], axis=-1
    )
    # Detalle: conserva parte de la crominancia original en los bordes
    keep = (preset.color_noise_detail / 100.0) * 0.3
    return L + blurred * (1.0 - keep) + chroma * keep


# ----------------------------------------------------------------------------
# Cadena completa
# ----------------------------------------------------------------------------


def process(img: np.ndarray, preset: VampirePreset, strength: float = 1.0,
            seed=None) -> np.ndarray:
    original = img.copy()
    h, w = img.shape[:2]

    out = apply_exposure(img, preset.exposure)
    out = apply_tone_regions(out, preset.highlights, preset.shadows,
                             preset.whites, preset.blacks)
    out = apply_contrast(out, preset.contrast)
    out = np.clip(out, 0.0, 1.0)

    out = apply_white_balance(out, preset.temp, preset.tint)
    out = np.clip(out, 0.0, 1.0)

    out = apply_dehaze(out, preset.dehaze)
    out = apply_local_contrast(out, preset.texture, preset.clarity, w, h)
    out = np.clip(out, 0.0, 1.0)

    out = apply_lut(out, monotone_curve_lut(preset.curve))

    out = apply_vibrance_saturation(out, preset.vibrance, preset.saturation)
    out = np.clip(out, 0.0, 1.0)

    out = apply_color_grading(out, preset)
    out = np.clip(out, 0.0, 1.0)

    out = apply_color_noise_reduction(out, preset)
    out = apply_vignette(out, preset)
    out = apply_grain(out, preset, seed=seed)

    out = np.clip(out, 0.0, 1.0)

    if strength < 1.0:
        out = original * (1.0 - strength) + out * strength
    return np.clip(out, 0.0, 1.0)


def load_image(path: str) -> tuple[np.ndarray, np.ndarray | None]:
    im = Image.open(path)
    im = Image.merge("RGB", im.convert("RGBA").split()[:3]) if im.mode in ("P", "LA") else im
    alpha = None
    if im.mode == "RGBA":
        alpha = np.asarray(im.split()[-1], dtype=np.float32) / 255.0
    arr = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    return arr, alpha


def save_image(arr: np.ndarray, path: str, alpha=None, quality: int = 95) -> None:
    data = (np.clip(arr, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    im = Image.fromarray(data, mode="RGB")
    if alpha is not None and path.lower().endswith(".png"):
        a = Image.fromarray((alpha * 255).astype(np.uint8), mode="L")
        im = im.convert("RGBA")
        im.putalpha(a)
    if path.lower().endswith((".jpg", ".jpeg")):
        im.save(path, quality=quality, subsampling=0)
    else:
        im.save(path)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Aplica el filtro 'vampire' (preset tipo Lightroom) a una imagen."
    )
    p.add_argument("input", help="Imagen de entrada o carpeta")
    p.add_argument("-o", "--output", default=None,
                   help="Archivo o carpeta de salida (por defecto: *_vampire.jpg)")
    p.add_argument("--strength", type=float, default=1.0,
                   help="Intensidad global del preset 0..1 (por defecto 1.0)")
    p.add_argument("--no-grain", action="store_true", help="Desactiva el grano")
    p.add_argument("--no-vignette", action="store_true", help="Desactiva la viñeta")
    p.add_argument("--seed", type=int, default=None, help="Semilla del grano")
    p.add_argument("--quality", type=int, default=95, help="Calidad JPEG")
    return p


def collect_files(path: str) -> list[str]:
    exts = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
    if os.path.isdir(path):
        return sorted(os.path.join(path, f) for f in os.listdir(path)
                      if f.lower().endswith(exts))
    return [path]


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    preset = VampirePreset()
    if args.no_grain:
        preset.grain = 0.0
    if args.no_vignette:
        preset.vignette = 0.0

    files = collect_files(args.input)
    if not files:
        print("No se encontraron imágenes.", file=sys.stderr)
        return 1

    batch = os.path.isdir(args.input)
    if batch and args.output:
        os.makedirs(args.output, exist_ok=True)

    for src in files:
        if batch:
            dst = os.path.join(args.output or ".", os.path.basename(src))
        elif args.output:
            dst = args.output
        else:
            root, ext = os.path.splitext(src)
            dst = f"{root}_vampire{ext or '.jpg'}"

        arr, alpha = load_image(src)
        result = process(arr, preset, strength=args.strength, seed=args.seed)
        save_image(result, dst, alpha=alpha, quality=args.quality)
        print(f"✓ {src} → {dst}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
