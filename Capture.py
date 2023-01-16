"""
Alternative screen capture device, when there is no camera of webcam connected
to the desktop.
"""

import logging
import sys
import time
import cv2
import numpy as np
# import pygame
from VK import VK_CODE

if sys.platform == 'win32':
    import win32gui, win32ui, win32con, win32api
else:
    logging.warning("Screen capture is not supported on platform: {}".format(sys.platform))

from collections import namedtuple

# via https://stackoverflow.com/questions/66384468/how-to-record-my-computer-screen-with-high-fps
class ScreenCapture:
    """
        Captures a fixed  region of the total screen. If no region is given
        it will take the full screen size.
        region_ltrb: Tuple[int, int, int, int]
            Specific region that has to be taken from the screen using
            the top left `x` and `y`,  bottom right `x` and `y` (ltrb coordinates).
    """
    __region = namedtuple('region', ('x', 'y', 'width', 'height'))

    def __init__(self, region_ltrb=None):
        self.region = region_ltrb
        self.hwin = win32gui.GetDesktopWindow()

        # Time management
        self._time_start = time.time()
        self._time_taken = 0
        self._time_average = 0.04

    def __getitem__(self, item):
        return self.screenshot()

    def __next__(self):
        return self.screenshot()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_type and isinstance(exc_val, StopIteration):
            return True
        return False

    @staticmethod
    def screen_dimensions():
        """ Retrieve total screen dimensions.  """
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        return left, top, height, width

    @property
    def fps(self):
        return int(1 / self._time_average) * (self._time_average > 0)

    @property
    def region(self):
        return self._region

    @property
    def size(self):
        return self._region.width, self._region.height

    @region.setter
    def region(self, value):
        if value is None:
            self._region = self.__region(*self.screen_dimensions())
        else:
            assert len(value) == 4, f"Region requires 4 input, x, y of left top, and x, y of right bottom."
            left, top, x2, y2 = value
            width = x2 - left
            height = y2 - top
            self._region = self.__region(*list(map(int, (left, top, width, height))))

    def screenshot(self, color=None):
        """
            Takes a  part of the screen, defined by the region.
            :param color: cv2.COLOR_....2...
                Converts the created BGRA image to the requested image output.
            :return: np.ndarray
                An image of the region in BGRA values.
        """
        left, top, width, height = self._region
        hwindc = win32gui.GetWindowDC(self.hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)

        signed_ints_array = bmp.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype='uint8')
        img.shape = (height, width, 4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(self.hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        # This makes sure that the FPS are taken in comparison to screenshots rates and vary only slightly.
        self._time_taken, self._time_start = time.time() - self._time_start, time.time()
        self._time_average = self._time_average * 0.95 + self._time_taken * 0.05

        if color is not None:
            return cv2.cvtColor(img, color)
        return img[:,:,:3]

    def show(self, screenshot=None):
        """ Displays an image to the screen. """
        image = screenshot if screenshot is not None else self.screenshot()
        cv2.imshow('Screenshot', image)

        if cv2.waitKey(1) & 0xff == ord('q'):
            raise StopIteration
        return image

    def close(self):
        """ Needs to be called before exiting when `show` is used, otherwise an error will occur.  """
        cv2.destroyWindow('Screenshot')

    def scale(self, src: np.ndarray, size: tuple):
        return cv2.resize(src, size, interpolation=cv2.INTER_LINEAR_EXACT)

    def save(self, path, screenshot=None):
        """ Store the current screenshot in the provided path. Full path, with img name is required.) """
        image = screenshot if screenshot is not None else self.screenshot()
        cv2.imwrite(filename=path, img=image)


class KeyCapture:

    def __init__(self, retval='key'):
        self.VK_CODE = VK_CODE
        self.retval = retval

    def __getitem__(self, item):
        return self.keyshot()

    def __next__(self):
        return self.keyshot()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_type and isinstance(exc_val, StopIteration):
            return True
        return False

    def keyshot(self):
        
        keys_list = []

        for key in self.VK_CODE:
            if win32api.GetAsyncKeyState(self.VK_CODE[key]):
                if self.retval == 'key':
                    keys_list.append(key)
                elif self.retval == 'hex':
                    keys_list.append(self.VK_CODE[key])
        return keys_list

    def mouseshot(self):
        return win32api.GetCursorPos()


if __name__ == '__main__':

    # setup
    screen_xsize = 1920
    screen_ysize = 1080    
    
    keycap = KeyCapture()
    #cap = ScreenCapture((0,0,screen_xsize, screen_ysize))
    cap = ScreenCapture()

    # Example usage as generator.
    start_time = time.perf_counter()
    for frame, screenshot in enumerate(ScreenCapture((0, 0, screen_xsize, screen_ysize)), start=1):   
        fps = str(np.round(frame / (time.perf_counter() - start_time), decimals=2))
        keys_pressed = keycap.keyshot()
        mouse_position = keycap.mouseshot()
        print("\rFPS: {}, mouse: {}, keys: {}, ".format(fps, mouse_position, keys_pressed), end='', flush=True)

