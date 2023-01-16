import logging
import subprocess
import ffmpeg
import numpy as np
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class FFMPEGStreamer:

    def __init__(self, width=1920, height=1080, video_out_filename='video.mp4'):
        self.width = width
        self.height = height
        self.process2 = None
        self.video_out_filename = video_out_filename

    def start_ffmpeg_process(self):
        logger.info('Starting ffmpeg process2')
        
        pix_fmt = 'rgb24'

        args = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt=pix_fmt, s='{}x{}'.format(self.width, self.height))
            .output(self.video_out_filename, vcodec='h264_nvenc', pix_fmt='yuv420p', preset='slow')
            .overwrite_output()
            .compile()
        )
        self.process2 = subprocess.Popen(args, stdin=subprocess.PIPE)

    # from https://github.com/kkroening/ffmpeg-python/blob/master/examples/tensorflow_stream.py
    def write_frame(self, frame):
        logger.debug('Writing frame')
        self.process2.stdin.write(
            frame.tobytes()
        )

    def close(self):
        self.process2.stdin.close()
        self.process2.wait()

    def start(self):
        print('starting ffmpeg process')
        self.start_ffmpeg_process()

# example usage
if __name__ == '__main__':

    import Capture

    # set capture region, x, y, width, height
    region_ltrb = (0,0,1920, 1080)
    cap = Capture.ScreenCapture(region_ltrb)

    # set video stream output
    video_out_filename = 'output.mp4'
    stream = FFMPEGStreamer(video_out_filename=video_out_filename)
    stream.start()

    # iterate some frames and write
    for f in range(0, 100):
        frame = cap.screenshot()
        stream.write_frame(frame)
    
    stream.close()

