#!/usr/bin/env python

from flac import AudioFile
from PyQt5.QtCore import QDir, Qt, QUrl, QByteArray
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget)
from PyQt5.QtWidgets import QMainWindow,QWidget, QPushButton, QAction
from PyQt5.QtGui import QIcon, QPixmap, QGuiApplication
import sys


class AudioWindow(QMainWindow):

    def __init__(self, parent=None):
        super(AudioWindow, self).__init__(parent)
        self.setWindowTitle("Flac player")

        self.mediaPlayer = QMediaPlayer()
        self.file_info = None

        #videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.volumeSlider = QSlider(Qt.Vertical)
        self.volumeSlider.setRange(0, 0)
        self.volumeSlider.setValue(100)
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.volumeSlider.sliderMoved.connect(self.setVolume)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                QSizePolicy.Maximum)

        self.info_window = InfoWindow(self.file_info)

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open flac file')
        openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        self.infoAction = QAction('&File info', self)
        self.infoAction.setStatusTip('Show file info')
        self.infoAction.triggered.connect(self.showInfo)
        self.infoAction.setEnabled(False)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.infoAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.volumeSlider)

        layout = QVBoxLayout()
        #layout.addWidget(videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        #self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.volumeChanged.connect(self.volumeChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open flac file",
                                                  QDir.homePath())
        if fileName != '':
            try:
                    self.file_info = AudioFile(fileName)

            except Exception:
                self.infoAction.setEnabled(False)
                self.errorLabel.setText('Error: file is not flac')
                self.mediaPlayer.setMedia(QMediaContent())
                self.playButton.setEnabled(False)
                self.volumeSlider.setRange(0, 0)
            else:
                self.infoAction.setEnabled(True)
                self.volumeSlider.setRange(0, 100)
                self.volumeSlider.setValue(100)
                self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
                self.errorLabel.setText('')
                self.playButton.setEnabled(True)

    def exitCall(self):
        sys.exit(app.exec_())

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def volumeChanged(self, volume):
        self.volumeSlider.setValue(volume)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def setVolume(self, volume):
        self.mediaPlayer.setVolume(volume)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def showInfo(self):
        self.info_window = InfoWindow(self.file_info)
        self.info_window.show()


class InfoWindow(QWidget):
    def __init__(self, file_info):
        super().__init__()
        self.file_info = file_info
        self.setWindowTitle('Audio info')
        layout = QVBoxLayout(self)
        infoLabel = QLabel()
        infoLabel.setText(self.make_text())
        # pictureLabel = QLabel()
        # if self.file_info:
        #     if self.file_info.picture:
        #         picture = QPixmap()
        #         picture.loadFromData(self.file_info.picture[0], self.file_info.picture[1])
        #         pictureLabel.setPixmap(picture)
        self.saveButton = QPushButton('Save image')
        if self.file_info:
            if self.file_info.picture:
                self.saveButton.setEnabled(True)
                self.saveButton.clicked.connect(self.file_info.save_picture)
        layout.addWidget(infoLabel)
        layout.addWidget(self.saveButton)
        self.setLayout(layout)

    def make_text(self):
        text = ''
        if self.file_info:
            text = '''                      minimum block size: {0} samples
                      maximum block size: {1} samples
                      minimum frame size: {2} bytes
                      maximum frame size: {3} bytes
                      sample rate: {4} Hz
                      number of channels: {5}
                      bits per sample: {6}
                      samples in stream: {7}'''.format(self.file_info.streaminfo['block_minsize'],
                                                       self.file_info.streaminfo['block_maxsize'],
                                                       self.file_info.streaminfo['frame_minsize'],
                                                       self.file_info.streaminfo['frame_maxsize'],
                                                       self.file_info.streaminfo['rate'],
                                                       self.file_info.streaminfo['channels'],
                                                       self.file_info.streaminfo['bits per sample'],
                                                       self.file_info.streaminfo['samples in flow'])
            if self.file_info.tags:
                tags = ''
                for tag in self.file_info.tags:
                    if tag is 'vendor': continue
                    i = 0
                    tags += '\n                      {0}: '.format(tag)
                    for tag_value in self.file_info.tags[tag]:
                        tags += tag_value
                        if i != len(self.file_info.tags[tag]) - 1:
                            tags += ', '
                        i += 1
                text += tags

        return text


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = AudioWindow()
    player.resize(640, 200)
    player.show()
    sys.exit(app.exec_())
