import cv2
import numpy as np


class Detected:
    def __init__(self, center, box, area):
        self.center = center
        self.box = box
        self.area = area
    def __repr__(self):
        return f"box: {self.box}; center : {self.center}"


def get_default_hue_range(hue):
    if 50 <= hue <= 70:
        return 25
    if 110 <= hue <= 130:
        return 15
    return 10


def make_hsv_mask(img_hsv, hue, hue_range=None, min_s=150, min_v=60):
    hue = int(hue)
    if hue_range is None:
        hue_range = get_default_hue_range(hue)

    lower_h = hue - hue_range
    upper_h = hue + hue_range

    if lower_h < 0:
        mask1 = cv2.inRange(img_hsv, (0, min_s, min_v), (upper_h, 255, 255))
        mask2 = cv2.inRange(img_hsv, (180 + lower_h, min_s, min_v), (179, 255, 255))
        return cv2.bitwise_or(mask1, mask2)

    if upper_h > 179:
        mask1 = cv2.inRange(img_hsv, (lower_h, min_s, min_v), (179, 255, 255))
        mask2 = cv2.inRange(img_hsv, (0, min_s, min_v), (upper_h - 180, 255, 255))
        return cv2.bitwise_or(mask1, mask2)

    return cv2.inRange(
        img_hsv,
        (lower_h, min_s, min_v),
        (upper_h, 255, 255)
    )


def apply_blur(img, blur_level):
    blur_level = int(blur_level)
    if blur_level <= 0:
        return img

    kernel_size = blur_level * 2 + 1
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)


def clean_mask(mask, morphology_level):
    morphology_level = int(morphology_level)
    if morphology_level <= 0:
        return mask

    kernel_size = morphology_level * 2 + 1
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask

def make_hsv_mask_for_black(img_hsv):
    mask = cv2.inRange(img_hsv, (0, 0, 0), (179, 255, 60))
    return mask


def make_hsv_mask_for_white(img_hsv):
    mask = cv2.inRange(img_hsv, (0, 0, 200), (179, 50, 255))
    return mask

#target_color задаємо в BGR (одновимірним лістом з трьох елементів)
#функція повертає список з об'єктів Detected 
def detect(
    image_path,
    target_color,
    hue_range=None,
    min_s=150,
    min_v=60,
    min_area=120,
    blur_level=1,
    morphology_level=1,
):
    target_color = np.uint8([[target_color]])
    target_color = cv2.cvtColor(target_color, cv2.COLOR_BGR2HSV)

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    img = apply_blur(img, blur_level)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # ----Маскування та очищення від шуму----
    hue = target_color[0][0][0]
    saturation = target_color[0][0][1]
    value = target_color[0][0][2]

    if value < 60:
        mask = make_hsv_mask_for_black(img_hsv)
    elif saturation < 30 and value > 200:
        mask = make_hsv_mask_for_white(img_hsv)
    else:
        mask = make_hsv_mask(img_hsv, hue, hue_range, min_s, min_v)
    mask = clean_mask(mask, morphology_level)

    # ----Знаходження контурів----
    cnt = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    detected_ones = []


    for contour in cnt:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        m = cv2.moments(contour)
        if m["m00"] == 0:
            continue

        center = (int(m['m10']/m["m00"]), int(m['m01']/m["m00"]))
        x, y, w, h = cv2.boundingRect(contour)
        box = (x, y, w, h)

        detected_ones.append(Detected(center, box, area))

    return detected_ones

