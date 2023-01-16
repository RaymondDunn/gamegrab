import csv
import time

# csv streamer via 
class CSVStreamer:

    def __init__(self, key_out_filename='keystrokes.csv', mouse_out_filename='mouse.csv'):

        self.key_out_filename = key_out_filename
        self.mouse_out_filename = mouse_out_filename

        # open filehandles and writers
        self.key_output_filehandle = open(self.key_out_filename, "w", newline='')
        self.mouse_output_filehandle = open(self.mouse_out_filename, "w", newline='')
        self.key_writer = csv.writer(self.key_output_filehandle)
        self.mouse_writer = csv.writer(self.mouse_output_filehandle)

    def write_keys_list(self, frame_number, keys_list):
        for key in keys_list:
            self.key_writer.writerow([frame_number, key])
            self.key_output_filehandle.flush()

    def write_mouse_pos(self, frame_number, mouse_pos):
        self.mouse_writer.writerow([frame_number, mouse_pos[0], mouse_pos[1]])

    def close(self):
        self.key_output_filehandle.close()
        self.mouse_output_filehandle.close()

    def start(self):
        print('starting csv output stream')

# example usage
if __name__ == '__main__':

    import Capture

    keycap = Capture.KeyCapture(retval='key')

    # set video stream output
    key_out_filename = 'keystrokes.csv'
    mouse_out_filename = 'mouse.csv'
    stream = CSVStreamer(key_out_filename=key_out_filename, mouse_out_filename=mouse_out_filename)
    stream.start()

    fps = 30
    frames_to_grab = fps * 5
    for f in range(0, frames_to_grab):
        keys_list = keycap.keyshot()
        mouse_pos = keycap.mouseshot()
        stream.write_keys_list(f, keys_list)
        stream.write_mouse_pos(f, mouse_pos)
        time.sleep(1/fps)
    
    stream.close()

