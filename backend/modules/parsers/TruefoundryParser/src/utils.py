import base64
import io
from collections import OrderedDict

import cv2
import numpy as np
from PIL import Image


class OrderedSet:
    def __init__(self):
        self._ordered_dict = OrderedDict()

    def add(self, item):
        self._ordered_dict[item] = None

    def __iter__(self):
        return iter(self._ordered_dict.keys())


def stringToRGB(base64_string: str):
    imgdata = base64.b64decode(str(base64_string))
    img = Image.open(io.BytesIO(imgdata))
    opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
    return opencv_img


def arrayToBase64(image_arr: np.ndarray):
    image = Image.fromarray(image_arr)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    encoded = base64.b64encode(img_bytes)
    base64_str = encoded.decode("utf-8")
    return base64_str
