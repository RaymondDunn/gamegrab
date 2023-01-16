# from pyqtgraph.Qt import QtGui, QtCore
# from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import PlotWidget
from datetime import datetime
import pyqtgraph as pg
import numpy as np
import os
import pickle
import json
import tifffile as tf
import cv2
import pandas as pd

# single-window app
class MyApp:
    
    # sometimes, putting gui code in __init__ creates problems (e.g. serialization w/r/t subprocesses)
    def __init__(self, args={}):

        # initialize video capture
        self.datadir = args.get('datadir', './data/') 
        self.mouse_out_filename = self.datadir + args.get('mouse_out_filename', 'mouse.csv')
        self.key_out_filename = self.datadir + args.get('key_out_filename', 'keystrokes.csv')
        self.video_out_filename = self.datadir + args.get('video_out_filename', 'video.mp4')

        # local vars
        self.video_cap = None
        self.video_length = None
        self.current_frame_ndx = 0
        self.load_video()
        self.load_keystrokes()

        # initialize display
        self.intialize_display()

    # create gui window
    def intialize_display(self):
        
        # make app, we do it this way in case an instance of the app is
        # already running (like if using in jupyter notebook)
        #self.app = QtCore.QCoreApplication.instance()
        #if self.app is None:
        #    self.app = QtGui.QApplication([])
        self.app = pg.mkQApp()

        # it should exit on close per  https://stackoverflow.com/questions/57408620/cant-kill-pyqt-window-after-closing-it-which-requires-me-to-restart-the-kernal/58537032#58537032
        self.app.setQuitOnLastWindowClosed(True)

        # app has a main window
        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle(
            "Example PyQt app"
        )
        self.window.resize(1400, 800)

        # window has a grid layout (easy to add widgets/items to)
        self.window_grid = QtWidgets.QGridLayout()

        # add other grids/widgets into window
        self.plot_graphics_widget = pg.GraphicsLayoutWidget()
        self.command_panel_grid = QtWidgets.QGridLayout()

#
        #####################################################################
        # build gui elements here
        #####################################################################
        # image
        #############
        
        # create view box for image item with scrolling locked
        self.image_vbox = pg.ViewBox(lockAspect=True, enableMouse=True)

        # create image item to put image in
        self.image_ii = pg.ImageItem()
        
        # adjust image showing to be row-major and origin in top left, removing need for transpose
        self.image_ii.setOpts(axisOrder="row-major")
        self.image_vbox.invertY()

        # make histogram lookup widget
        self.lut_histogram_item = pg.HistogramLUTItem(image=self.image_ii, fillHistogram=False)

        # add image item to box, add image viewbox and lut histogram to plot graphics window
        self.image_vbox.addItem(self.image_ii)
        self.plot_graphics_widget.addItem(self.image_vbox)
        self.plot_graphics_widget.addItem(self.lut_histogram_item)

        ##############
        # slider
        ##############
        # label above slider
        self.frame_slider_label = QtWidgets.QLabel('frame slider: {}/{}'.format(self.current_frame_ndx, self.video_length))

        # slider
        self.video_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.video_frame_slider.setMinimum(0)
        self.video_frame_slider.setMaximum(self.video_length - 1)
        self.video_frame_slider.setTickInterval(1)
        self.video_frame_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.video_frame_slider.valueChanged.connect(self.refresh_dashboard)

        # add qlabel and slider to command panel
        self.command_panel_grid.addWidget(self.frame_slider_label, 0,0,1,2, alignment=QtCore.Qt.AlignCenter)
        self.command_panel_grid.addWidget(self.video_frame_slider, 1,0,1,2)


        #############
        # text boxes
        #############
        self.current_keystrokes_label = QtWidgets.QLabel("[]")
        self.command_panel_grid.addWidget(self.current_keystrokes_label, 2, 0, 1, 2)

        ####################
        ## cursor graphic
        #####################

        # render graphic object at mouse cursor
        self.cursor_diameter = 30
        self.cursor_graphic = QtWidgets.QGraphicsEllipseItem()
        cursor_pen = QtGui.QPen()
        cursor_pen.setWidth(3)
        cursor_pen.setColor(QtGui.QColor("green"))
        cursor_pen.setStyle(QtCore.Qt.DotLine)
        self.cursor_graphic.setPen(cursor_pen)
        self.image_vbox.addItem(self.cursor_graphic, ignoreBounds=False)

        #####################################################################

        # assemble hierarchical containers
        # add plot graphics widget and command panel to window grid
        self.window_grid.addWidget(self.plot_graphics_widget)
        self.window_grid.addItem(self.command_panel_grid)

        # set window layout to grid
        self.window.setLayout(self.window_grid)

        # show the window
        self.window.show()

        # update display
        self.refresh_dashboard()

        # begin event loop
        self.app.exec_()

    # helper to load video
    def load_video(self):

        # create video capture
        self.video_cap = cv2.VideoCapture(self.video_out_filename)
        self.video_length = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def load_keystrokes(self):
        self.keystroke_df = pd.read_csv(self.key_out_filename, header=None)
        self.mouse_df = pd.read_csv(self.mouse_out_filename, header=None)

    # helper to get frame from video
    def get_frame_from_video(self, frame_ndx):

        # set video capture to correct index
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_ndx)
        success, img = self.video_cap.read()

        if not success:
            print('Cant grab frame {} from video capture!'.format(frame_ndx))
        else:
            return img

    # function to update displayed images
    def update_display_image(self, img):

        # get current image
        self.image_ii.setImage(img, autoLevels=True)

    def update_current_keystrokes(self):
        self.current_frame_ndx = self.video_frame_slider.value()

        # set current keystrokes if there are any
        num_current_keystrokes = self.keystroke_df[self.keystroke_df[0] == self.current_frame_ndx].size
        if num_current_keystrokes > 0:
            current_keystrokes = self.keystroke_df[self.keystroke_df[0] == self.current_frame_ndx][1].to_list()
        else:
            current_keystrokes = []

        # set mouse position
        self.current_mouse_x = int(self.mouse_df[self.mouse_df[0] == self.current_frame_ndx][1])
        self.current_mouse_y = int(self.mouse_df[self.mouse_df[0] == self.current_frame_ndx][2])

        # set label and render cursor graphic
        self.current_keystrokes_label.setText('current keystrokes: {}'.format(current_keystrokes))
        
        # unpack and draw
        self.cursor_graphic.setRect(
            self.current_mouse_x - self.cursor_diameter // 2,
            self.current_mouse_y - self.cursor_diameter // 2,
            self.cursor_diameter,
            self.cursor_diameter,
        )

    # function to update displayed text in the window
    def update_display_text(self):
        
        self.current_frame_ndx = self.video_frame_slider.value()
        self.frame_slider_label.setText('frame slider: {}/{}'.format(self.current_frame_ndx, self.video_length))
        
    # wrapper function to update the window
    def refresh_dashboard(self):

        frame_ndx = self.video_frame_slider.value()
        img = self.get_frame_from_video(frame_ndx=frame_ndx)
        self.update_current_keystrokes()
        self.update_display_image(img)
        self.update_display_text()
     

# standalone testing
if __name__ == "__main__":

    # load file
    video_fname = 'C:/Users/rldun/code/gamegrab/data/video.mp4'
    
    # build app input parameters
    app_args = {
        'video_fname': video_fname
        }

    # instantiate app
    myapp = MyApp(app_args)