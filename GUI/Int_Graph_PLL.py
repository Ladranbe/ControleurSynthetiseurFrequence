# -*- coding: cp1252 -*-
import sys
import serial
import codecs
import re
import serial.tools.list_ports
import image_qrc

from PyQt4.QtGui import *
from PyQt4.QtCore import *

NIR_RANGE_MAX_BOUNDARY_MHZ = 3072       #Near Infrared frequency channel
NIR_RANGE_MIN_BOUNDARY_MHZ = 1472

UV_RANGE_MAX_BOUNDARY_MHZ = 2080
UV_RANGE_MIN_BOUNDARY_MHZ = 1040

VIS_RANGE_MAX_BOUNDARY_MHZ = 2496       #Visible light frequency channel
VIS_RANGE_MIN_BOUNDARY_MHZ = 1152

RF_REF_MIN_MHZ = 20
RF_REF_MAX_MHZ = 250

RF_PFD_MIN_KHZ = 40
RF_PFD_MAX_KHZ = 100000

def port_is_usable(port):
        #Vérifie si le port série peut être utilisé
        try:
                ser=serial.Serial(port)
                return True
        except serial.serialutil.SerialException:
                return False

def file_is_readable(txtFile):
        #Vérifie si le fichier peut-être lu
        try:
                open(txtFile,"r")
                return True
        except IOError:
                return False

def send_instructions(iLatch, fLatch, rLatch, abLatch, port):
    #La boucle "with..as..." permet d'ouvrir puis de fermer proprement
    #le port série utilisé
    if port_is_usable(port)==True:
            with serial.Serial(port) as ser :
                iLatch_toSend=iLatch.decode('hex')  #Converti la chaîne hexadécimale en séries de bytes
                fLatch_toSend=fLatch.decode('hex')  #avec 2 valeurs alphanumériques par octet
                rLatch_toSend=rLatch.decode('hex')
                abLatch_toSend=abLatch.decode('hex')
                
                ser.write(iLatch_toSend)            #Envoi de la trame sur le port série
                compteur=7
                while(compteur>0):                  #Boucle de temporisation pour s'assurer que la donnée
                      compteur=compteur-1           #précédente ait bien été envoyée
                ser.write(fLatch_toSend)
                compteur=7
                while(compteur>0):
                      compteur=compteur-1
                ser.write(rLatch_toSend)
                compteur=7
                while(compteur>0):
                      compteur=compteur-1
                ser.write(abLatch_toSend)
    else:
            QMessageBox.about(window,'Serial port error','Please check that the device is connected to the right port')
            return


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle("PLL Controller version 0.1")
        self.resize(800, 600)
        self.move(20,0)
        self.setWindowIcon(QIcon("logo3.png"))

        #Définition des listes contenant les items à placer dans les ComboBox (combinaison
        #d'un champ d'édition de texte et d'une liste déroulante)
        self.serialPorts=[]
        for port in serial.tools.list_ports.comports():
                if port[2] != 'n/a':
                        port_str=str(port[:2])
                        self.serialPorts.append(port_str.rstrip('\''))
        self.channels=['Near-infrared channel (NIR) - 1472-3072 MHz', 'UV channel - 1040-2080 MHz',\
                       'Visible light channel (VIS) - 1152-2496 MHz']
        self.prescalerValues=['8/9', '16/17', '32/33', '64/65']
        self.CPsetting=['0,625 mA', '1,25 mA', '1,875 mA', '2,5 mA', '3,125 mA', '3,75 mA', '4,375 mA', '5,0 mA']
        self.CPgain=['0', '1']
        self.CPoutput=['Normal','Three-state']
        self.fastlockMode=['Disabled', 'Mode 1', 'Mode 2']
        self.timeoutCycles=['3', '7', '11', '15', '19', '23', '27', '31', '35', '39', '43', '47',
                            '51', '55', '59', '63']
        self.PFDpolarity=['Negative', 'Positive']
        self.counterReset=['Disabled', 'Enabled']
        self.lockDetectPrecision=['3 cycles', '5 cycles']
        self.powerDown=['Normal operation', 'Asynchronous power-down', 'Synchronous power-down']
        self.abpw=['2,9 ns', '1,3 ns TEST MODE ONLY', '6,0 ns', '2,9 ns']
        self.muxout=['Three-state output', 'Digital lock detect', 'N divider output', 'DVDD',
                     'R divider output', 'Analog lock detect', 'Serial data output', 'DGND']

        #Création des LineEdit (lignes de champ de texte)
        self.rfref_line=QLineEdit()
        self.rfpfd_line=QLineEdit()
        self.spacingTab1_line=QLineEdit()
        self.startFreq_line=QLineEdit()
        self.startFreq_line.setFixedWidth(50)
        self.stopFreq_line=QLineEdit()
        self.stopFreq_line.setFixedWidth(50)
        self.spacingTab2_line=QLineEdit()
        self.spacingTab2_line.setFixedWidth(50)
        self.timeDelay_line=QLineEdit()
        self.timeDelay_line.setFixedWidth(50)

        #Création des PushButtons (boutons poussoirs)
        self.writePLL_button=QPushButton("Write PLL")
        self.writePLL_button.setFixedWidth(90)
        self.writePLL_button.setFixedHeight(35)
        self.autoSweep_button=QPushButton("Auto Sweep")
        self.autoSweep_button.setFixedWidth(90)
        self.autoSweep_button.setFixedHeight(35)
        self.stop_buttonTab1=QPushButton("Stop / Reset")
        self.stop_buttonTab1.setFixedWidth(90)
        self.stop_buttonTab1.setFixedHeight(35)
        self.quit_buttonTab1=QPushButton("Quit")
        self.quit_buttonTab1.setFixedWidth(50)
        self.quit_buttonTab1.setFixedHeight(35)
        self.load_buttonTab1=QPushButton("Load settings")
        self.load_buttonTab1.setFixedWidth(100)
        self.load_buttonTab1.setFixedHeight(35)
        self.save_buttonTab1=QPushButton("Save settings")
        self.save_buttonTab1.setFixedWidth(100)
        self.save_buttonTab1.setFixedHeight(35)
        self.stop_buttonTab2=QPushButton("Stop / Reset")
        self.stop_buttonTab2.setFixedWidth(90)
        self.stop_buttonTab2.setFixedHeight(35)
        self.start_button=QPushButton("Start")
        self.start_button.setFixedWidth(50)
        self.start_button.setFixedHeight(35)
        self.quit_buttonTab2=QPushButton("Quit")
        self.quit_buttonTab2.setFixedWidth(50)
        self.quit_buttonTab2.setFixedHeight(35)
        self.load_buttonTab2=QPushButton("Load settings")
        self.load_buttonTab2.setFixedWidth(100)
        self.load_buttonTab2.setFixedHeight(35)
        self.save_buttonTab2=QPushButton("Save settings")
        self.save_buttonTab2.setFixedWidth(100)
        self.save_buttonTab2.setFixedHeight(35)

        #Création des ProgressBar (barre de progression)
        self.autoSweep_progressbar=QProgressBar()
        self.autoSweep_progressbar.setGeometry(200, 80, 250, 20)
        self.autoSweep_progressbar.setTextVisible(True) #Afficher le pourcentage indiquant la progression
        self.sweep_progressbar=QProgressBar()
        self.sweep_progressbar.setFixedWidth(150)
        self.sweep_progressbar.setTextVisible(True)

        #Création d'un LCDNumber (zone d'affichage style écran LCD)
        self.timeRemaining_lcdnumber=QLCDNumber()
        self.timeRemaining_lcdnumber.setFixedWidth(120)
        self.timeRemaining_lcdnumber.setFixedHeight(60)
        self.timeRemaining_lcdnumber.setDigitCount(16)
        self.timeRemaining_lcdnumber.setSegmentStyle(QLCDNumber.Flat)

        #Création des SpinBox (zone de sélection numérique avec incrément/décrément)
        self.rfvco_spinbox=QDoubleSpinBox()     #Une DoubleSpinbox permet d'écrire des nombres flottants
        self.rfvco_spinbox.setFixedWidth(70)
        self.rfvco_spinbox.setFixedHeight(25)
        self.rfvco_spinbox.setRange(NIR_RANGE_MIN_BOUNDARY_MHZ,NIR_RANGE_MAX_BOUNDARY_MHZ)
        self.currentOutputFreqValue_spinbox=QDoubleSpinBox()
        self.currentOutputFreqValue_spinbox.setFixedWidth(80)
        self.currentOutputFreqValue_spinbox.setFixedHeight(25)
        self.currentOutputFreqValue_spinbox.setReadOnly(True)
        self.currentOutputFreqValue_spinbox.setRange(0,8000)
        self.currentOutputFreqValue_spinbox.setDecimals(4)

        #Création d'une police spécifique) pour les Label (libellé)
        font=QFont("Comic Sans MS", 10, QFont.Bold)

        #Création des labels
        self.writePLL_label=QLabel()    #Label vide car le texte du label sera écrit au moment opportun
        self.writePLL_label.setAlignment(Qt.AlignCenter)
        self.bcountValueTab1_label=QLabel()
        self.bcountValueTab1_label.setFont(font)     #Application de la police au label
        self.acountValueTab1_label=QLabel()
        self.acountValueTab1_label.setFont(font)
        self.ncountValueTab1_label=QLabel()
        self.ncountValueTab1_label.setFont(font)
        self.rcountValueTab1_label=QLabel()
        self.rcountValueTab1_label.setFont(font)
        self.bcountValueTab2_label=QLabel()
        self.bcountValueTab2_label.setFont(font)     #Application de la police au label
        self.acountValueTab2_label=QLabel()
        self.acountValueTab2_label.setFont(font)
        self.ncountValueTab2_label=QLabel()
        self.ncountValueTab2_label.setFont(font)
        self.rcountValueTab2_label=QLabel()
        self.rcountValueTab2_label.setFont(font)
        self.rCounterLatchValueTab1_label=QLabel()
        self.rCounterLatchValueTab1_label.setFont(font)
        self.abCounterLatchValueTab1_label=QLabel()
        self.abCounterLatchValueTab1_label.setFont(font)
        self.functionLatchValueTab1_label=QLabel()
        self.functionLatchValueTab1_label.setFont(font)
        self.initLatchValueTab1_label=QLabel()
        self.initLatchValueTab1_label.setFont(font)
        self.RFsettings_label=QLabel("RF Settings")
        self.RFsettings_label.setFont(font)
        self.rCounterLatchTab1_label=QLabel("R Counter Latch =")
        self.abCounterLatchTab1_label=QLabel("AB Counter Latch =")
        self.functionLatchTab1_label=QLabel("Function Latch =")
        self.initLatchTab1_label=QLabel("Initialization Latch =")
        self.rCounterLatchValueTab2_label=QLabel()
        self.rCounterLatchValueTab2_label.setFont(font)
        self.abCounterLatchValueTab2_label=QLabel()
        self.abCounterLatchValueTab2_label.setFont(font)
        self.functionLatchValueTab2_label=QLabel()
        self.functionLatchValueTab2_label.setFont(font)
        self.initLatchValueTab2_label=QLabel()
        self.initLatchValueTab2_label.setFont(font)
        self.rCounterLatchTab2_label=QLabel("R Counter Latch =")
        self.abCounterLatchTab2_label=QLabel("AB Counter Latch =")
        self.functionLatchTab2_label=QLabel("Function Latch =")
        self.initLatchTab2_label=QLabel("Initialization Latch =")
        self.settings_label=QLabel("Settings")
        self.settings_label.setFont(font)
        self.CPset1_label=QLabel("Charge Pump current setting 1 :")
        self.CPset2_label=QLabel("Charge Pump current setting 2 :")
        self.CPgain_label=QLabel("Charge Pump Gain :")
        self.CPoutput_label=QLabel("Charge Pump Output :")
        self.fastlockMode_label=QLabel("FastLock Mode :")
        self.timeout_label=QLabel("Timeout (in PFD cycles):")
        self.PFDpolarity_label=QLabel("Phase Detector Polarity :")
        self.counterReset_label=QLabel("Counter Reset :")
        self.lockDetectPrecision_label=QLabel("Lock Detect Precision:")
        self.powerDown_label=QLabel("Power Down :")
        self.abpw_label=QLabel("Antibacklash Pulse Width :")
        self.muxout_label=QLabel("MUXOUT :")
        self.frequencySweep_label=QLabel("Frequency sweep")
        self.frequencySweep_label.setFont(font)
        self.startFreq_label=QLabel("Start frequency (in MHz):")
        self.stopFreq_label=QLabel("Stop frequency (in MHz):")
        self.spacingTab2_label=QLabel("Spacing (in MHz);")
        self.timeDelay_label=QLabel("Time delay (in ms):")
        self.currentOutputFreq_label=QLabel("Current output frequency (in MHz):")
        self.timeRemaining_label=QLabel("Time remaining:")
        self.sweepCompleted_label=QLabel()
        
        #Création de toutes les ComboBox
        self.serialPorts_combobox=QComboBox()
        self.serialPorts_combobox.addItems(self.serialPorts)
        self.channel_combobox=QComboBox()
        self.channel_combobox.addItems(self.channels)
        self.prescaler_combobox=QComboBox()
        self.prescaler_combobox.addItems(self.prescalerValues)
        self.CPsetting1_combobox=QComboBox()
        self.CPsetting1_combobox.addItems(self.CPsetting)
        self.CPsetting2_combobox=QComboBox()
        self.CPsetting2_combobox.addItems(self.CPsetting)
        self.CPgain_combobox=QComboBox()
        self.CPgain_combobox.addItems(self.CPgain)
        self.CPoutput_combobox=QComboBox()
        self.CPoutput_combobox.addItems(self.CPoutput)
        self.fastlockMode_combobox=QComboBox()
        self.fastlockMode_combobox.addItems(self.fastlockMode)
        self.timeout_combobox=QComboBox()
        self.timeout_combobox.addItems(self.timeoutCycles)
        self.PFDpolarity_combobox=QComboBox()
        self.PFDpolarity_combobox.addItems(self.PFDpolarity)
        self.counterReset_combobox=QComboBox()
        self.counterReset_combobox.addItems(self.counterReset)
        self.lockDetectPrecision_combobox=QComboBox()
        self.lockDetectPrecision_combobox.addItems(self.lockDetectPrecision)
        self.powerDown_combobox=QComboBox()
        self.powerDown_combobox.addItems(self.powerDown)
        self.abpw_combobox=QComboBox()
        self.abpw_combobox.addItems(self.abpw)
        self.muxout_combobox=QComboBox()
        self.muxout_combobox.addItems(self.muxout)

        #Création de deux Tab (onglets) pour y stocker les objets créés
        self.tab=QTabWidget()
        self.tab1=QWidget()
        self.tab2=QWidget()

        #Ajouts de certains widgets (composants d'interface graphique) à layoutCounters
        #layoutCounters = layout de formulaire permettant d'afficher les valeurs des compteurs R, N, A et B
        #dans le deuxième onglet de la fenêtre
        self.layoutCounters=QFormLayout()
        self.layoutCounters.addRow("N Counter =", self.ncountValueTab2_label)
        self.layoutCounters.addRow("R counter =", self.rcountValueTab2_label)
        self.layoutCounters.addRow("B Counter =", self.bcountValueTab2_label)
        self.layoutCounters.addRow("A Counter =", self.acountValueTab2_label)
        self.layoutCounters.setSpacing(10)

        #Ajouts de widgets (composants d'interface graphique) à layoutFL
        #layoutFL = layout de formulaire pour la partie gauche de la fenêtre du premier onglet
        #Un layout de formulaire permet de créer un label et de positionner le widget juste à côté
        self.layoutFL=QFormLayout()
        self.layoutFL.addRow("Serial Port :",self.serialPorts_combobox)
        self.layoutFL.addRow(self.RFsettings_label)
        self.layoutFL.addRow("Channel :", self.channel_combobox)
        self.layoutFL.addRow("Reference Frequency (in MHz):", self.rfref_line)
        self.layoutFL.addRow("Channel Spacing (in kHz):", self.spacingTab1_line)
        self.layoutFL.addRow("RF VCO Output Frequency (in MHz):", self.rfvco_spinbox)
        self.layoutFL.addRow("PFD Frequency (in kHz):", self.rfpfd_line)
        self.layoutFL.addRow("Prescaler :", self.prescaler_combobox)
        self.layoutFL.addRow("N Counter =", self.ncountValueTab1_label)
        self.layoutFL.addRow("R counter =", self.rcountValueTab1_label)
        self.layoutFL.addRow("B Counter =", self.bcountValueTab1_label)
        self.layoutFL.addRow("A Counter =", self.acountValueTab1_label)
        self.layoutFL.setVerticalSpacing(13)        #Espacement vertical des éléments
        self.layoutFL.setHorizontalSpacing(13)      #Espacement horizontal des éléments
        
        #Ajouts de widgets à layoutGR.
        #layoutGR = layout sous forme de grille contenant les éléments affichés dans la partie droite de la fenêtre du premier onglet.
        #Un layout de grille permet de sélectionner une ligne ainsi qu'une colonne précises pour positionner un widget.
        self.layoutGR=QGridLayout()
        self.layoutGR.setVerticalSpacing(35)
        self.layoutGR.setHorizontalSpacing(15)
        self.layoutGR.addWidget(self.settings_label, 0, 0, Qt.AlignTop)
        self.layoutGR.addWidget(self.CPset1_label, 1, 0)
        self.layoutGR.addWidget(self.CPsetting1_combobox, 1, 1)
        self.layoutGR.addWidget(self.CPset2_label, 2, 0)
        self.layoutGR.addWidget(self.CPsetting2_combobox, 2, 1)
        self.layoutGR.addWidget(self.CPgain_label, 3, 0)
        self.layoutGR.addWidget(self.CPgain_combobox, 3, 1)
        self.layoutGR.addWidget(self.CPoutput_label, 4, 0)
        self.layoutGR.addWidget(self.CPoutput_combobox, 4, 1)
        self.layoutGR.addWidget(self.fastlockMode_label, 5, 0)
        self.layoutGR.addWidget(self.fastlockMode_combobox, 5, 1)
        self.layoutGR.addWidget(self.timeout_label, 6, 0)
        self.layoutGR.addWidget(self.timeout_combobox, 6, 1)
        self.layoutGR.addWidget(self.PFDpolarity_label, 7, 0)
        self.layoutGR.addWidget(self.PFDpolarity_combobox, 7, 1)
        self.layoutGR.addWidget(self.counterReset_label, 1, 2)
        self.layoutGR.addWidget(self.counterReset_combobox, 1, 3)
        self.layoutGR.addWidget(self.lockDetectPrecision_label, 2, 2)
        self.layoutGR.addWidget(self.lockDetectPrecision_combobox, 2, 3)
        self.layoutGR.addWidget(self.powerDown_label, 3, 2)
        self.layoutGR.addWidget(self.powerDown_combobox, 3, 3)
        self.layoutGR.addWidget(self.abpw_label, 4, 2)
        self.layoutGR.addWidget(self.abpw_combobox, 4, 3)
        self.layoutGR.addWidget(self.muxout_label, 5, 2)
        self.layoutGR.addWidget(self.muxout_combobox, 5, 3)

        #Ajouts de widgets à layoutTab2
        #layoutTab2 = layout sous forme de grille contenant une partie des éléments à afficher dans le deuxième onglet de la fenêtre
        self.layoutTab2=QGridLayout()
        self.layoutTab2.setVerticalSpacing(25)
        self.layoutTab2.setHorizontalSpacing(10)
        self.layoutTab2.addWidget(self.frequencySweep_label,0,0)
        self.layoutTab2.addWidget(self.startFreq_label,1,0)
        self.layoutTab2.addWidget(self.startFreq_line,1,1)
        self.layoutTab2.addWidget(self.stopFreq_label,2,0)
        self.layoutTab2.addWidget(self.stopFreq_line,2,1)
        self.layoutTab2.addWidget(self.spacingTab2_label,3,0)
        self.layoutTab2.addWidget(self.spacingTab2_line,3,1)
        self.layoutTab2.addWidget(self.timeDelay_label,4,0)
        self.layoutTab2.addWidget(self.timeDelay_line,4,1)
        self.layoutTab2.addWidget(self.currentOutputFreq_label,5,0)
        self.layoutTab2.addWidget(self.currentOutputFreqValue_spinbox,5,1)
        self.layoutTab2.addWidget(self.sweep_progressbar,6,0)
        self.layoutTab2.addWidget(self.sweepCompleted_label,6,1)
        self.layoutTab2.addWidget(self.timeRemaining_label,7,0)
        self.layoutTab2.addWidget(self.timeRemaining_lcdnumber,7,1)
        self.layoutTab2.addWidget(self.start_button,8,0)
        self.layoutTab2.addWidget(self.stop_buttonTab2,8,1)

        #Création d'un layout spécifique pour 3 PushButton et 1 label
        self.button_box=QVBoxLayout()   #Layout de type "disposition verticale"
        self.button_box.addStretch(1)   #Permet de placer le bouton tout à droite de la fenêtre
        self.button_box.addWidget(self.writePLL_button)
        self.button_box.addWidget(self.writePLL_label)
        self.button_box.addWidget(self.autoSweep_button)
        self.button_box.addWidget(self.stop_buttonTab1)
        self.button_box.addWidget(self.autoSweep_progressbar)
        self.stop_buttonTab1.setVisible(False) #Ne sera pas affiché tout de suite
        self.autoSweep_progressbar.setVisible(False)
        self.button_box.setSpacing(5)

        #Création d'un layout spécifique pour 3 PushButtons (load, save et quit) pour le premier onglet
        self.buttonsTab1_layout=QGridLayout()
        self.buttonsTab1_layout.addWidget(self.load_buttonTab1,0,0,Qt.AlignLeft)
        self.buttonsTab1_layout.addWidget(self.save_buttonTab1,1,0,Qt.AlignLeft)
        self.buttonsTab1_layout.addWidget(self.quit_buttonTab1,1,1,Qt.AlignRight)

        #Idem pour le deuxième onglet
        self.buttonsTab2_layout=QGridLayout()
        self.buttonsTab2_layout.addWidget(self.load_buttonTab2,0,0,Qt.AlignLeft)
        self.buttonsTab2_layout.addWidget(self.save_buttonTab2,1,0,Qt.AlignLeft)
        self.buttonsTab2_layout.addWidget(self.quit_buttonTab2,1,1,Qt.AlignRight)

        #Layout de grille pour afficher le contenu des registres de la PLL dans le premier onglet
        self.layoutLatchTab1=QGridLayout()
        self.layoutLatchTab1.addWidget(self.initLatchTab1_label, 0, 0)
        self.layoutLatchTab1.addWidget(self.initLatchValueTab1_label, 0, 1)
        self.layoutLatchTab1.addWidget(self.functionLatchTab1_label, 1, 0)
        self.layoutLatchTab1.addWidget(self.functionLatchValueTab1_label, 1, 1)
        self.layoutLatchTab1.addWidget(self.rCounterLatchTab1_label, 2, 0)
        self.layoutLatchTab1.addWidget(self.rCounterLatchValueTab1_label, 2, 1)
        self.layoutLatchTab1.addWidget(self.abCounterLatchTab1_label, 3, 0)
        self.layoutLatchTab1.addWidget(self.abCounterLatchValueTab1_label, 3, 1)
        self.layoutLatchTab1.setAlignment(Qt.AlignCenter)   #Permet d'aligner le layout au milieu de la fenêtre
        self.layoutLatchTab1.setVerticalSpacing(7)

        #Layout de grille pour afficher le contenu des registres de la PLL dans le deuxième onglet
        self.layoutLatchTab2=QGridLayout()
        self.layoutLatchTab2.addWidget(self.initLatchTab2_label, 0, 0)
        self.layoutLatchTab2.addWidget(self.initLatchValueTab2_label, 0, 1)
        self.layoutLatchTab2.addWidget(self.functionLatchTab2_label, 1, 0)
        self.layoutLatchTab2.addWidget(self.functionLatchValueTab2_label, 1, 1)
        self.layoutLatchTab2.addWidget(self.rCounterLatchTab2_label, 2, 0)
        self.layoutLatchTab2.addWidget(self.rCounterLatchValueTab2_label, 2, 1)
        self.layoutLatchTab2.addWidget(self.abCounterLatchTab2_label, 3, 0)
        self.layoutLatchTab2.addWidget(self.abCounterLatchValueTab2_label, 3, 1)
        self.layoutLatchTab2.setVerticalSpacing(0)

        #Ajouts des layouts layoutFL, layout GD et button_box au layoutH1 (horizontal) du premier onglet
        #pour que layoutFL, layoutGR et button_box soient placés l'un à côté de l'autre dans tab1
        self.layoutH1=QHBoxLayout()
        self.layoutH1.addLayout(self.layoutFL)
        self.layoutH1.setSpacing(20)     #Pour espacer les layouts entre eux
        self.layoutH1.addLayout(self.layoutGR)
        self.layoutH1.addStretch(1)
        self.layoutH1.addLayout(self.button_box)

        #Ajouts des layouts layoutCounters et layoutLatchTab2 au layoutH2 du deuxième onglet
        self.layoutH2=QHBoxLayout()
        self.layoutH2.addLayout(self.layoutCounters,Qt.AlignCenter)
        self.layoutH2.addLayout(self.layoutLatchTab2,Qt.AlignCenter)
        self.layoutH2.addStretch(1)
        self.layoutH2.setSpacing(10)
        self.layoutH2.setAlignment(Qt.AlignCenter)
        
        #Ajouts des layouts au layout du 1er onglet layoutV1 (vertical)
        self.layoutV1=QVBoxLayout(self.tab1) #On renseigne ici que le layout sera celui du premier onglet
        self.layoutV1.addLayout(self.layoutH1)
        self.layoutV1.addLayout(self.layoutLatchTab1)
        self.layoutV1.setSpacing(10)
        self.layoutV1.addLayout(self.buttonsTab1_layout)

        self.tab.addTab(self.tab1,"Main settings") #Ajout de tab1 au TabWidget

        #Ajouts des layouts layoutTab2 et layoutH2 au layout principal du deuxième onglet layoutV2
        self.layoutV2=QVBoxLayout(self.tab2)
        self.layoutV2.addLayout(self.layoutTab2)
        self.layoutV2.addLayout(self.layoutH2)
        self.layoutV2.addStretch(3)
        self.layoutV2.addLayout(self.buttonsTab2_layout)
        
        self.tab.addTab(self.tab2,"Sweep") #Ajout du tab2 au TabWidget
        
        #Layout principal contenant uniquement les 2 onglets
        self.lay=QVBoxLayout()
        self.lay.addWidget(self.tab)


        self.setLayout(self.lay)    #On renseigne ici quel layout devra être utilisé par
                                    #la classe principale

        #Connexion des signaux émis par certains widgets
        self.connect(self.writePLL_button, SIGNAL("clicked()"), self.writePLLbutton_clicked_event)
        self.connect(self.rfpfd_line, SIGNAL("textChanged(QString)"), self.spacingTab1_line.setText)
        self.connect(self.spacingTab1_line, SIGNAL("textChanged(QString)"), self.rfpfd_line.setText)
        self.connect(self.save_buttonTab1, SIGNAL("clicked()"), self.saveButton_clicked_event)
        self.connect(self.save_buttonTab2, SIGNAL("clicked()"), self.saveButton_clicked_event)
        self.connect(self.load_buttonTab1, SIGNAL("clicked()"), self.loadButton_clicked_event)
        self.connect(self.load_buttonTab2, SIGNAL("clicked()"), self.loadButton_clicked_event)
        self.connect(self.channel_combobox, SIGNAL("currentIndexChanged (int)"), self.channelCombobox_changed_event)
        self.connect(self.spacingTab1_line, SIGNAL("textEdited (QString)"), self.channel_spacing_changed_event)
        self.connect(self.quit_buttonTab1, SIGNAL("clicked()"), self.quit_button_clicked_event)
        self.connect(self.quit_buttonTab2, SIGNAL("clicked()"), self.quit_button_clicked_event)
        self.connect(self.autoSweep_button, SIGNAL('clicked()'), self.autoSweep_button_clicked_event)
        self.connect(self.stop_buttonTab1, SIGNAL('clicked()'), self.stop_buttonTab1_clicked_event)
        self.connect(self.start_button, SIGNAL('clicked()'), self.start_button_clicked_event)
        self.connect(self.stop_buttonTab2, SIGNAL('clicked()'), self.stop_buttonTab2_clicked_event)

        #Dès qu'un changement de valeur survient dans un objet,
        #il faut mettre à jour le label correspondant au bouton "Write PLL"
        self.connect(self.channel_combobox, SIGNAL("currentIndexChanged (int)"), self.update_writePLL_button_label)
        self.connect(self.rfref_line, SIGNAL("textChanged(QString"), self.update_writePLL_button_label)
        self.connect(self.spacingTab1_line, SIGNAL("textChanged(QString)"), self.update_writePLL_button_label)
        self.connect(self.rfvco_spinbox, SIGNAL("valueChanged(double)"), self.update_writePLL_button_label)
        self.connect(self.rfpfd_line, SIGNAL("textChanged(QString)"), self.update_writePLL_button_label)
        self.connect(self.prescaler_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.CPsetting1_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.CPsetting2_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.CPgain_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.CPoutput_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.fastlockMode_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.timeout_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.PFDpolarity_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.counterReset_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.lockDetectPrecision_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.powerDown_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.abpw_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.muxout_combobox, SIGNAL("currentIndexChanged(int)"), self.update_writePLL_button_label)
        self.connect(self.load_buttonTab1, SIGNAL("clicked()"), self.update_writePLL_button_label)
        self.connect(self.autoSweep_button, SIGNAL("clicked()"), self.update_writePLL_button_label)

    def writePLLbutton_clicked_event(self):
        self.stop_buttonTab1.setVisible(False)      #On s'assure que le bouton soit caché
        self.autoSweep_progressbar.setVisible(False) #Idem pour pour la barre de progression

        #On vérifie qu'il y ai bien un port série de sélectionné
        if str(self.serialPorts_combobox.currentText())=='':    #S'il n'y a pas de port série affiché dans la combo box, une erreur est renvoyée
                QMessageBox.about(self, 'Error : serial port',\
                'No USB device seems to be connected to your computer.')
                return
        else:   #Sinon, on récupère le numéro du port série à utiliser
                serial_port="COM"+(str(self.serialPorts_combobox.currentText())[5])+":" #Format "COMx:"
        
        rfvco_mhz=self.rfvco_spinbox.value()    #Récupération de la valeur de la SpinBox
        rfvco_hz=int(rfvco_mhz * 1e6)
            
        rfref_mhz=self.rfref_line.text()    #Récupération de la valeur du champ de texte
        if re.match("[0-9]{2,3}(?![\d.])",rfref_mhz)!=None:  #On vérifie que la chaîne entrée est bien un entier
                                                    #sur 2 à 3 chiffres
            
                rfref_mhz=int(rfref_mhz)            #Conversion de la chaîne de caractères en entier
                
                #La valeur doit se situer dans un intervalle précis, si elle n'y est pas contenue,
                #une boite de dialogue indiquant une erreur est renvoyée
                if (rfref_mhz<RF_REF_MIN_MHZ or rfref_mhz>RF_REF_MAX_MHZ):
                        QMessageBox.about(self, 'Error : incompatible string format',\
                        'Input for Reference Frequency can only be between 20 and 250 MHz')
                        return #Sortie de la fonction pour ne pas exécuter toutes les prochaines
                               #instructions
                        
                #Si tout est bon, la valeur en MHz est convertie en Hz pour la suite
                else:
                        rfref_hz=int(rfref_mhz * 1e6)
                        
        #Si la chaine entrée n'est pas un entier sur 4 chiffres, une erreur est renvoyée        
        else:
                QMessageBox.about(self, 'Error : incompatible string format',\
                'Input for Reference Frequency can only be a 2 or 3 digits number')
                return

        rfpfd_khz=self.rfpfd_line.text()
        if re.match("[0-9]{1,5}(0)(?![\d.])",rfpfd_khz)!=None:   #On vérifie que la chaîne entrée est bien un
                                                        #entier ayant de 1 à 5 chiffres et se terminant
                                                        #par un 0 (nombre rond)
            
                rfpfd_khz=int(rfpfd_khz)    #Conversion de la chaîne de caractères en entier

                #La valeur doit se situer dans un intervalle précis, si elle n'y est pas contenue,
                #une boite de dialogue indiquant une erreur est renvoyée
                if (rfpfd_khz < RF_PFD_MIN_KHZ or rfpfd_khz > RF_PFD_MAX_KHZ or rfpfd_khz % 10 != 0):
                        QMessageBox.about(self, 'Error : incompatible string format',\
                        'Input for PFD Frequency can only be between 40 and 100 000 kHz (round number)')
                        return

                #Si tout est bon, la valeur en kHz est convertie en Hz pour la suite
                else:
                        rfpfd_hz=int(rfpfd_khz*1e3)
                        channelSpac=rfpfd_hz

        #Si la chaîne entrée ne correspond pas à l'expression régulière, une erreur est renvoyée
        else:
                QMessageBox.about(self, 'Error : incompatible string format',\
                'Input for PFD Frequency can only be a 2 - 6 digits round number')
                return

        prescaler_currentIndex=self.prescaler_combobox.currentIndex() #Répération de l'indice courant
                                                                      #de la ComboBox
        
        #Suivant la valeur de l'indice récupéré, on en déduit la valeur du prédiviseur
        if prescaler_currentIndex==0:
                prescaler=8
        elif prescaler_currentIndex==1:
                prescaler=16
        elif prescaler_currentIndex==2:
                prescaler=32
        else:
                prescaler=64

        r_counter = int(rfref_hz/channelSpac)   #Calculs provenant de la datasheet de la PLL
        n_counter = int(rfvco_hz/rfpfd_hz)
        b_counter = int(n_counter/prescaler)
        a_counter = n_counter%prescaler
        self.rcountValueTab1_label.setText(str(r_counter))   #On indique les valeurs des compteurs
        self.ncountValueTab1_label.setText(str(n_counter))   #dans leurs labels respectifs
        self.bcountValueTab1_label.setText(str(b_counter))
        self.acountValueTab1_label.setText(str(a_counter))

        CPset1=self.CPsetting1_combobox.currentIndex()
        CPset2=self.CPsetting2_combobox.currentIndex()

        CPgain=self.CPgain_combobox.currentIndex()

        CPoutput=self.CPoutput_combobox.currentIndex()

        fastlock=self.fastlockMode_combobox.currentIndex()

        timer_counter=self.timeout_combobox.currentIndex()

        pfd_polarity=self.PFDpolarity_combobox.currentIndex()

        counter_reset=self.counterReset_combobox.currentIndex()

        lockDetect_precision=self.lockDetectPrecision_combobox.currentIndex()

        power_down=self.powerDown_combobox.currentIndex()
        
        #Power-down est une valeur sur 2 bits qu'il faut découper en deux variables distinctes
        if power_down==0:
                power_down2=0
                power_down1=0
        elif power_down==1:
                power_down2=0
                power_down1=1
        else:
                power_down2=1
                power_down1=1

        abpw=self.abpw_combobox.currentIndex()

        muxout=self.muxout_combobox.currentIndex()

        #On concatène les valeurs binaires obtenues pour former le registre de 24 bits à envoyer à la PLL
        function_latch_b="{0:02b}".format(prescaler_currentIndex)+"{0:1b}".format(power_down2)\
                          +"{0:03b}".format(CPset2)+"{0:03b}".format(CPset1)+"{0:04b}".format(timer_counter)+\
                          "{0:02b}".format(fastlock)+"{0:1b}".format(CPoutput)+"{0:1b}".format(pfd_polarity)+\
                         "{0:03b}".format(muxout)+"{0:1b}".format(power_down1)+"{0:1b}".format(counter_reset)+'10'

        #Le registre d'initialisation est le même que le registre précédent à l'exception
        #des deux derniers bits (bits de contrôle)
        initialization_latch_b=function_latch_b[0:22]+'11'

        r_counter_latch_b='000'+"{0:1b}".format(lockDetect_precision)+'00'+"{0:02b}".format(abpw)+\
                           "{0:014b}".format(r_counter)+'00'
        
        ab_counter_latch_b='00'+"{0:1b}".format(CPgain)+"{0:013b}".format(b_counter)+"{0:06b}".format(a_counter)+'01'

        #On converti les valeurs binaires des registres en valeur hexadécimale sur 6 données
        #alphanumériques
        function_latch_hex='%06x' % int(function_latch_b, 2)
        initialization_latch_hex='%06x' % int(initialization_latch_b, 2)
        r_counter_latch_hex='%06x' % int(r_counter_latch_b, 2)
        ab_counter_latch_hex='%06x' % int(ab_counter_latch_b, 2)

        #On affiche les valeurs des registres dans leurs labels respectifs
        #On fait précéder les valeurs hexa par un "Ox" pour plus de clarté
        #On met également les lettres en majuscules pour l'esthétique
        self.functionLatchValueTab1_label.setText("0x"+str(function_latch_hex).upper())
        self.initLatchValueTab1_label.setText("0x"+str(initialization_latch_hex).upper())
        self.rCounterLatchValueTab1_label.setText("0x"+str(r_counter_latch_hex).upper())
        self.abCounterLatchValueTab1_label.setText("0x"+str(ab_counter_latch_hex).upper())
        
        #Appel de la fonction permettant l'envoi des registres sur le port série
        send_instructions(initialization_latch_hex, function_latch_hex, r_counter_latch_hex, ab_counter_latch_hex, serial_port)

        #Si on arrive jusqu'ici, c'est que les registres ont été fournis à la fonction
        #d'envoi donc on peut afficher le label sous le bouton "Write PLL"
        self.writePLL_label.setText("Data processed")


    def autoSweep_button_clicked_event(self):
        self.update_writePLL_button_label()
        self.stop_buttonTab1.setVisible(True) #Affichage du bouton "Stop"
        self.autoSweep_progressbar.setVisible(True) #Affichage de la barre de progression

        #On vérifie qu'il y ai bien un port série sélectionné
        if str(self.serialPorts_combobox.currentText())=='':    #S'il n'y a pas de port série affiché dans la combo box une erreur est renvoyée
                QMessageBox.about(self, 'Error : serial port',\
                'No USB device seems to be connected to your computer.')
                self.timer1.stop()
                return
        else:   #Sinon, on récupère le numéro du port série à utiliser
                serial_port="COM"+(str(self.serialPorts_combobox.currentText())[5])+":" #Format "COMx:"
        
        rfvco_mhz=self.rfvco_spinbox.value()    #Récupération de la valeur de la SpinBox
        rfvco_hz=int(rfvco_mhz * 1e6)
            
        rfref_mhz=self.rfref_line.text()    #Récupération de la valeur du champ de texte
        if re.match("[0-9]{2,3}(?![\d.])",rfref_mhz)!=None:  #On vérifie que la chaîne entrée est bien un entier
                                                    #sur 4 chiffres
            
                rfref_mhz=int(rfref_mhz)            #Conversion de la chaîne de caractères en entier
                
                #La valeur doit se situer dans un intervalle précis, si elle n'y est contenue,
                #une boite de dialogue indiquant une erreur est renvoyée
                if (rfref_mhz<RF_REF_MIN_MHZ or rfref_mhz>RF_REF_MAX_MHZ):
                        QMessageBox.about(self, 'Error : incompatible string format',\
                        'Input for Reference Frequency can only be between 20 and 250 MHz')
                        self.timer1.stop()
                        return
                        
                        
                #Si tout est bon, la valeur en MHz est convertie en Hz pour la suite
                else:
                        rfref_hz=int(rfref_mhz * 1e6)
                        
        #Si la chaine entrée n'est pas un entier sur 4 chiffres, une erreur est renvoyée        
        else:
                QMessageBox.about(self, 'Error : incompatible string format',\
                'Input for Reference Frequency can only be a 2 or 3 digits number')
                self.timer1.stop()
                return

        rfpfd_khz=self.rfpfd_line.text()
        if re.match("[0-9]{1,5}(0)(?![\d.])",rfpfd_khz)!=None:   #On vérifie que la chaîne entrée est bien un
                                                        #entier ayant de 1 à 5 chiffres et se terminant
                                                        #par un 0 (nombre rond)
            
                rfpfd_khz=int(rfpfd_khz)    #Conversion de la chaîne de caractères en integer

                #La valeur doit se situer dans un intervalle précis, si elle n'y est contenue,
                #une boite de dialogue indiquant une erreur est renvoyée
                if (rfpfd_khz < RF_PFD_MIN_KHZ or rfpfd_khz > RF_PFD_MAX_KHZ or rfpfd_khz % 10 != 0):
                        QMessageBox.about(self, 'Error : incompatible string format',\
                        'Input for PFD Frequency can only be between 40 and 100 000 kHz (round number)')
                        self.timer1.stop()
                        return

                #Si tout est bon, la valeur en kHz est convertie en Hz pour la suite
                else:
                        rfpfd_hz=int(rfpfd_khz*1e3)
                        channelSpac=rfpfd_hz

        #Si la chaîne entrée ne correspond pas à l'expression régulière, une erreur est renvoyée
        else:
                QMessageBox.about(self, 'Error : incompatible string format',\
                'Input for PFD Frequency can only be a 2 - 6 digits round number')
                self.timer1.stop()
                return

        prescaler_currentIndex=self.prescaler_combobox.currentIndex() #Répération de l'indice courant
                                                                      #de la ComboBox
        
        #Suivant la valeur de l'indice récupéré, on en déduit la valeur du prédiviseur
        if prescaler_currentIndex==0:
                prescaler=8
        elif prescaler_currentIndex==1:
                prescaler=16
        elif prescaler_currentIndex==2:
                prescaler=32
        else:
                prescaler=64

        r_counter = int(rfref_hz/channelSpac)   #Calculs provenant de la datasheet de la PLL
        n_counter = int(rfvco_hz/rfpfd_hz)
        b_counter = int(n_counter/prescaler)
        a_counter = n_counter%prescaler
        self.rcountValueTab1_label.setText(str(r_counter))   #On indique les valeurs des compteurs
        self.ncountValueTab1_label.setText(str(n_counter))   #dans leurs labels respectifs
        self.bcountValueTab1_label.setText(str(b_counter))
        self.acountValueTab1_label.setText(str(a_counter))

        CPset1=self.CPsetting1_combobox.currentIndex()
        CPset2=self.CPsetting2_combobox.currentIndex()

        CPgain=self.CPgain_combobox.currentIndex()

        CPoutput=self.CPoutput_combobox.currentIndex()

        fastlock=self.fastlockMode_combobox.currentIndex()

        timer_counter=self.timeout_combobox.currentIndex()

        pfd_polarity=self.PFDpolarity_combobox.currentIndex()

        counter_reset=self.counterReset_combobox.currentIndex()

        lockDetect_precision=self.lockDetectPrecision_combobox.currentIndex()

        power_down=self.powerDown_combobox.currentIndex()
        
        #Power-down est une valeur sur 2 bits qu'il faut découper en deux variables distinctes
        if power_down==0:
                power_down2=0
                power_down1=0
        elif power_down==1:
                power_down2=0
                power_down1=1
        else:
                power_down2=1
                power_down1=1

        abpw=self.abpw_combobox.currentIndex()

        muxout=self.muxout_combobox.currentIndex()

        #On concatène les valeurs binaires obtenues pour former le registre à envoyer à la PLL
        function_latch_b="{0:02b}".format(prescaler_currentIndex)+"{0:1b}".format(power_down2)\
                          +"{0:03b}".format(CPset2)+"{0:03b}".format(CPset1)+"{0:04b}".format(timer_counter)+\
                          "{0:02b}".format(fastlock)+"{0:1b}".format(CPoutput)+"{0:1b}".format(pfd_polarity)+\
                         "{0:03b}".format(muxout)+"{0:1b}".format(power_down1)+"{0:1b}".format(counter_reset)+'10'

        #Le registre d'initialisation est le même que le registre précédent à l'exception
        #des deux derniers bits
        initialization_latch_b=function_latch_b[0:22]+'11'

        r_counter_latch_b='000'+"{0:1b}".format(lockDetect_precision)+'00'+"{0:02b}".format(abpw)+\
                           "{0:014b}".format(r_counter)+'00'
        
        ab_counter_latch_b='00'+"{0:1b}".format(CPgain)+"{0:013b}".format(b_counter)+"{0:06b}".format(a_counter)+'01'

        #On converti les valeurs binaires des registres en valeur hexadécimale sur 6 données
        #alphanumériques
        function_latch_hex='%06x' % int(function_latch_b, 2)
        initialization_latch_hex='%06x' % int(initialization_latch_b, 2)
        r_counter_latch_hex='%06x' % int(r_counter_latch_b, 2)
        ab_counter_latch_hex='%06x' % int(ab_counter_latch_b, 2)

        #On affiche les valeurs des registres dans leurs labels respectifs
        #On fait précéder les valeurs hexa par un "Ox" pour plus de clarté
        #On met également les lettres en majuscules pour l'esthétique
        self.functionLatchValueTab1_label.setText("0x"+str(function_latch_hex).upper())
        self.initLatchValueTab1_label.setText("0x"+str(initialization_latch_hex).upper())
        self.rCounterLatchValueTab1_label.setText("0x"+str(r_counter_latch_hex).upper())
        self.abCounterLatchValueTab1_label.setText("0x"+str(ab_counter_latch_hex).upper())
        
        #Appel de la fonction permettant l'envoi des registres sur le port série
        send_instructions(initialization_latch_hex, function_latch_hex, r_counter_latch_hex, ab_counter_latch_hex, serial_port)

        #Une fois que les instructions ont été envoyées une première fois,
        #on incrémente la fréquence de sortie
        self.rfvco_spinbox.setValue(rfvco_mhz+(channelSpac*1e-6))

        #On affiche la progression de la manoeuvre avec la ProgressBar
        self.autoSweep_progressbar.setRange(self.rfvco_spinbox.minimum(),self.rfvco_spinbox.maximum())
        self.autoSweep_progressbar.setValue(rfvco_mhz)

        #Si la valeur max de la spinbox est atteinte, le timer peut être arrêté
        if self.rfvco_spinbox.value()==self.rfvco_spinbox.maximum():
                self.timer1.stop()
        else: #Sinon, relance du timer
                self.frequency_autoSweep()

    def frequency_autoSweep(self):
        self.timer1=QTimer()

        #Dès que le compteur fini de compter, on appelle la fonction "autoSweep_button_clicked_event"
        self.connect(self.timer1, SIGNAL("timeout()"), self.autoSweep_button_clicked_event)
        self.timer1.start(2 * 1000) #Le timer compte 2 secondes

    def stop_buttonTab1_clicked_event(self):
        if self.timer1.isActive()==True:
                self.timer1.stop() #Arrêt du timer sur appui du bouton "Stop"
        #self.autoSweep_progressbar.setValue(0)
        #self.autoSweep_progressbar.setVisible(False)
        self.autoSweep_progressbar.reset()
        self.rfvco_spinbox.setValue(self.rfvco_spinbox.minimum())

        self.ncountValueTab1_label.setText('');
        self.rcountValueTab1_label.setText('');
        self.bcountValueTab1_label.setText('');
        self.acountValueTab1_label.setText('');

        self.initLatchValueTab1_label.setText('');
        self.functionLatchValueTab1_label.setText('');
        self.rCounterLatchValueTab1_label.setText('');
        self.abCounterLatchValueTab1_label.setText('');
        
    def saveButton_clicked_event(self):
        #Ouverture d'une petite fenêtre de dialogue contenant uniquement 2 bouttons et un champ de texte
        #pour entrer un nom de fichier dans lequel seront sauvegardés les paramètres
        text, ok = QInputDialog.getText(self, 'Save settings', 
        'Enter file name :')
        
        if ok and text != '':  #Récupération du nom entré par l'utilisateur
                self.saveFile = str(text)+".txt"
                
        else :  #Si la ligne de texte est vide ou si l'on appui sur "cancel", une error est affichée
                QMessageBox.about(self,'Error','Unable to save settings as no output file name has been chosen')
                return
                
        #La boucle "with...as..." permet d'ouvrir puis de fermer proprement le fichier
        with open(self.saveFile,"w") as fichier: #Le "w" indique qu'on ouvre le fichier en écriture
            fichier.write(str(self.channel_combobox.currentIndex()))    #On écrit ensuite toutes les données
            fichier.write("\n"+self.rfref_line.text())                  #dans le fichier
            fichier.write("\n"+str(self.rfvco_spinbox.value()))
            fichier.write("\n"+self.rfpfd_line.text())
            fichier.write("\n"+str(self.prescaler_combobox.currentIndex()))
            fichier.write("\n"+str(self.CPsetting1_combobox.currentIndex()))
            fichier.write("\n"+str(self.CPsetting2_combobox.currentIndex()))
            fichier.write("\n"+str(self.CPgain_combobox.currentIndex()))
            fichier.write("\n"+str(self.CPoutput_combobox.currentIndex()))
            fichier.write("\n"+str(self.fastlockMode_combobox.currentIndex()))
            fichier.write("\n"+str(self.timeout_combobox.currentIndex()))
            fichier.write("\n"+str(self.PFDpolarity_combobox.currentIndex()))
            fichier.write("\n"+str(self.counterReset_combobox.currentIndex()))
            fichier.write("\n"+str(self.lockDetectPrecision_combobox.currentIndex()))
            fichier.write("\n"+str(self.powerDown_combobox.currentIndex()))
            fichier.write("\n"+str(self.abpw_combobox.currentIndex()))
            fichier.write("\n"+str(self.muxout_combobox.currentIndex()))
            fichier.write("\n"+self.startFreq_line.text())
            fichier.write("\n"+self.stopFreq_line.text())
            fichier.write("\n"+self.spacingTab2_line.text())
            fichier.write("\n"+self.timeDelay_line.text())

        #Les paramètres étant sauvegardés, on peut afficher un petit message
        #pour l'utilisateur
        QMessageBox.about(self, 'Success', 'Settings successfuly saved to "%s" file' % (self.saveFile))
        
    def loadButton_clicked_event(self):
        self.stop_buttonTab1.setVisible(False) #On s'assure que ce bouton ne s'affiche pas
        self.autoSweep_progressbar.setVisible(False) #Idem pour la barre de progression

        #Ouverture d'une petite fenêtre de dialogue contenant uniquement 2 bouttons et un champ de texte
        #pour entrer un nom de fichier dans lequel seront sauvegardés les paramètres
        text, ok = QInputDialog.getText(self, 'Load settings', 
        'Enter a file name :')
        
        if ok and text != '':  #Récupération du nom entré par l'utilisateur
                self.loadFile = str(text)+".txt"
                
        else :  #Si la ligne de texte est vide ou si l'on appui sur "cancel", une error est affichée
                QMessageBox.about(self,'Error','Unable to load settings as no input file name has been chosen')
                return

        if file_is_readable(self.loadFile)==True: #Si le fichier existe
                with open(self.loadFile,"r") as fichier:
                    liste=[]    #Création d'une liste pour stocker les valeurs contenues dans le fichier
                    
                    for ligne in fichier:       #On parcourt toutes les lignes du fichier
                            
                        liste.append(ligne.rstrip('\n\r'))  #On veille à supprimer le "\n" à la fin de chaque ligne
                                                                #indiquant un retour à la ligne
                
                self.channel_combobox.setCurrentIndex(int(liste[0]))
                self.rfref_line.setText(liste[1])
                self.rfvco_spinbox.setValue(float(liste[2]))
                self.rfpfd_line.setText(liste[3])
                self.prescaler_combobox.setCurrentIndex(int(liste[4]))
                self.CPsetting1_combobox.setCurrentIndex(int(liste[5]))
                self.CPsetting2_combobox.setCurrentIndex(int(liste[6]))
                self.CPgain_combobox.setCurrentIndex(int(liste[7]))
                self.CPoutput_combobox.setCurrentIndex(int(liste[8]))
                self.fastlockMode_combobox.setCurrentIndex(int(liste[9]))
                self.timeout_combobox.setCurrentIndex(int(liste[10]))
                self.PFDpolarity_combobox.setCurrentIndex(int(liste[11]))
                self.counterReset_combobox.setCurrentIndex(int(liste[12]))
                self.lockDetectPrecision_combobox.setCurrentIndex(int(liste[13]))
                self.powerDown_combobox.setCurrentIndex(int(liste[14]))
                self.abpw_combobox.setCurrentIndex(int(liste[15]))
                self.muxout_combobox.setCurrentIndex(int(liste[16]))
                self.startFreq_line.setText(liste[17])
                self.stopFreq_line.setText(liste[18])
                self.spacingTab2_line.setText(liste[19])
                self.timeDelay_line.setText(liste[20])

                #On s'assure que le pas de la RF VCO spinbox soit égal à la valeur chargée dans le champ "Channel spacing"
                self.rfvco_spinbox.setSingleStep(int(self.spacingTab1_line.text())*1e-3)
                        
        else:   #Si le fichier ne peut pas être ouvert, une erreur est renvoyée
                QMessageBox.about(self,'File error','"%s" doesn\'t seem to exist' %(self.loadFile))
                return
        
    def channelCombobox_changed_event(self):
        channelCombobox_currentIndex=self.channel_combobox.currentIndex()
        
        #En fonction du cannal de fréquence choisit, on modifie en conséquence
        #l'intervalle de la ComboBox représentant la fréquence de sortie à obtenir
        if channelCombobox_currentIndex==0:
            self.rfvco_spinbox.setMinimum(float(NIR_RANGE_MIN_BOUNDARY_MHZ))
            self.rfvco_spinbox.setMaximum(float(NIR_RANGE_MAX_BOUNDARY_MHZ))
            self.rfvco_spinbox.setValue(float(NIR_RANGE_MIN_BOUNDARY_MHZ))
        elif channelCombobox_currentIndex==1:
            self.rfvco_spinbox.setMinimum(float(UV_RANGE_MIN_BOUNDARY_MHZ))
            self.rfvco_spinbox.setMaximum(float(UV_RANGE_MAX_BOUNDARY_MHZ))
            self.rfvco_spinbox.setValue(float(UV_RANGE_MIN_BOUNDARY_MHZ))
        else:
            self.rfvco_spinbox.setMinimum(float(VIS_RANGE_MIN_BOUNDARY_MHZ))
            self.rfvco_spinbox.setMaximum(float(VIS_RANGE_MAX_BOUNDARY_MHZ))
            self.rfvco_spinbox.setValue(float(VIS_RANGE_MIN_BOUNDARY_MHZ))

    def channel_spacing_changed_event(self):
            
        #En fonction de l'espacement de canal choisit, on modifie en conséquence
        #l'incrément (pas) de la ComboBox
        if self.spacingTab1_line.text()=='': #S'il n'y a rien d'écrit dans le champ de texte,
                                             #on fixe une valeur par défaut
            self.rfvco_spinbox.setSingleStep(1)
        else:
            self.rfvco_spinbox.setSingleStep(float(self.spacingTab1_line.text())*1e-3)

    def update_writePLL_button_label(self):
        self.writePLL_label.setText('') #Le label n'apparaît plus
        return

    def start_button_clicked_event(self):
        self.sweep_progressbar.setVisible(True)

        #On vérifie qu'il y ai bien un port série sélectionné
        if str(self.serialPorts_combobox.currentText())=='':    #S'il n'y a pas de port série affiché dans la combo box une erreur est renvoyée
                QMessageBox.about(self, 'Error : serial port',\
                'No USB device seems to be connected to your computer.')
                self.timer2.stop()
                return
        else:   #Sinon, on récupère le numéro du port série à utiliser
                serial_port="COM"+(str(self.serialPorts_combobox.currentText())[5])+":" #Format "COMx:"

        startFreq_mhz=self.startFreq_line.text()
        stopFreq_mhz=self.stopFreq_line.text()
        spacingTab2_mhz=self.spacingTab2_line.text()
        timeDelay=self.timeDelay_line.text()

        if re.match("[0-9]{4}(?![\d.])",startFreq_mhz)!=None and re.match("[0-9]{4}(?![\d.])",stopFreq_mhz)!=None:
                startFreq_mhz=int(startFreq_mhz)
                stopFreq_mhz=int(stopFreq_mhz)
                if startFreq_mhz>=1000 and startFreq_mhz<stopFreq_mhz and stopFreq_mhz>0 and stopFreq_mhz<=2400:
                        startFreq_hz=int(startFreq_mhz * 1e6)
                        stopFreq_hz=int(stopFreq_mhz * 1e6)
                else:
                        QMessageBox.about(self,"Input Error","Input for Start and Stop frequencies is a value range 1000 to 2400 MHz and Start must be less than Stop Fequency.")
                        self.timer2.stop()
                        return
        else:
                QMessageBox.about(self,"Input Error","Input for Start and Stop frequencies can only be a 4 digits number")
                self.timer2.stop()
                return

        #if re.match("[0-9]{1,4}(?![\d.])",spacingTab2_mhz)!=None or re.match("[0-9]+\.[0-9]{1,4}",spacingTab2_mhz)!=None:
        #if re.match("(?<![\d.])(\d{1,4}|\d{0,4}\.\d{1,4})?(?![\d.])",spacingTab2_mhz)!=None:
        if re.match("[0-9]{1,4}(?![\d.])", spacingTab2_mhz)!=None or re.match("[0-9]{0,4}\.[0-9]{1,4}(?![\d.])",spacingTab2_mhz)!=None:
                spacingTab2_mhz=float(spacingTab2_mhz)
                if spacingTab2_mhz<(stopFreq_mhz - startFreq_mhz):
                        spacingTab2_hz=int(spacingTab2_mhz * 1e6)
                else:
                        QMessageBox.about(self,"Input error","Input for Spacing must be lesser than Start - Stop frequencies and may be a floating number (4 decimal places max)")
                        self.timer2.stop()
                        return
        else:
                QMessageBox.about(self,"Input Error","Input for Spacing can only be a 1 - 4 digits number or a floating value with 1 to 4 decimal places")
                self.timer2.stop()
                return


        if re.match("[0-9]{1,5}(?![\d.])",timeDelay)!=None:
                timeDelay=int(timeDelay)
                if timeDelay>=0 and timeDelay<=10000:
                        timeDelay_ms=timeDelay
                else:
                        QMessageBox.about(self,"Input Error","Input for Time Delay must be between 0 and 10 000 ms")
                        self.timer2.stop()
                        return
        else:
                QMessageBox.about(self,"Input Error","Input for Time Delay can only be a 1 to 5 digits number")
                self.timer2.stop()
                return
        
        rfref_mhz=self.rfref_line.text()    #Récupération de la valeur du champ de texte
        if re.match("[0-9]{2,3}(?![\d.])",rfref_mhz)!=None:  #On vérifie que la chaîne entrée est bien un entier
                                                    #sur 4 chiffres
            
                rfref_mhz=int(rfref_mhz)            #Conversion de la chaîne de caractères en entier
                
                #La valeur doit se situer dans un intervalle précis, si elle n'y est contenue,
                #une boite de dialogue indiquant une erreur est renvoyée
                if (rfref_mhz<RF_REF_MIN_MHZ or rfref_mhz>RF_REF_MAX_MHZ):
                        QMessageBox.about(self, 'Error : incompatible string format',\
                        'Input for Reference Frequency can only be between 20 and 250 MHz')
                        self.timer2.stop()
                        return
                        
                #Si tout est bon, la valeur en MHz est convertie en Hz pour la suite
                else:
                        rfref_hz=int(rfref_mhz * 1e6)
                        
        #Si la chaine entrée n'est pas un entier sur 4 chiffres, une erreur est renvoyée        
        else:
                QMessageBox.about(self, 'Error : incompatible string format',\
                'Input for Reference Frequency can only be a 2 or 3 digits number')
                self.timer2.stop()
                return

        rfpfd_khz=self.rfpfd_line.text()
        if re.match("[0-9]{1,5}(0)(?![\d.])",rfpfd_khz)!=None:   #On vérifie que la chaîne entrée est bien un
                                                        #entier ayant de 1 à 5 chiffres et se terminant
                                                        #par un 0 (nombre rond)
            
                rfpfd_khz=int(rfpfd_khz)    #Conversion de la chaîne de caractères en integer

                #La valeur doit se situer dans un intervalle précis, si elle n'y est contenue,
                #une boite de dialogue indiquant une erreur est renvoyée
                if (rfpfd_khz < RF_PFD_MIN_KHZ or rfpfd_khz > RF_PFD_MAX_KHZ or rfpfd_khz % 10 != 0):
                        QMessageBox.about(self, 'Error : incompatible string format',\
                        'Input for PFD Frequency can only be between 40 and 100 000 kHz (round number)')
                        self.timer2.stop()
                        return

                #Si tout est bon, la valeur en MHz est convertie en Hz pour la suite
                else:
                        rfpfd_hz=int(rfpfd_khz*1e3)
                        channelSpac=rfpfd_hz

        #Si la chaîne entrée ne correspond pas à l'expression régulière, une erreur est renvoyée
        else:
                QMessageBox.about(self, 'Error : incompatible string format',\
                'Input for PFD Frequency can only be a 2 - 6 digits round number')
                self.timer2.stop()
                return

        #self.sweep_progressbar.setRange(startFreq_hz,stopFreq_hz)
        self.currentOutputFreqValue_spinbox.setRange(startFreq_mhz,stopFreq_mhz)

        currentOutputFreq_mhz=self.currentOutputFreqValue_spinbox.value()
        currentOutputFreq_hz=currentOutputFreq_mhz * 1e6

        prescaler_currentIndex=self.prescaler_combobox.currentIndex() #Récupération de l'indice courant
                                                                      #de la ComboBox
        
        #Suivant la valeur de l'indice récupéré, on en déduit la valeur du prédiviseur
        if prescaler_currentIndex==0:
                prescaler=8
        elif prescaler_currentIndex==1:
                prescaler=16
        elif prescaler_currentIndex==2:
                prescaler=32
        else:
                prescaler=64

        r_counter = int(rfref_hz/channelSpac)   #Calculs provenant de la datasheet de la PLL
        n_counter = int(int(currentOutputFreq_hz)/rfpfd_hz)
        b_counter = int(n_counter/prescaler)
        a_counter = n_counter%prescaler
        self.rcountValueTab2_label.setText(str(r_counter))   #On indique les valeurs des compteurs
        self.ncountValueTab2_label.setText(str(n_counter))   #dans leurs labels respectifs
        self.bcountValueTab2_label.setText(str(b_counter))
        self.acountValueTab2_label.setText(str(a_counter))

        CPset1=self.CPsetting1_combobox.currentIndex()
        CPset2=self.CPsetting2_combobox.currentIndex()

        CPgain=self.CPgain_combobox.currentIndex()

        CPoutput=self.CPoutput_combobox.currentIndex()

        fastlock=self.fastlockMode_combobox.currentIndex()

        timer_counter=self.timeout_combobox.currentIndex()

        pfd_polarity=self.PFDpolarity_combobox.currentIndex()

        counter_reset=self.counterReset_combobox.currentIndex()

        lockDetect_precision=self.lockDetectPrecision_combobox.currentIndex()

        power_down=self.powerDown_combobox.currentIndex()
        
        #Power-down est une valeur sur 2 bits qu'il faut découper en deux variables distinctes
        if power_down==0:
                power_down2=0
                power_down1=0
        elif power_down==1:
                power_down2=0
                power_down1=1
        else:
                power_down2=1
                power_down1=1

        abpw=self.abpw_combobox.currentIndex()

        muxout=self.muxout_combobox.currentIndex()

        #On concatène les valeurs binaires obtenues pour former le registre à envoyer à la PLL
        function_latch_b="{0:02b}".format(prescaler_currentIndex)+"{0:1b}".format(power_down2)\
                          +"{0:03b}".format(CPset2)+"{0:03b}".format(CPset1)+"{0:04b}".format(timer_counter)+\
                          "{0:02b}".format(fastlock)+"{0:1b}".format(CPoutput)+"{0:1b}".format(pfd_polarity)+\
                         "{0:03b}".format(muxout)+"{0:1b}".format(power_down1)+"{0:1b}".format(counter_reset)+'10'

        #Le registre d'initialisation est le même que le registre précédent à l'exception
        #des deux derniers bits
        initialization_latch_b=function_latch_b[0:22]+'11'

        r_counter_latch_b='000'+"{0:1b}".format(lockDetect_precision)+'00'+"{0:02b}".format(abpw)+\
                           "{0:014b}".format(r_counter)+'00'
        
        ab_counter_latch_b='00'+"{0:1b}".format(CPgain)+"{0:013b}".format(b_counter)+"{0:06b}".format(a_counter)+'01'

        #On converti les valeurs binaires des registres en valeur hexadécimale sur 6 données
        #alphanumériques
        function_latch_hex='%06x' % int(function_latch_b, 2)
        initialization_latch_hex='%06x' % int(initialization_latch_b, 2)
        r_counter_latch_hex='%06x' % int(r_counter_latch_b, 2)
        ab_counter_latch_hex='%06x' % int(ab_counter_latch_b, 2)

        #On affiche les valeurs des registres dans leurs labels respectifs
        #On fait précéder les valeurs hexa par un "Ox" pour plus de clarté
        #On met également les lettres en majuscules pour l'esthétique
        self.functionLatchValueTab2_label.setText("0x"+str(function_latch_hex).upper())
        self.initLatchValueTab2_label.setText("0x"+str(initialization_latch_hex).upper())
        self.rCounterLatchValueTab2_label.setText("0x"+str(r_counter_latch_hex).upper())
        self.abCounterLatchValueTab2_label.setText("0x"+str(ab_counter_latch_hex).upper())
        
        #Appel de la fonction permettant l'envoi des registres sur le port série
        send_instructions(initialization_latch_hex, function_latch_hex, r_counter_latch_hex, ab_counter_latch_hex, serial_port)

        self.currentOutputFreqValue_spinbox.setValue(currentOutputFreq_mhz+spacingTab2_mhz) #Incrément de la fréquence de sortie courante
        self.sweep_progressbar.setRange(self.currentOutputFreqValue_spinbox.minimum(),self.currentOutputFreqValue_spinbox.maximum())
        self.sweep_progressbar.setValue(self.currentOutputFreqValue_spinbox.value()) #Affichage de la progression avec la ProgressBar

        timeRemaining_ms=(((stopFreq_hz-(currentOutputFreq_hz))/spacingTab2_hz)*(timeDelay_ms+30)) #+30 pour compter le temps d'exécution du programme
                
        if timeRemaining_ms>=0: #Temps que l'on atteint pas 0, on affiche le temps restant
                timeRemaining_s=int((timeRemaining_ms / 1e3)%60)
                timeRemaining_min=int(((timeRemaining_ms / 1e3)/ 60)%60)
                timeRemaining_h=int((((timeRemaining_ms / 1e3)/ 60) / 60)%24)
                timeRemaining_d=int((((timeRemaining_ms / 1e3)/ 60) / 60) / 24)
                text="{:02d}".format(timeRemaining_d)+' '+'DAYS '+"{:02d}".format(timeRemaining_h)+":"+"{:02d}".format(timeRemaining_min)+\
                      ":"+"{:02d}".format(int(timeRemaining_s-(timeDelay_ms*1e-3)))
                self.timeRemaining_lcdnumber.display(text)
        else: #Dès que la limite est atteinte, on affiche 0
                text="00 DAYS 00:00:00"
                self.timeRemaining_lcdnumber.display(text)

        if currentOutputFreq_mhz==self.currentOutputFreqValue_spinbox.maximum(): #On s'assure d'arrêter le timer dès que le balayage de fréquence est terminé 
                self.timer2.stop()
                '''self.sweep_progressbar.reset()
                self.currentOutputFreqValue_spinbox.setValue(self.currentOutputFreqValue_spinbox.minimum())
                text="00 DAYS 00:00:00"
                self.timeRemaining_lcdnumber.display(text)'''
                self.sweepCompleted_label.setText("Sweep completed") #Affichage du label indiquant la fin de l'opération
        else: #Si la valeur max n'est pas encore atteinte, on relance le timer
                self.frequency_sweep_timer(timeDelay_ms)

    def frequency_sweep_timer(self,delay):
        self.timer2=QTimer()

        #Dès que le compteur fini de compter, on appelle la fonction "start_button_clicked_event"
        self.connect(self.timer2, SIGNAL("timeout()"), self.start_button_clicked_event)
        self.timer2.start(delay)

    def stop_buttonTab2_clicked_event(self):
        if self.timer2.isActive()==True:
                self.timer2.stop() #Arrêt du timer sur appui du bouton "Stop"
        self.currentOutputFreqValue_spinbox.setValue(self.currentOutputFreqValue_spinbox.minimum())
        #self.sweep_progressbar.setRange(0,10)
        #self.sweep_progressbar.setValue(0)
        self.sweep_progressbar.reset()
        text="00 DAYS 00:00:00"
        self.timeRemaining_lcdnumber.display(text)
        self.sweepCompleted_label.setText('')

        self.ncountValueTab2_label.setText('');
        self.rcountValueTab2_label.setText('');
        self.bcountValueTab2_label.setText('');
        self.acountValueTab2_label.setText('');

        self.initLatchValueTab2_label.setText('');
        self.functionLatchValueTab2_label.setText('');
        self.rCounterLatchValueTab2_label.setText('');
        self.abCounterLatchValueTab2_label.setText('');

    def quit_button_clicked_event(self):
        app.quit()      #Après un appui sur "Quit", l'application est arrêtée
        window.close()  #et la fenêtre fermée  
        
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)
    
#On renseigne ici la feuille de style qui définit les caractéristiques graphiques
#des widgets présents dans la fenêtre
app.setStyleSheet("QLabel {color: rgb(0,0,127);}"\
                  "QPushButton:flat {color: rgb(255,255,255); background-color: rgb(255,116,70);}"\
                  "QPushButton:pressed {color: rgb(255,255,255); background-color: rgb(255,168,156);\
                  border-radius: 6px; border: 2px solid rgb(255,136,112);}"\
                  "QPushButton:default {color: rgb(255,255,255); background-color: rgb(255,116,70);}"\
                  "QPushButton {color: rgb(255,255,255); background-color: rgb(255,116,70); font: bold 12px;\
                  border: 2px solid rgb(255,136,112);}"\
                  "QDoubleSpinBox {color: rgb(0,0,0); background-color: rgb(255,255,150);\
                  border: 2px solid rgb(255,116,70);}"\
                  "QDoubleSpinBox::up-button {width: 20px; height: 10px;}"\
                  "QDoubleSpinBox::down-button {width: 20px; height: 10px;}"\
                  "QComboBox {border: 2px solid rgb(255,116,70); border-radius: 3px; padding: 1px 18px 1px 3px;\
                  background-color: rgb(255,255,150);}"\
                  "QComboBox:on {padding-top: 3px; padding-left: 4px; background-color: rgb(255,183,0);\
                  color: rgb(255,255,255);}"\
                  "QComboBox::down-arrow:on {top: 1px; left: 1px;}"\
                  "QComboBox::down-arrow {color: red;}"
                  "QLineEdit {background-color: rgb(255,255,150); selection-color: rgb(240,77,48);\
                  selection-background-color: yellow; border: 2px solid rgb(255,116,70); border-radius: 3px;}"\
                  "QLCDNumber {background-color : rgb(255,255,150); border: 2px solid rgb(255,116,70);}")

window = MainWindow()
window.setPalette(QPalette(QColor(255,255,255)))    #Fond blanc pour la fenêtre
window.setAutoFillBackground(True)                  #Remplissage du fond
window.show()
app.exec_()
