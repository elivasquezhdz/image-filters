import cv2
import numpy as np


def img_sect(img, sections, orientation="h"):
    """
    Divide an image into equal sections using NumPy slicing.
    """
    h, w, _ = img.shape
    slices = []

    if orientation.lower() == 'v':
        section_w = w // sections
        for i in range(sections):
            x1 = i * section_w
            x2 = w if i == sections - 1 else (i + 1) * section_w
            slices.append(img[:, x1:x2])

    elif orientation.lower() == 'h':
        section_h = h // sections
        for i in range(sections):
            y1 = i * section_h
            y2 = h if i == sections - 1 else (i + 1) * section_h
            slices.append(img[y1:y2, :])

    else:
        raise ValueError("Orientation must be 'h' or 'v'")

    return slices


def create_collage(frame, sections=20):
    # Flips
    h_flip = cv2.flip(frame, 1)     # horizontal
    v_flip = cv2.flip(frame, 0)     # vertical
    hv_flip = cv2.flip(frame, -1)   # both

    # 2x2 mosaic
    top = np.hstack([frame, h_flip])
    bottom = np.hstack([v_flip, hv_flip])
    mosaic = np.vstack([top, bottom])

    # --- Vertical slicing & reorder ---
    slices_v = img_sect(mosaic, sections, 'v')
    vc = np.zeros_like(mosaic)

    sw = slices_v[0].shape[1]
    for i in range(sections // 2):
        a = slices_v[i]
        b = slices_v[-(i + 1)]
        vc[:, (i * 2) * sw:(i * 2 + 1) * sw] = a
        vc[:, (i * 2 + 1) * sw:(i * 2 + 2) * sw] = b

    # --- Horizontal slicing & reorder ---
    slices_h = img_sect(vc, sections, 'h')
    vc2 = np.zeros_like(vc)

    sh = slices_h[0].shape[0]
    for i in range(sections // 2):
        a = slices_h[i]
        b = slices_h[-(i + 1)]
        vc2[(i * 2) * sh:(i * 2 + 1) * sh, :] = a
        vc2[(i * 2 + 1) * sh:(i * 2 + 2) * sh, :] = b

    return vc2


def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera not available")
        return

    sections = 20

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize for performance (optional)
        frame = cv2.resize(frame, (320, 240))

        collage = create_collage(frame, sections)

        cv2.imshow("OpenCV Collage", collage)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
