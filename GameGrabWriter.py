import pandas as pd
import KeyToFileStreamer
import ScreenToFileStreamer
import Capture
import os
import time
import numpy as np

class GameGrabWriter:

    def __init__(self, args={}):

        # initialize file handles
        self.datadir = args.get('datadir', './data/') 
        self.mouse_out_filename = self.datadir + args.get('mouse_out_filename', 'mouse.csv')
        self.key_out_filename = self.datadir + args.get('key_out_filename', 'keystrokes.csv')
        self.video_out_filename = self.datadir + args.get('video_out_filename', 'video.mp4')
        
        # check output dir
        if not os.path.isdir(self.datadir):
            os.mkdir(self.datadir)

        # load args
        self.region_ltrb = args.get('lrtb', (0,0,1920, 1080))
        self.key_encoding = args.get('key_encoding', 'key')
        self.fps = args.get('fps', 30)

        # derived args
        self.interframe_interval = 1/self.fps
        self.frame_time_list = []
        self.t0 = None

        # initialize readers
        self.screencap = Capture.ScreenCapture(self.region_ltrb)
        self.keycap = Capture.KeyCapture(retval=self.key_encoding)

        # open_writers
        self.WRITERS_ARE_OPEN = False
        self.initialize_writers()

    def initialize_writers(self):
        
        if not self.WRITERS_ARE_OPEN:

            # open writers
            self.keystroke_writer = KeyToFileStreamer.CSVStreamer(key_out_filename=self.key_out_filename, mouse_out_filename=self.mouse_out_filename)
            self.keystroke_writer.start()
            self.screen_writer = ScreenToFileStreamer.FFMPEGStreamer(video_out_filename=self.video_out_filename)
            self.screen_writer.start()

            # mark flag
            self.WRITERS_ARE_OPEN = True

    def close_writers(self):

        if self.WRITERS_ARE_OPEN:
            self.screen_writer.close()
            self.keystroke_writer.close()
            self.WRITERS_ARE_OPEN = False

    def read(self):
        frame = self.screencap.screenshot()
        keys_list = self.keycap.keyshot()
        mouse_pos = self.keycap.mouseshot()
        return frame, keys_list, mouse_pos

    def write(self, frame_number, frame, keys_list, mouse_pos):
        self.screen_writer.write_frame(frame)
        self.keystroke_writer.write_keys_list(frame_number, keys_list)
        self.keystroke_writer.write_mouse_pos(frame_number, mouse_pos)

    def snap(self, frame_number):
        frame, keys_list, mouse_pos = self.read()
        self.write(frame_number, frame, keys_list, mouse_pos)

    def record(self, rec_duration_seconds):

        # open writers if they aren't already
        self.initialize_writers()
        
        # calculate frames
        frames = int(rec_duration_seconds * self.fps)
        
        # repeatedly snap
        self.frame_time_list = []
        self.t0 = time.time()
        next_call = self.t0
        for f in range(frames):
            self.snap(f)
            self.frame_time_list.append(time.time() - self.t0)
            nowtime = time.time()
            next_call = next_call + self.interframe_interval / 1000
            if next_call - nowtime < 0:
                # print("warning: strobe delay exceeded inter-frame-interval on frame {}.".format(f))
                pass
            else:
                time.sleep(next_call - nowtime)

        # close writers
        self.close_writers()

    def close(self):
        self.close_writers()

    def print_summary(self):

        if self.t0 is not None:

            # print inter frame interval
            frame_times = np.array(ggw.frame_time_list)
            delays = frame_times[1:] - frame_times[:-1]
            actual_fps = 1/delays.mean()
            print('goal fps: {}, actual: {}'.format(self.fps, actual_fps))


# example usage
if __name__ == '__main__':

    rec_duration_seconds = 5
    
    # initalize writer to save data, all defaults
    ggw = GameGrabWriter()
    
    # do example recording
    ggw.record(rec_duration_seconds)

    # print summary
    ggw.print_summary()

    # close
    ggw.close()


# example in interactive session
"""
from GameGrabWriter import GameGrabWriter
import numpy as np

ggw = GameGrabWriter()

ggw.record(5)

# do stuff

t0 = ggw.t0
frame_times = np.array(ggw.frame_time_list)
delays = frame_times[1:] - frame_times[:-1]


"""