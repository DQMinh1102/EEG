from PyQt5 import QtWidgets, QtCore, QtGui, QtCore
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSlot
import pyqtgraph as pg
import serial
import sys
import time
import numpy as np
import csv
from PyQt5 import uic
from scipy.signal import sosfiltfilt, butter
import glob

counter = 0
jumper = 10

class MainWindow(QtWidgets.QMainWindow):
    switch_rev_list_window = QtCore.pyqtSignal()
    switch_window = QtCore.pyqtSignal()
    def __init__(self, *args, **kwargs):
        global save_btn, run_btn, OK_btn, NO_btn
        QtWidgets.QMainWindow.__init__(self,*args, **kwargs)
        self.resize(1920,900)
        self.setWindowTitle("EEG-Blink")
        self.setWindowIcon(QIcon("mat2.png"))
        self.portName = []                      # replace this port name by yours!
        self.ser = serial.Serial()
        # app.aboutToQuit.connect(self.closeEvent)
        self.ttfp1 = 0
        self.ttfp2 = 0
        self.tt1 = 1
        self.tt2 = 1
        self.fp1 = [1,5,3,6,5,7,8,4,5,6,4,5,6,2,5]
        self.fp2 = [1,3,6,5,4,7,3,7,5,7,1,4,5,2,9]
        self.fs = 128  
        self.cutoff_h = 30
        self.cutoff_l = 1
        self.nyq = 0.5 * self.fs
        self.order = 2   
      
        self.windowWidth = 1000
        self.Fp1 = np.zeros(self.windowWidth)
        self.Fp2 = np.zeros(self.windowWidth)
        self.ptr = - self.windowWidth
        self.tt_f = 0

        self.run = True

        self.fileName = []
        self.threadpool = QtCore.QThreadPool()  #chạy đa luồng
        
        self.graph_layout = QtWidgets.QVBoxLayout()
        self.layout1 = QtWidgets.QVBoxLayout()
        self.layout2 = QtWidgets.QVBoxLayout()  
        self.filter_layout = QtWidgets.QHBoxLayout()
        self.back_layout =QtWidgets.QHBoxLayout()
        self.bt_layout = QtWidgets.QHBoxLayout()
        self.main_layout = QtWidgets.QHBoxLayout()
    # graph layout
        self.Fp1_graphWidget = pg.PlotWidget()
        self.Fp1_graphWidget.setTitle("EEG Fp1", size="12pt", color = "#ffffff")
        self.Fp1_graphWidget.setLabel('left', 'Amplitude ')
        self.Fp1_graphWidget.setLabel('bottom', 'Samples')
        self.Fp1_graphWidget.setYRange(0.8, -0.8)
        self.Fp1_graphWidget.showGrid(x=True, y=True, alpha=1)
        # self.Fp1_graphWidget.invertY(True)

        self.Fp2_graphWidget = pg.PlotWidget()
        self.Fp2_graphWidget.setTitle("EEG Fp2", size="12pt", color = "#ffffff")
        self.Fp2_graphWidget.setLabel('left', 'Amplitude ')
        self.Fp2_graphWidget.setLabel('bottom', 'Samples')
        self.Fp2_graphWidget.setYRange(0.8, -0.8)
        self.Fp2_graphWidget.showGrid(x=True, y=True, alpha=1)
        # self.Fp2_graphWidget.invertY(True)
        # self.Fp2_graphWidget.getPlotItem().hideAxis('left')
        self.Fp1_graphWidget.setBackground('#1d1f24') 
        self.Fp2_graphWidget.setBackground('#1d1f24')
     
        self.eye_lbl = QtWidgets.QLabel('Eye Blink Detection:       ')
        self.eye_lbl.setStyleSheet( " color: #2b4bab;"
                                    "background-color: #dbdbdb;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 23px;"
                                "padding: 15px;"                                 
                                )    
# label run and save
        self.run_save = QtWidgets.QLabel()
        self.run_save.setStyleSheet( " color: #1d1f24;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )
# Back for window review
        self.back_btn = QtGui.QPushButton("TURNBACK")
        self.back_btn.setIcon(QtGui.QIcon('back.png'))
        self.back_btn.setIconSize(QtCore.QSize(40,40))
        self.back_btn.setStyleSheet( "QPushButton" "{"
                                        " color: #222831;"
                                    "background-color: #a6bdba;"
                                    "selection-background-color: blue;"
                                    "border-radius: 10px;"
                                    "font: bold 18px;"
                                    "padding: 8px;""}"
                                        "QPushButton::hover" "{"
                                        "background-color: #87dec7;""}"
                                    "QPushButton::pressed" "{"
                                        "background-color: #60b59f; ""}"                           
                                    ) 
        self.back_btn.hide()
        self.back_layout.setContentsMargins(1500,0,0,15)
        self.back_layout.addWidget(self.back_btn)
# check filter
        self.check_fil = QtWidgets.QCheckBox("FILTER ")
        self.check_fil.setToolTip('Clicking to filter the signal ')
        self.check_fil.setStyleSheet( "QCheckBox" "{"
                                    " color:#f7bd3e; "
                                "background-color:  #1d1f24;"
                                "border-radius: 10px;"
                                "font: bold 20px;"
                                "padding: 0px;""}"                              
                                )
        self.check_fil.setChecked(False)
        self.check_fil.stateChanged.connect(self.oncheck)
        self.filter_layout.setContentsMargins(1700,0,0,0)
        self.filter_layout.addWidget(self.check_fil)
        self.graph_layout.setContentsMargins(30,0,0,0)
        self.graph_layout.addWidget(self.Fp1_graphWidget)
        self.graph_layout.addWidget(self.Fp2_graphWidget)
        # graph_layout.addWidget(self.run_save)
        self.graph_layout.addWidget(self.eye_lbl)
        self.layout1.addLayout(self.bt_layout)
        self.layout1.addLayout(self.filter_layout)
        self.layout1.addLayout(self.graph_layout)
        self.layout1.addLayout(self.back_layout)
        # Button
        self.com_lbl = QtWidgets.QLabel('Checking COM...')
        self.com_lbl.setStyleSheet( " color: #ffffff;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )                
        self.com_btn = QtGui.QComboBox()
        self.com_btn.setIconSize(QtCore.QSize(40,40))
        self.com_btn.setStyleSheet( "QComboBox" "{"" color: #222831;"
                                "background-color: #4e99cc;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"  "}"
                                 "QComboBox::hover" "{"" color: #222831;"
                                    "background-color: #82ace8;""}" 
                                    "QListView" "{""background-color: #82ace8;""} "                         
                                )   
        self.com_btn.addItems(["Select COM Port","COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9","COM10"])
        index = 0
        blu = QIcon('blu.png')
        self.com_btn.setItemIcon(index,blu)
        self.com_btn.currentTextChanged.connect(self.on_combobox_func)
        
        self.run_btn = QtGui.QPushButton("  RUN")
        self.run_btn.setIcon(QtGui.QIcon('run.png'))
        self.run_btn.setIconSize(QtCore.QSize(40,40))
        self.run_btn.setStyleSheet( "QPushButton" "{"
                                    " color: #222831;"
                                "background-color: #a6bdba;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color: #9ce695;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #7bc274;""}"                              
                                )  
        self.run_btn.setEnabled(False)
        self.save_btn = QtGui.QPushButton("  SAVE")
        self.save_btn.setIcon(QtGui.QIcon('save.png'))
        self.save_btn.setIconSize(QtCore.QSize(40,40))
        self.save_btn.setStyleSheet("QPushButton" "{"
                                    " color: #222831;"
                                "background-color:  #a6bdba;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color:  #87cfd6;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #19b3c2;""}"                           
                                )  
# ----------------btn_review---------------------
        self.rev_btn = QtGui.QPushButton("  REVIEW")
        self.rev_btn.setIcon(QtGui.QIcon('rev.png'))
        self.rev_btn.setIconSize(QtCore.QSize(40,40))
        self.rev_btn.setStyleSheet("QPushButton" "{"
                                    " color: #222831;"
                                "background-color:  #a6bdba;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color:  #f2e8ae;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #d6c878;""}"                           
                                ) 
    # -------------
        self.blink_l = QtWidgets.QLabel(' L ')
        self.blink_l.setStyleSheet( " color: #1d1f24;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 17px;"
                                "padding: 10pxpx;"                                 
                                )
        self.blink_r = QtWidgets.QLabel(' R ')
        self.blink_r.setStyleSheet( " color: #1d1f24;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 17px;"
                                "padding: 10pxpx;"                                 
                                )
#-------SAVE WINDOW--------
        self.stop_btn = QtGui.QPushButton()
        self.stop_btn.setIcon(QtGui.QIcon('stop.png'))
        self.stop_btn.setIconSize(QtCore.QSize(40,40))
        self.stop_btn.setToolTip('Stop Saving')
        self.stop_btn.setStyleSheet("QPushButton" "{"
                                    " color: #222831;"
                                "background-color: #a6bdba;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color: #edadab;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #d97471;""}"                         
                                ) 
        self.stop_btn.hide()

        self.bt_layout.setContentsMargins(50,10,50,5)
        self.bt_layout.setSpacing(40)
        self.bt_layout.addWidget(self.com_btn)
        self.bt_layout.addWidget(self.com_lbl)
        self.bt_layout.addWidget(self.run_btn)
        self.bt_layout.addWidget(self.stop_btn) 
        self.bt_layout.addWidget(self.save_btn) 
        self.bt_layout.addWidget(self.rev_btn) 
        self.bt_layout.addWidget(self.run_save)
        # bt_layout.addWidget(self.back_btn)
        self.layout2.setContentsMargins(15,200,20,150)
        self.layout2.setSpacing(250)
        self.layout2.addWidget(self.blink_l)
        self.layout2.addWidget(self.blink_r)
        self.main_layout.addLayout(self.layout1)
        self.main_layout.addLayout(self.layout2)         
# ---------Layout chính--------
        widget = QtWidgets.QWidget()
        widget.setLayout(self.main_layout)
        widget.autoFillBackground()
        widget.setStyleSheet( "background-color: #1d1f24;")
        self.setCentralWidget(widget)      
# ---------------------Khung plot Data------------------------
        pen1 = pg.mkPen(color=(33, 211, 217))
        pen2= pg.mkPen(color=(235, 113, 141))
        pen1.setWidth(0.5)
        pen2.setWidth(0.5)
        self.curve =  self.Fp1_graphWidget.plot(pen=pen1)
        self.curve2 =  self.Fp2_graphWidget.plot(pen=pen2)
        self.update_plot_data()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(7)  
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        self.run_btn.clicked.connect(self.start_worker)
        self.run_btn.clicked.connect(self.run_btn_clicked)
        self.save_btn.clicked.connect(self.save_btn_clicked)
        self.stop_btn.clicked.connect(self.Stop_saving)
        self.rev_btn.clicked.connect(self.rev_btn_clicked)
        
    def closeEvent(self,event):
        reply = QtWidgets.QMessageBox.information(self, 'QUIT', 'Are you sure you want to quit?',
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.run = False
                self.ser.close()
                event.accept()
                # self.close()
                sys.exit()
            except:
                pass  
        else:
            event.ignore()  

    def oncheck(self, state):
        if state == QtCore.Qt.Checked:
            self.tt_f = 1
            self.run_save.setText('Run Filter')
        else:
            self.tt_f = 0
            self.run_save.setText('Run Raw')
    def butter_bandpass_filter(self, data, cutoff_h, cutoff_l, fs, order):
        high_cut = cutoff_h / self.nyq
        low_cut = cutoff_l / self.nyq
        sos = butter(order, [low_cut,high_cut], btype='bandpass', analog=False, output = 'sos', fs = fs)
        y = sosfiltfilt(sos, data)
        return y
    def start_worker(self):
        worker = Worker(self.start_stream,)
        self.threadpool.start(worker)
    def start_stream(self):
        self.run_btn.setEnabled(False)
        self.get_data()

    def get_data(self):
        print(self.portName) 
        if self.fileName:
            self.writer.writeheader()
        else:
            pass
        while self.run:
            try:
                self.Fp1[:-1] = self.Fp1[1:]          
                self.Fp2[:-1] = self.Fp2[1:]          
                data = self.ser.readline()            
                value_decode = str(data.strip(b'\r\n').decode('utf8'))
                value_list = value_decode.split(',')   
                if self.fileName:
                    self.writer.writerow({'Fp1': str(value_list[0]), 'Fp2': str(value_list[1])})
                else:
                    pass
                if self.tt_f == 1:
############## FILTER
                    self.fp1.append(int(float(value_list[0]))) 
                    self.fp2.append(int(float(value_list[1])))
                    if self.fp1[-1] < 690 or self.fp2[-1] < 690:
                        if self.fp1[-1] < 690 and self.fp2[-1] > 690:
                            self.ttfp1 = 1
                        else:
                            self.ttfp2 = 1
                    if self.ttfp2 == 1 and self.tt2 == 1:
                        self.ttfp2 == 0
                        self.tt2 = 0
                        self.blink_r_eye()
                    if self.ttfp1 == 1 and self.tt1 == 1:
                        self.ttfp1 == 0
                        self.tt1 = 0
                        self.blink_l_eye()
                    self.fp1_filted = self.butter_bandpass_filter(self.fp1,  
                                                        self.cutoff_h, self.cutoff_l, self.fs, self.order)
                    self.fp2_filted = self.butter_bandpass_filter(self.fp2,  
                                                        self.cutoff_h, self.cutoff_l, self.fs, self.order)
                    self.Fp1[-1] = self.fp1_filted[-1]    
                    self.Fp2[-1] = self.fp2_filted[-1]
                    self.fp1.pop(0)
                    self.fp2.pop(0)
                # self.ptr += 1
                else:
############## NON_FILTER
                    self.Fp1[-1] = float(value_list[0])                           
                    self.Fp2[-1] = float(value_list[1])                   
                    if self.fp1[-1] < 690 or self.fp2[-1] < 690:
                        if self.Fp2[-1] < 690 and self.Fp1[-1] > 690:
                            self.ttfp2 = 1
                        elif self.fp1[-1] < 698 and self.fp2[-1] > 690:
                            self.ttfp1 = 1
                        
                    if self.ttfp2 == 1 and self.tt2 == 1:
                        self.ttfp2 == 0
                        self.tt2 = 0
                        self.blink_r_eye()
                    if self.ttfp1 == 1 and self.tt1 == 1:
                        self.ttfp1 == 0
                        self.tt1 = 0
                        self.blink_l_eye()
################
                self.ptr += 1
            except:
                pass

    def update_plot_data(self):
        self.curve.setData(self.Fp1)                
        self.curve.setPos(self.ptr,0)                    
        self.curve2.setData(self.Fp2)                
        self.curve2.setPos(self.ptr,0)                    
    def file_save(self,text):
        self.fileName.append(text)
        print(self.fileName)
        print(self.fileName[-1])
        if self.fileName:
            self.file = open(self.fileName[-1], "a", newline="")
            self.fieldnames = ['Fp1', 'Fp2']
            self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
            print("Created file")
        else:
            pass

    def on_combobox_func(self, text):  # +++
        try:
            self.a = []
            self.current_text  = text
            self.portName.append(text)
            self.baudrate = 9600
            self.ser = serial.Serial(self.portName[-1],self.baudrate)
            self.a.append(self.ser.readline())
            print("Connected to", self.portName[-1])
            self.com_lbl.setText("  Connected to " + self.portName[-1]+"        ")
            self.com_lbl.setStyleSheet( " color: #00fa08;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )
            self.run_save.setText('')
            self.run_btn.setEnabled(True)
        except:
            # self.run_btn.setEnabled(False)
            print("Failed to connect to COM port")          
            self.com_lbl.setText("Failed to connect to COM port")
            self.com_lbl.setStyleSheet( " color: #f06960;"
                                    "background-color:#1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )
            self.run_save.setText('')
            
    def run_btn_clicked(self):                         
        self.run_btn.setStyleSheet( " color: #222831;"
                                "background-color: #f07171;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;"                                
                                )   
                   
        if self.ser.is_open == True:
            self.run_save.setText("Running...")
            self.run_save.setStyleSheet( " color: #00fa08;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )  
            # self.run_btn.setEnabled(False)
        else:
            self.run_save.setText("**COM port error !!")
            self.run_save.setStyleSheet( " color: #f07171;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: italic 17px;"
                                "padding: 10px;")
            self.run_btn.setStyleSheet( " color: #222831;"
                                "background-color: #79d1a1;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 6px;"                                
                                )
            self.ser.close()
    def save_btn_clicked(self):
        self.save_btn.setStyleSheet( "color: #222831;"
                                "background-color: #f07171;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;"    
                                "font color: black;" )                          
        self.run_btn.setStyleSheet( "color: #222831;"
                                "background-color: #79d1a1;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;"    
                                "font color: white;"                            
                                )  
        self.save_btn.setEnabled(True)
        if self.ser.is_open == True:
            self.ser.close()
            self.switch_window.emit()   
        self.switch_window.emit() 
       
    def rev_btn_clicked(self):
        self.switch_rev_list_window.emit()

    def Stop_saving(self):
        self.file.close()
        self.run_save.setText('Stop Saving into file '+ self.fileName[-1])
        self.run_save.setStyleSheet( " color: #ffd940;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )
        self.fileName.pop()
    def blink_r_eye(self):
        self.thread_r = Blink(eyes=2)
        self.thread_r.start()
        self.thread_r.blink.connect(self.blink_eye)
        self.thread_r.non_blink.connect(self.non_blink_eye)

    def blink_l_eye(self):
        self.thread_l = Blink(eyes=1)
        self.thread_l.start()
        self.thread_l.blink.connect(self.blink_eye)
        self.thread_l.non_blink.connect(self.non_blink_eye)
    
    def blink_eye(self):
        eyes = self.sender().eyes
        if eyes == 1:
            self.blink_l.setStyleSheet( "background-color: #f0e141;" )
            self.eye_lbl.setText('Eye Blink Detection:  LEFT')
        if eyes == 2:
            self.blink_r.setStyleSheet( "background-color: #f0e141;" )
            self.eye_lbl.setText('Eye Blink Detection:  RIGHT')
        if eyes ==1 and eyes ==2:
            self.blink_l.setStyleSheet( "background-color: #f0e141;" )
            self.blink_r.setStyleSheet( "background-color: #f0e141;" )
            self.eye_lbl.setText('Eye Blink Detection:  BOTH')
    def non_blink_eye(self):
        eyes = self.sender().eyes
        if eyes == 1:
            self.blink_l.setStyleSheet( "background-color: #1d1f24;" )
            self.eye_lbl.setText('Eye Blink Detection:     ')
            self.ttfp1 = 0
            self.tt1 = 1
        if eyes == 2:
            self.blink_r.setStyleSheet( "background-color: #1d1f24;" )
            self.eye_lbl.setText('Eye Blink Detection:     ')
            self.ttfp2 = 0
            self.tt2 = 1

class Blink(QtCore.QThread):
    blink = QtCore.pyqtSignal()
    non_blink = QtCore.pyqtSignal()
    def __init__(self, eyes = 0):
        super().__init__()
        self.eyes = eyes
    def run(self):
        self.blink.emit()
        time.sleep(0.5)
        self.non_blink.emit()

class Worker(QtCore.QRunnable):
    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
    @pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)

class ReviewList(QtWidgets.QMainWindow):
    switch_rev_window = QtCore.pyqtSignal(str)
    switch_window = QtCore.pyqtSignal()
    def __init__(self,*args, **kwargs):
        super(ReviewList, self).__init__()
        try:
            self.resize(600,600)
            self.setWindowTitle("Review Data") 
            self.setWindowIcon(QIcon("mat2.png"))
            self.mainrev_layout = QtWidgets.QVBoxLayout()
            self.list_layout = QtWidgets.QVBoxLayout()
            self.btn_layout = QtWidgets.QHBoxLayout()
            self.listWidget = QtWidgets.QListWidget()

            self.path = "C:/Users/ASUS/Desktop/DATN/Processing data"
            self.files = glob.glob(self.path + "/*.csv")
            for filename in self.files:
                self.listWidget.addItem(filename.split('\\')[1])
            self.back_list_btn = QtGui.QPushButton("  TURNBACK")
            self.back_list_btn.setIcon(QtGui.QIcon('back.png'))
            self.back_list_btn.setIconSize(QtCore.QSize(40,40))
            self.back_list_btn.setStyleSheet( "QPushButton" "{"
                                        " color: #222831;"
                                    "background-color: #a6bdba;"
                                    "selection-background-color: blue;"
                                    "border-radius: 10px;"
                                    "font: bold 16px;"
                                    "padding: 8px;""}"
                                        "QPushButton::hover" "{"
                                        "background-color: #87dec7;""}"
                                    "QPushButton::pressed" "{"
                                        "background-color: #60b59f; ""}"                           
                                    )
            self.back_list_btn.clicked.connect(self.back_to_main)
            self.listWidget.itemDoubleClicked.connect(self.onClicked)
            self.btn_layout.setContentsMargins(300,0,0,0)
            self.mainrev_layout.addLayout(self.list_layout)
            self.mainrev_layout.addLayout(self.btn_layout)
            self.btn_layout.addWidget(self.back_list_btn)
            self.list_layout.addWidget(self.listWidget)
            widget1 = QtWidgets.QWidget()
            widget1.setLayout(self.mainrev_layout)
            widget1.autoFillBackground()
            widget1.setStyleSheet( "background-color: #1d1f24;") 
            self.setCentralWidget(widget1)
            self.listWidget.setStyleSheet(" color: #171515;"
                                "background-color: #e3e1e1;"
                                "border-radius: 10px;"
                                "font: bold 19px;"
                                "padding: 10px;"  "}"
                                )
        except:
            pass

    def back_to_main(self):
        self.close()
        self.switch_window.emit()
    def onClicked(self, item):
        self.switch_rev_window.emit(item.text())
        self.close()

class RevWindow(MainWindow):
    switch_window = QtCore.pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.Fp1_graphWidget.invertY(False)
        self.Fp2_graphWidget.invertY(False)
        self.run_btn.hide()
        self.save_btn.hide()
        self.rev_btn.hide()
        self.back_btn.show()
        self.eye_lbl.hide() 
        self.back_btn.clicked.connect(self.back_btn_clicked)
        self.com_btn.hide()
    def get_data(self):
        return super().get_data()
        
    def on_combobox_func(self, text):
        return super().on_combobox_func(text)

    def back_btn_clicked(self):
        self.run = False
        self.hide()
        self.switch_window.emit()

class SaveWindow(QtWidgets.QMainWindow):
    switch_window = QtCore.pyqtSignal(str)
    def __init__(self,*args, **kwargs):
        super(SaveWindow, self).__init__()
        self.resize(600,300)
        self.setWindowTitle("Save Data") 
        self.setWindowIcon(QIcon("mat2.png"))
        btn1_layout = QtWidgets.QHBoxLayout()
        save_layout = QtWidgets.QVBoxLayout()
        mainsave_layout = QtWidgets.QVBoxLayout()

        self.file_lbl = QtWidgets.QLabel('File name:')
        self.file_lbl.setStyleSheet( " color: #ffffff;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 18px;"
                                "padding: 10px;"                                 
                                )
        self.file_note = QtWidgets.QLabel("NOTE" + "\n"+ "*You MUST name the file. If you DON'T, it will return MainWindow"+ "\n"
                                         +"**The file name MUST have '.csv' at the end, Example: EEG_blink.csv")
        self.file_note.setAlignment(Qt.AlignBottom)
        self.file_note.setStyleSheet( " color: #ffffff;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: italic 17px;"
                                "padding: 20px;"                                 
                                )
        self.file_name = QtWidgets.QLineEdit('Enter here')
        self.file_name.setAlignment(Qt.AlignTop)
        self.file_name.setStyleSheet( " color: #ffffff;"
                                    "background-color: #3b3432;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )
        # self.file_name.textChanged.connect(self.OK_saving)
        self.OK_btn = QtGui.QPushButton(" Save Now")
        self.OK_btn.setIcon(QtGui.QIcon('OK.png'))
        self.OK_btn.setIconSize(QtCore.QSize(40,40))
        self.OK_btn.setStyleSheet( "QPushButton" "{"
                                    " color: #222831;"
                                "background-color: #a6bdba;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color: #9ce695;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #7bc274;""}"                           
                                )
        self.NO_btn = QtGui.QPushButton("  Cancel")
        self.NO_btn.setIcon(QtGui.QIcon('no.png'))
        self.NO_btn.setIconSize(QtCore.QSize(40,40))
        self.NO_btn.setStyleSheet( "QPushButton" "{"
                                    " color: #222831;"
                                "background-color: #a6bdba;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 16px;"
                                "padding: 8px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color: #edadab;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #d97471;""}"                           
                                )
        
        mainsave_layout.setContentsMargins(30,30,30,30)
        save_layout.setContentsMargins(0,0,0,50)
        save_layout.setSpacing(0)
        save_layout.addWidget(self.file_lbl)
        save_layout.addWidget(self.file_name)
        save_layout.addWidget(self.file_note)
        mainsave_layout.addLayout(save_layout)
        btn1_layout.addWidget(self.OK_btn)
        btn1_layout.addWidget(self.NO_btn)
        mainsave_layout.addLayout(btn1_layout)

        widget1 = QtWidgets.QWidget()
        widget1.setLayout(mainsave_layout)
        widget1.autoFillBackground()
        widget1.setStyleSheet( "background-color: #1d1f24;") 
        self.setCentralWidget(widget1)

        self.OK_btn.clicked.connect(self.OK_saving)
        self.NO_btn.clicked.connect(self.Cancel)
        
    def OK_saving(self):
        self.switch_window.emit(self.file_name.text())
    def Cancel(self):
        self.file_name = QtWidgets.QLineEdit('Enter here')
        self.close()
        self.switch_window.emit(self.file_name.text())
 
class FirstWindow(QtWidgets.QMainWindow):
    switch_window = QtCore.pyqtSignal()
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self) 
        self.setGeometry(500,80,900,700)
        self.setWindowTitle("Welcome to H-M DEVICE") 
        self.setWindowIcon(QIcon("mat2.png")) 
        self.port_name = "COM ?"
        btn2_layout = QtWidgets.QVBoxLayout()
        logo_layout = QtWidgets.QHBoxLayout()
        mainblue_layout = QtWidgets.QVBoxLayout()
        widget1 = QtWidgets.QWidget()
        widget1.setLayout(mainblue_layout)
        widget1.autoFillBackground()
        widget1.setStyleSheet( "background-color: #ffffff;") 
        self.setCentralWidget(widget1)

        self.label1 = QtWidgets.QLabel()
        spkt = QtGui.QPixmap("SPKT.png")
        spkt = spkt.scaled(698, 256, QtCore.Qt.KeepAspectRatio)
        self.label1.setPixmap(spkt)
        
        self.label2 = QtWidgets.QLabel()
        bme = QtGui.QPixmap("logo BME.png")
        bme = bme.scaled(150, 150, QtCore.Qt.KeepAspectRatio)
        self.label2.setPixmap(bme)

        self.label3 = QtWidgets.QLabel()
        self.label3.setAlignment(Qt.AlignCenter)
        ten = QtGui.QPixmap("ten.png")
        ten = ten.scaled(692, 302, QtCore.Qt.KeepAspectRatio)
        self.label3.setPixmap(ten)

        self.connect_btn = QtGui.QPushButton("CONNECT TO H-M DEVICE")
        self.connect_btn.setStyleSheet("QPushButton" "{"
                                    " color: #3e4e54;"
                                "background-color:   #92d9e0;"
                                "selection-background-color: blue;"
                                "border-radius: 10px;"
                                "font: bold 17px;"
                                "padding: 15px;""}"
                                    "QPushButton::hover" "{"
                                    "background-color:  #f7c1d6;""}"
                                  "QPushButton::pressed" "{"
                                    "background-color: #ed9fb6;""}"                           
                                )  

        self.connect_lb = QtWidgets.QLabel()
        logo_layout.setContentsMargins(0,0,10,00)
        logo_layout.addWidget(self.label1)
        logo_layout.addWidget(self.label2)
        btn2_layout.setContentsMargins(90,0,90,50)
        btn2_layout.setSpacing(0)
        btn2_layout.addWidget(self.label3)
        btn2_layout.addWidget(self.connect_lb)
        # self.connect_lb.setText("YOUR COM PORT IS:    " + self.port_name)
        self.connect_lb.setAlignment(Qt.AlignCenter)
        self.connect_lb.setStyleSheet( " color: #db1118;"
                                    "background-color: #FFFFFF;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 19px;"
                                "padding: 10px;")
        btn2_layout.addWidget(self.connect_btn)
        mainblue_layout.addLayout(logo_layout)
        mainblue_layout.addLayout(btn2_layout)
        self.connect_btn.clicked.connect(self.connect)

        widget1 = QtWidgets.QWidget()
        widget1.setLayout(mainblue_layout)
        widget1.autoFillBackground()
        widget1.setStyleSheet( "background-color: #ffffff;") 
        self.setCentralWidget(widget1)

    def connect(self):
        self.switch_window.emit()
        self.close()

class SplashScreen(QtWidgets.QMainWindow):
    switch_window = QtCore.pyqtSignal()
    def __init__(self,*args, **kwargs):
        super(SplashScreen, self).__init__()
        self.ui = uic.loadUi("splash_screen.ui", self)
        self.progressBarValue(0)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)  
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.ui.circularBg.setGraphicsEffect(self.shadow)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)
        self.timer.start(9)
        self.show()

    def progress(self):
        global counter
        global jumper
        value = counter
 
        htmlText = """<p><span style=" font-size:50pt;">{VALUE}</span><span style=" 
                    font-size:50pt; vertical-align:super;">%</span></p>"""
        newHtml = htmlText.replace("{VALUE}", str(jumper))

        if(value > jumper):
            self.ui.labelPercentage.setText(newHtml)
            jumper += 11
        if value >= 100:
            value = 1.000
        self.progressBarValue(value)
        
        if counter > 100:
            self.timer.stop()

            self.close()
            self.switch_window.emit()
        counter += 0.5
    def progressBarValue(self, value):

        styleSheet = """
        QFrame{
        	border-radius: 150px;
        	background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} 
            rgba(255, 0, 127, 0), stop:{STOP_2} rgba(85, 170, 255, 255));
        }
        """
        progress = (100 - value) / 100.0
        stop_1 = str(progress - 0.001)
        stop_2 = str(progress)
        newStylesheet = styleSheet.replace(
            "{STOP_1}", stop_1).replace("{STOP_2}", stop_2)
        self.ui.circularProgress.setStyleSheet(newStylesheet)
       
class Controller:
    def __init__(self):
        pass
    def show_load(self):
        self.l = SplashScreen()
        self.l.switch_window.connect(self.show_first)
        self.l.show()

    def show_first(self):
        self.f = FirstWindow()
        self.f.switch_window.connect(self.show_main)
        self.f.show()
        
    def show_main(self):
        self.w = MainWindow()        
        self.w.switch_window.connect(self.show_save)
        self.w.switch_rev_list_window.connect(self.show_review_list)
        self.w.show()
     
    def show_save(self):
        self.s = SaveWindow()
        self.s.portNNAMEinSAVE = self.get_port
        self.s.switch_window.connect(self.show_window_two)
        self.w.hide()
        self.s.show()

    def show_review_list(self):
        self.r_l = ReviewList()
        # self.r.switch_window.connect(self.show_window_rev)
        self.w.hide()
        self.r_l.show()
        self.r_l.switch_window.connect(self.show_main)
        self.r_l.switch_rev_window.connect(self.show_review)
    
    def show_review(self,text):
        self.r = RevWindow()
        self.r.on_combobox_func(text)
        self.r.show()
        self.r.switch_window.connect(self.show_review_list)

    def show_window_two(self, text):
        if text == "Enter here":
            self.s.close()
            self.show_main()
            
        else:
            self.w = MainWindow() 
            self.w.file_save(text)
            self.w.stop_btn.clicked.connect(self.w.Stop_saving)
            self.w.stop_btn.show()
            self.w.run_btn.setText('')
            self.w.run_btn.setIcon(QtGui.QIcon('run.png'))
            self.w.save_btn.setText("   SAVE AGAIN")
            self.w.run_btn.setToolTip('Start Saving')
            self.w.switch_window.connect(self.show_save)
            self.w.switch_rev_list_window.connect(self.show_review_list)
            self.s.close()
            self.w.com_lbl.setText('Seclect COM Port Again!')
            self.w.com_lbl.setStyleSheet( " color: #00bbff;"
                                    "background-color: #1d1f24;"
                                "selection-background-color: red;"
                                "border-radius: 10px;"
                                "font: bold 15px;"
                                "padding: 10px;"                                 
                                )
            self.w.setWindowTitle("Save Data Window")
            self.w.show()
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    controller.show_load()
    sys.exit(app.exec_())
