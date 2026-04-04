import json
import os
from time import sleep
from typing import TypeVar
from PySide6.QtGui import QIntValidator
from screeninfo.common import Monitor


from mongita.database import Database
from screeninfo import get_monitors
from datetime import datetime
from PySide6.QtCore import QObject, QSize, Qt
from PySide6.QtWidgets import QFrame, QGroupBox, QHBoxLayout, QProgressBar, QScrollArea, QStyle, QTextEdit, QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QComboBox, QLabel
from bson import ObjectId

from controller.DBRequestsController import DBRequestsController
from dispatcher.Abstract_Dispatcher import Abstract_Dispatcher
from dispatcher.Dispatcher_Local import Dispatcher_Local
from queue import Queue
from dispatcher.Dispatcher_Master import Dispatcher_Master
from dispatcher.Dispatcher_Slave import Dispatcher_Slave
from message.ConnectedMessage import ConnectedMessage
from message.DisconnectedMessage import DisconnectedMessage
from message.DispatcherMessage import DispatcherMessage
from message.MacroMessage import MacroMessage
from message.AbstractUpdateMessage import AbstractUpdateMessage
from message.ErrorMessage import ErrorMessage
from message.PlayerMessage import PlayerMessage
from message.RemoteMessage import RemoteMessage
from messenger.messenger import Messenger

from model.Coordinates import Coordinates
from model.Screen import Screen
from model.Macro import Macro
from util.Target import Target
from util.DBConnection import DBConnection
from util.Event_Enum import DispatcherEvent, MacroEvent, PlayerEvent
from util.parse_ini import parse_ini
from util.Dispatcher_Enum import Dispatcher

T = TypeVar("T", bound=QObject)
LOGS_FOLDER = "./Logs"

class GuiConfig:
    def __init__(self) -> None:
        self.show_connections = False

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config: str = parse_ini()
        self.available_screens: list[Screen] = [Screen(id=i, resolution=Coordinates(
            x=monitor.width, y=monitor.height), top_left=Coordinates(x=monitor.x, y=monitor.y)) for i, monitor in enumerate[Monitor](get_monitors())]

        self.bbdd: str = parse_ini()
        self.connection: Database | None = DBConnection.get_connection(
            db=self.bbdd)
        self.controller: DBRequestsController = DBRequestsController()

        self.queue: Queue[AbstractUpdateMessage] = Queue[AbstractUpdateMessage]()

        self.messenger: Messenger = Messenger()
        self.messenger.signal.connect(self.consume_events)

        self.dispatcher: Abstract_Dispatcher = Dispatcher_Local(messenger=self.messenger,available_screens=self.available_screens)

        self.active_connections:dict[str,QGroupBox] = {}

        # GUI ITEMS
        self.setWindowTitle("AutoKey")
        self.setStyleSheet("""
                                QWidget {
                                    background-color: #0f539a;
                                }
                                QPushButton, QComboBox, QLineEdit, QTextEdit, QScrollArea, QGroupbox {
                                    background-color: white;
                                    color: black;
                                    border: 1px solid #CCCCCC;
                                    padding: 4px;
                                    border-radius: 4px;
                                }
                                QComboBox QAbstractItemView {
                                    background-color: #e7eef5
                                    }
                                QScrollArea {
                                    background-color: #e7eef5
                                    }
                                QGroupBox::title {
                                    color: white;
                                    font-weight: bold;
                                    font-size: 100pt;
                                    subcontrol-origin: margin;
                                    subcontrol-position: top center;
                                }
                            """)
        self.gui_config: GuiConfig = GuiConfig()

        # MAIN CENTRAL ITEMS
        self.main_central_widget: QWidget = QWidget()
        # Set the central widget of the Window.
        self.setCentralWidget(self.main_central_widget)
        self.main_horizontal_layout: QHBoxLayout = QHBoxLayout(self.main_central_widget)
        
        # MASTER MODE ITEMS
        self.scroll_area: QScrollArea = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumSize(500, 300)

        self.connections_menu: QFrame = QFrame()
        self.connections_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.connections_menu_layout: QVBoxLayout = QVBoxLayout(self.connections_menu)
        self.connections_menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.connections_menu)
        self.scroll_area.hide()

        # LOCAL MODE MENU
        self.local_menu_widget: QWidget = QWidget()
        self.local_menu_layout: QVBoxLayout = QVBoxLayout(self.local_menu_widget)
        self.local_menu_widget.setFixedSize(QSize(500,700))

        self.main_row_1: QHBoxLayout = QHBoxLayout()
        
        self.main_row_2: QHBoxLayout = QHBoxLayout()
        self.main_row_2_1: QVBoxLayout = QVBoxLayout()
        self.main_row_2_2: QVBoxLayout = QVBoxLayout()
        self.main_row_2.addLayout(self.main_row_2_1)
        self.main_row_2.addLayout(self.main_row_2_2)
        
        self.main_row_3: QHBoxLayout = QHBoxLayout()
        
        self.main_row_4: QVBoxLayout = QVBoxLayout()
        
        self.main_row_5: QHBoxLayout = QHBoxLayout()
        self.main_row_5_1: QHBoxLayout = QHBoxLayout()
        self.main_row_5_2: QHBoxLayout = QHBoxLayout()
        self.main_row_5_3: QHBoxLayout = QHBoxLayout()
        self.main_row_5_4: QHBoxLayout = QHBoxLayout()
        self.main_row_5.addLayout(self.main_row_5_1)
        self.main_row_5.addLayout(self.main_row_5_2)
        self.main_row_5.addLayout(self.main_row_5_3)
        self.main_row_5.addLayout(self.main_row_5_4)
        self.main_row_5_1.addStretch()
        self.main_row_5_2.addStretch()
        self.main_row_5_3.addStretch()
        self.main_row_5_4.addStretch()

        self.main_row_6: QHBoxLayout = QHBoxLayout()

        self.local_menu_layout.addLayout(self.main_row_1)
        self.local_menu_layout.addLayout(self.main_row_2)
        self.local_menu_layout.addLayout(self.main_row_3)
        self.local_menu_layout.addLayout(self.main_row_4)
        self.local_menu_layout.addLayout(self.main_row_5)
        self.local_menu_layout.addLayout(self.main_row_6)


        ########## ROW 1 OF MAIN MENU -> EXISTING MACROS ###################
        self.existing_macro_combo: QComboBox = QComboBox(parent=self)
        self.existing_macro_combo.setEditable(True)

        self.main_row_1.addWidget(self.existing_macro_combo)
        
        ########## ROW 2 OF MAIN MENU (LEFT COLUMN) ###################

        self.button1: QPushButton = QPushButton("Create macro")
        self.button1.clicked.connect(self.create_macro)
        self.button1.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))

        self.button2: QPushButton = QPushButton("Update macro")
        self.button2.clicked.connect(self.update_macro)
        self.button2.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))

        self.button3: QPushButton = QPushButton("Delete macro")
        self.button3.clicked.connect(self.delete_macro)
        self.button3.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))

        self.main_row_2_1.addWidget(self.button1)
        self.main_row_2_1.addWidget(self.button2)
        self.main_row_2_1.addWidget(self.button3)
        
        ########## ROW 2 OF MAIN MENU (RIGHT COLUMN) ###################

        self.button4: QPushButton = QPushButton("Run macro")
        self.button4.clicked.connect(self.run_macro)
        self.button4.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

        self.button5: QPushButton = QPushButton("Stop")
        self.button5.clicked.connect(self.stop)
        self.button5.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))

        self.button6: QPushButton = QPushButton("Pause/Continue")
        self.button6.clicked.connect(self.toggle_pause)
        self.button6.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

        self.main_row_2_2.addWidget(self.button4)
        self.main_row_2_2.addWidget(self.button5)
        self.main_row_2_2.addWidget(self.button6)

        ########## ROW 3 OF MAIN MENU -> SPEED & REPS BUTTONS ###################

        self.speed: QComboBox = QComboBox(placeholderText="Speed")
        self.speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward), "Turbo", 0.25)
        self.speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward), "Fast", 0.5)
        self.speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton), "Normal", 1.0)
        self.speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward), "Slow", 1.5)
        self.speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward), "Minimal", 2.0)
        self.speed.setCurrentIndex(2)
        self.speed.setEditable(True)
        self.speed.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speed.lineEdit().setReadOnly(True)
        self.speed.setStyleSheet("""
                                QComboBox {
                                    background-color: white;
                                    border: 1px solid gray;
                                }
                                QComboBox QAbstractItemView {
                                    background-color: #e7eef5;
                                }
                                """)


        self.reps: QComboBox = QComboBox()
        self.reps.setEditable(True)
        self.reps.lineEdit().setPlaceholderText("Repetitions")
        self.reps.addItem("")
        self.reps.addItem("∞ Infinite")
        self.reps.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reps.setStyleSheet("""
                                QComboBox {
                                    background-color: white;
                                    border: 1px solid gray;
                                }
                                QComboBox QAbstractItemView {
                                    background-color: #e7eef5;
                                }
                                """)

        self.main_row_2_1.addWidget(self.speed)
        self.main_row_2_2.addWidget(self.reps)

        ########## ROW 4 OF MAIN MENU -> LOG FIELD & PROGRESS BAR ###################
        self.progress_bar: QProgressBar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Step %v of %m (%p%)")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid gray;
                border-radius: 5px;
                background-color: white;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #e7eef5;
                border-radius: 24px;
            }
        """)
        self.progress_bar.hide()

        self.log_field: QTextEdit = QTextEdit()
        self.log_field.setReadOnly(True)

        self.main_row_4.addWidget(self.progress_bar)
        self.main_row_4.addWidget(self.log_field)
        

        ########## ROW 5 OF MAIN MENU -> CLEAR, IP, PORT, MODE ###################

        self.button7: QPushButton = QPushButton("Clear")
        self.button7.clicked.connect(self.clear_log_field)
        self.button7.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))

        self.host_text_edit: QLineEdit = QLineEdit()
        self.host_text_edit.setFixedSize(QSize(70, 25))
        # self.host_text_edit.setText("127.0.0.1")
        self.host_text_edit.setPlaceholderText("Host")
        self.host_text_edit.hide()

        self.port_text_edit: QLineEdit = QLineEdit()
        self.port_text_edit.setValidator(QIntValidator(0, 65535))
        self.port_text_edit.setFixedSize(QSize(70, 25))
        # self.port_text_edit.setText("3000")
        self.port_text_edit.setPlaceholderText("Port")
        self.port_text_edit.hide()

        self.dispatcher_mode_combo: QComboBox = QComboBox(parent=self)
        self.dispatcher_mode_combo.setEditable(True)
        self.dispatcher_mode_combo.currentTextChanged.connect(self.update_dispatcher_mode)

        self.main_row_5_1.addWidget(self.button7)
        self.main_row_5_2.addWidget(self.host_text_edit)
        self.main_row_5_3.addWidget(self.port_text_edit)
        self.main_row_5_4.addWidget(self.dispatcher_mode_combo)

        self.dispatcher_mode_combo.setStyleSheet("""
                                QComboBox {
                                    background-color: white;
                                    border: 1px solid gray;
                                }
                                QComboBox QAbstractItemView {
                                    background-color: #e7eef5;
                                }
                                """)
        self.dispatcher_mode_combo.setFixedWidth(80)
        self.dispatcher_mode_combo.setEditable(True)
        self.dispatcher_mode_combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dispatcher_mode_combo.lineEdit().setReadOnly(True)


        ########## ROW 6 OF MAIN MENU -> CONNECTION BUTTONS & SAMPLE BUTTON ###################
      
        self.connection_button: QPushButton = QPushButton("Connect")
        self.connection_button.clicked.connect(self.stablish_connection)
        self.connection_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.connection_button.hide()

        self.launch_server_button: QPushButton = QPushButton("Launch Server")
        self.launch_server_button.clicked.connect(self.launch_server)
        self.launch_server_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.launch_server_button.hide()
        
        self.disconnection_button: QPushButton = QPushButton("Disconnect")
        self.disconnection_button.clicked.connect(self.break_connection)
        self.disconnection_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        self.disconnection_button.hide()

        self.sample_message_button: QPushButton = QPushButton("sample message")
        self.sample_message_button.clicked.connect(self.dummy)
        self.sample_message_button.hide()

        self.main_row_6.addWidget(self.connection_button)
        self.main_row_6.addWidget(self.launch_server_button)
        self.main_row_6.addWidget(self.disconnection_button)
        self.main_row_6.addWidget(self.sample_message_button)

        ########## ADD TO GENERAL LAYOUT ###################  
        self.main_horizontal_layout.addWidget(self.local_menu_widget)
        self.main_horizontal_layout.addWidget(self.scroll_area)

        ########## INITIAL COMBOS FILL ###################
        self.fill_dispatcher_mode_combo()
        self.fill_macros_combo()



    def get_current_target(self) -> Target|None:
        host: str = self.host_text_edit.text()
        port_str: str = self.port_text_edit.text()

        try:
            port = int(port_str)
        except (ValueError,TypeError) as e:
            self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str(e)))
            return

        return Target(host=host,port=port)

    def stablish_connection(self) -> None:
        target: Target | None = self.get_current_target()
        if target is None:
            self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str("Failed to stablish connection")))
            return

        if target.url in self.active_connections.keys():
            return

        self.dispatcher.connect(target=target)

    def create_connection_box(self,target:Target) -> QGroupBox:
        box: QGroupBox = QGroupBox(target.url)
        box_layout: QVBoxLayout = QVBoxLayout()
        first_row: QHBoxLayout = QHBoxLayout()
        box_layout.addLayout(first_row)
        second_row: QHBoxLayout = QHBoxLayout()
        box_layout.addLayout(second_row)
        third_row: QHBoxLayout = QHBoxLayout()
        box_layout.addLayout(third_row)
        
        fourth_row: QHBoxLayout = QHBoxLayout()
        box_layout.addLayout(fourth_row)

        fifth_row: QHBoxLayout = QHBoxLayout()
        box_layout.addLayout(fifth_row)
        fifth_row_column_A: QVBoxLayout = QVBoxLayout()
        fifth_row.addLayout(fifth_row_column_A)

        fifth_row_column_B: QVBoxLayout = QVBoxLayout()
        fifth_row.addLayout(fifth_row_column_B)
        
        box.setLayout(box_layout)

        macro_combo: QComboBox = QComboBox(parent=box)
        macro_combo.setEditable(True)
        macro_combo.setObjectName("available_macros_combo")

        connection_led: QLabel = QLabel(parent=box)
        led_size:int = 24
        connection_led.setFixedSize(led_size,led_size)
        connection_led.setStyleSheet(
            f"""
            QLabel {{
            border: 2px solid #006400;
            border-radius: {led_size // 2}px;
            background-color: #00FF00;
            box-shadow: 0 0 5px #00FF00;
            }}
            """
        )
        connection_led.setObjectName("connection_led")

        speed: QComboBox = QComboBox(placeholderText="Speed",parent=box)
        speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward), "0.25", 0.25)
        speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward), "Turbo", 0.25)
        speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward), "Fast", 0.5)
        speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Normal", 1.0)
        speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward), "Slow", 1.5)
        speed.addItem(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward), "Minimal", 2.0)
        speed.setCurrentIndex(2)

        reps: QComboBox = QComboBox(parent=box)
        reps.setEditable(True)
        reps.lineEdit().setPlaceholderText("Repetitions")
        reps.addItem("")
        reps.addItem("∞ Infinite")
        reps.setCurrentIndex(-1)

        progress_bar: QProgressBar = QProgressBar(parent=box)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("Step %v of %m (%p%)")
        progress_bar.setObjectName("progress_bar")
        progress_bar.hide()

        log_field: QTextEdit = QTextEdit(parent=box)
        log_field.setReadOnly(True)
        log_field.setObjectName("log_field")

        button_play = QPushButton("Play",parent=box)
        play_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        button_play.setIcon(play_icon)
        button_play.clicked.connect(lambda _, t=target: self.run_macro(t=t,combo=macro_combo,s=speed,r=reps))
        
        button_pause = QPushButton("Pause",parent=box)
        pause_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        button_pause.setIcon(pause_icon)
        button_pause.clicked.connect(lambda _, t=target: self.toggle_pause(t=t))

        button_stop = QPushButton("Stop",parent=box)
        stop_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        button_stop.setIcon(stop_icon)
        button_stop.clicked.connect(lambda _, t=target: self.stop(t = t))
        
        button_disconnect = QPushButton("Disconnect",parent=box)
        disconnect_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        button_disconnect.setIcon(disconnect_icon)
        button_disconnect.clicked.connect(lambda _, t=target: self.break_connection(t=t))

        button_clear = QPushButton("clear",parent=box)
        play_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
        button_clear.setIcon(play_icon)
        button_clear.clicked.connect(lambda _, t=target: self.clear_log_field(t=t))

        first_row.addWidget(macro_combo)

        second_row.addWidget(speed)
        second_row.addWidget(reps)

        third_row.addWidget(button_play)
        third_row.addWidget(button_pause)
        third_row.addWidget(button_stop)
        third_row.addWidget(button_disconnect)
        fourth_row.addWidget(progress_bar)
        fifth_row_column_A.addWidget(log_field)
        fifth_row_column_B.addWidget(connection_led,alignment=Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        fifth_row_column_B.addWidget(button_clear,alignment=Qt.AlignmentFlag.AlignBottom)

        return box

    def break_connection(self,_:bool=False,t:Target|None=None) -> None:
        target:Target|None

        if type(self.dispatcher) == Dispatcher_Slave:
            target: Target | None = self.get_current_target()
            if target is None:
                self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str("Invalid IP or Port")))
                return
            target.host = "127.0.0.1"
        else:
            if t is None:
                self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str("Invalid IP or Port")))
                return
            target = t
        
        disconnection_succeed: bool = self.dispatcher.disconnect(target=target)
        if disconnection_succeed and type(self.dispatcher) == Dispatcher_Master:
            removed_conn_from_gui = self.active_connections.pop(target.url)
            if removed_conn_from_gui is not None:
                self.connections_menu_layout.removeWidget(removed_conn_from_gui)
                removed_conn_from_gui.deleteLater()
                if type(self.dispatcher) == Dispatcher_Master:
                    self.dispatcher.clean_disconnected_slave(slave_id=target.url)
        self.adjustSize()


        if not disconnection_succeed:
            self.log_field.append("Failed to close connection")
            return
        
        self.log_field.append("Connection closed")

        

    def dummy(self) -> None:
        target: Target | None = self.get_current_target()
        self.dispatcher.dummy(target=target,screen=self.available_screens[0])



    def get_item_by_id(self,slave_id:str,cls_type:type[T],name:str) -> T|None:
            slave_box: QGroupBox | None = self.active_connections.get(slave_id)
            if slave_box is None:
                return
            
            return slave_box.findChild(cls_type, name=name)
            
    def consume_events(self, received_message: AbstractUpdateMessage|RemoteMessage) -> None:
        slave_id:str|None = None
        log_field: QTextEdit
        message:AbstractUpdateMessage
        
        if isinstance(received_message,RemoteMessage):
            slave_id, message = received_message.slave_id, received_message.message
            tmp_log_field:QTextEdit | None = self.get_item_by_id(slave_id=slave_id,cls_type=QTextEdit,name="log_field")
            
            if tmp_log_field is None:
                return
            
            log_field = tmp_log_field
        
        else:
            message = received_message
            log_field = self.log_field
            
        message_line: str = json.dumps(message.jsonify(),indent=2)

        if isinstance(message, DisconnectedMessage) and type(self.dispatcher) == Dispatcher_Master:
                # self.dispatcher.clean_disconnected_slave(slave_id=message.slave_id)
                target = Target.from_string(message.slave_id)
                if target is not None:
                    self.dispatcher.stop(target=target)                  
        
        elif isinstance(message, ConnectedMessage):
            target = Target.from_string(message.slave_id)
            if target is not None:
                new_box: QGroupBox = self.create_connection_box(target=target)
                self.active_connections[target.url] = new_box

                self.connections_menu_layout.addWidget(new_box)

                self.fill_macros_combo(combo=new_box.findChild(QComboBox, "available_macros_combo"))

                self.adjustSize()

        elif isinstance(message, MacroMessage):
            steps_strings:str
            if message.macro is None:
                steps_strings = ""
            else:
                steps_strings_list = []
                for step in message.macro.steps:
                    step_name_list: list[str] = []
                    step_type: str | None = step.type
                    step_key: str | None = step.key
                    step_duration: float | None = step.key_duration
                    
                    if isinstance(step_key,str):
                        step_name_list.append(step_key)
                    if isinstance(step_type,str):
                        step_name_list.append(step_type)
                    if isinstance(step_duration,float):
                        step_name_list.append(f"({step_duration} s)")
                    
                    step_str = " ".join(step_name_list)
                    steps_strings_list.append(step_str)
                
                if not steps_strings_list:
                    steps_strings = ""
                else:
                    # steps_strings = "\n".join(f"+ {string}" for string in steps_strings_list)
                    steps_strings = f"Steps List:\n{"; ".join(steps_strings_list)}"
            
            match message.event:
                case MacroEvent.CREATED|MacroEvent.UPDATED:
                    if message.macro is None:
                        log_field.append(f"--> {message.event_time}: Failed to create macro: recorded macro is empty\n\n")
                        return
                    
                    log_field.append(f"--> {message.event_time}: Macro {message.macro.name} was correctly recorded\n{steps_strings}\n\n")

                    result:bool
                    if message.macro.id is None:
                        result = self.controller.save_macro(obj=message.macro)
                    else:
                        result = self.controller.update_macro(obj=message.macro)

                    if result:
                        log_field.append(f"--> {datetime.now()}: Macro {message.macro.name} was correctly saved\n\n")
                    else:
                        log_field.append(f"--> {datetime.now()}: Macro {message.macro.name} could not be saved correctly\n{steps_strings}\n\n")
                
                case MacroEvent.DELETED:
                    if message.macro is None or message.macro.name is None:
                        log_field.append(f"--> {message.event_time}: Macro \"Unknown\" was correctly deleted\n\n")
                    else:
                        log_field.append(f"--> {message.event_time}: Macro {message.macro.name} was correctly deleted\n{steps_strings}\n\n")
                
                case MacroEvent.SAVED:
                    if message.macro is None or message.macro.name is None:
                        log_field.append(f"--> {message.event_time}: Macro \"Unknown\" was correctly saved\n\n")
                    else:
                        log_field.append(f"--> {message.event_time}: Macro {message.macro.name} was correctly saved\n{steps_strings}\n\n")
                
                case MacroEvent.STARTED:
                    progress_bar:QProgressBar|None
                    if not slave_id:
                        progress_bar = self.progress_bar
                    else:
                        progress_bar = self.get_item_by_id(slave_id=slave_id,cls_type=QProgressBar,name="progress_bar")
                    
                    if progress_bar is not None and message.macro is not None:  
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(len(message.macro.steps))
                    
            self.fill_macros_combo()

        elif isinstance(message, PlayerMessage):
            progress_bar:QProgressBar|None
            if not slave_id:
                progress_bar = self.progress_bar
            else:
                progress_bar = self.get_item_by_id(slave_id=slave_id,cls_type=QProgressBar,name="progress_bar")
            
                if progress_bar is None:
                    return                

            match message.event:
                case PlayerEvent.STARTED|PlayerEvent.STOPPED|PlayerEvent.TOGGLED_PAUSE|PlayerEvent.FINISHED:
                    log_field.append(f"--> {message.event_time}: Player {message.event.name.lower()}\n\n".replace("_"," "))

                case PlayerEvent.ADVANCED:
                    progress_bar.setValue(message.current_step)
                    # progress_bar.repaint()
                    progress_bar.update()
                    
                case PlayerEvent.END_OF_MACRO:
                    target:Target|None = None
                    if slave_id:
                        target = Target.from_string(url=slave_id)
                        if target is None:
                            return
                    self.stop(t=target)
        
        elif isinstance(message,ErrorMessage):
            log_field.append(f"--> {message.event_time}: {message.error}\n\n")
        elif isinstance(message,DispatcherMessage):
            log_field.append(f"--> {message.event_time}: {message.event.name.replace("_"," ").capitalize()}\n\n")
            match message.event:
                case DispatcherEvent.ON_RUN:
                    progress_bar:QProgressBar|None
                    if not slave_id:
                        progress_bar = self.progress_bar
                    else:
                        progress_bar = self.get_item_by_id(slave_id=slave_id,cls_type=QProgressBar,name="progress_bar")
                    
                        if progress_bar is None:
                            return
                    if progress_bar.isHidden():    
                        progress_bar.show()
                case DispatcherEvent.SERVER_DOWN:
                    if slave_id:
                        connection_led = self.get_item_by_id(slave_id=slave_id,cls_type=QLabel,name="connection_led")
                        if connection_led:
                            connection_led.setStyleSheet(f"""
                                                            QLabel {{
                                                                border: 2px solid #8B0000;
                                                                border-radius: {connection_led.width() // 2}px;
                                                                background-color: #FF0000;
                                                                box-shadow: 0 0 5px #FF0000;
                                                            }}
                                                        """)
        else:
            log_field.append(f"--> {message_line}\n\n")

        self.add_to_log(slave_id,message_line)

    def add_to_log(self, slave_id:str|None,message_line:str) -> None:
        try:
            if slave_id is None:
                slave_id = "127.0.0.1"
            line:str = f"{datetime.now()}\nMode: {self.dispatcher.__class__.__name__.split("_")[1]}, Target: {slave_id}\n{message_line}\n\n"

            if not os.path.exists(LOGS_FOLDER):
                os.makedirs(name=LOGS_FOLDER)
        
            with open(file=f"./Logs/{datetime.now().strftime("%Y-%m-%d")}.log",mode="a",encoding="UTF-8") as log:
                log.write(line)
        
        except Exception as e:
            self.log_field.append(str(e))

    def toogle_buttons(self,mode) -> None:
        match mode:
            case Dispatcher.Local:
                self.existing_macro_combo.show()
                self.button1.show()
                self.button2.show()
                self.button3.show()
                self.button4.show()
                self.speed.show()
                self.reps.show()
                self.port_text_edit.hide()

            case Dispatcher.Master:
                self.scroll_area.show()
                self.connection_button.show()
                self.host_text_edit.show()
                self.button5.hide()
                self.button6.hide()

            case Dispatcher.Slave:
                self.launch_server_button.show()
                self.disconnection_button.show()
                
                
        if mode == Dispatcher.Local or mode == Dispatcher.Slave:
            self.hide_scroll_area()
            self.connection_button.hide()
            self.host_text_edit.hide()
            self.button5.show()
            self.button6.show()

        if mode == Dispatcher.Master or mode == Dispatcher.Slave:
            self.existing_macro_combo.hide()
            self.button1.hide()
            self.button2.hide()
            self.button3.hide()
            self.button4.hide()
            self.speed.hide()
            self.reps.hide()
            self.port_text_edit.show()
        
        if mode == Dispatcher.Master or mode == Dispatcher.Local:
            self.launch_server_button.hide()
            self.disconnection_button.hide()

    def update_dispatcher_mode(self, text: str) -> None:
        mode: Dispatcher = Dispatcher[text]
        if mode.value == type(self.dispatcher):
            return
        
        if type(self.dispatcher) == Dispatcher_Master:
            for k in self.active_connections.keys():
                self.break_connection(t= Target.from_string(url=k))

        self.dispatcher.clean_up()
        self.messenger.master = None
        
        match mode:
            case Dispatcher.Local:
                self.dispatcher = Dispatcher_Local(messenger=self.messenger,available_screens=self.available_screens)
                self.toogle_buttons(mode=Dispatcher.Local)

            case Dispatcher.Master:
                self.dispatcher = Dispatcher_Master(messenger=self.messenger,available_screens=self.available_screens)
                self.toogle_buttons(mode=Dispatcher.Master)

            case Dispatcher.Slave:
                self.clear_log_field()
                self.dispatcher = Dispatcher_Slave(messenger=self.messenger,available_screens=self.available_screens)
                self.toogle_buttons(mode=Dispatcher.Slave)
        
        self.adjustSize()

    def launch_server(self) -> None:
        if type(self.dispatcher) != Dispatcher.Slave.value:
            return
        try:
            server_up = self.dispatcher.run_server(port=int(self.port_text_edit.text()))
            if server_up is False:
                self.dispatcher.clean_up()
                self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str("Unable to start Server")))
        except ValueError:
            self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(), error=str("Expected type int")))

    def hide_scroll_area(self) -> None:
        self.scroll_area.hide()
        
        self.main_horizontal_layout.update()
        self.main_horizontal_layout.activate()


    def fill_macros_combo(self,combo:QComboBox|None=None) -> None:
        existing_macros: list[Macro] = self.controller.get_all_macros()
        combos_to_update: list[QComboBox] = []
        
        if combo is None:
            combos_to_update.append(self.existing_macro_combo)
            for box in self.connections_menu.findChildren(QGroupBox):
                combo = box.findChild(QComboBox, "available_macros_combo")
                if combo is not None:
                    combos_to_update.append(combo)
        elif isinstance(combo,QComboBox):
            combos_to_update.append(combo)

        for combobox in combos_to_update:
            combobox.clear()
            combobox.addItem("")
            
            for i in existing_macros:
                if not i.name:
                    i.name = "<Unknown>"
                combobox.addItem(i.name, userData=i.id)

    def fill_dispatcher_mode_combo(self) -> None:

        self.dispatcher_mode_combo.clear()
        self.dispatcher_mode_combo.addItem("")
        for i in Dispatcher:
            self.dispatcher_mode_combo.addItem(i.name)

        self.dispatcher_mode_combo.setCurrentIndex(1)

    def create_macro(self) -> None:
        try:
            name: str = self.existing_macro_combo.currentText().strip()
            macro: Macro = Macro()
            macro.name = name if (len(name)>0) else "<Unknown>"
            self.dispatcher.record(macro=macro)

        except Exception as e:
            print(e)
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(e)))

    def update_macro(self) -> None:
        index: int = self.existing_macro_combo.currentIndex()
        try:
            _id: ObjectId = ObjectId(
                oid=self.existing_macro_combo.itemData(index))
            macro: Macro | None = self.controller.get_macro_by_id(_id=_id)
            if macro is None:
                return
            macro.screens = []
            macro.steps = []

            if not isinstance(macro, Macro):
                raise RuntimeError("Macro not found")
            elif macro.name is None:
                macro.name = "<Unknown>"

            self.dispatcher.update(macro=macro)

        except Exception as e:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(e)))

    def delete_macro(self) -> None:
        index: int = self.existing_macro_combo.currentIndex()
        try:
            _id: ObjectId = ObjectId(
                oid=self.existing_macro_combo.itemData(index))

            macro: Macro | None = self.controller.get_macro_by_id(_id=_id)
            if not isinstance(macro, Macro):
                raise RuntimeError("Macro not found")

            result: bool = self.controller.delete_macro(_id=_id)
            if result is False:
                raise RuntimeError(
                    "Failed to delete macro: an unexpected error occurred.")
            else:
                self.messenger.send_event(event=MacroMessage(
                    event_time=datetime.now(), macro=macro,event=MacroEvent.DELETED))

        except Exception as e:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(e)))

    def run_macro(self,_:bool=False,t:Target|None=None,combo:QComboBox|None=None,s:QComboBox|None=None,r:QComboBox|None = None) -> None:
        rs: QComboBox
        rr: QComboBox
        current_combo: QComboBox
        target: Target | None

        try:
            if type(self.dispatcher) == Dispatcher_Local:
                rs = self.speed
                rr = self.reps
                target = self.get_current_target()
                current_combo= self.existing_macro_combo
            else:
                if (t is None 
                    or combo is None
                    or s is None
                    or r is None):
                    return
                rs = s
                rr = r
                target = t
                current_combo= combo

            speed_float: float = rs.currentData()
            raw_reps: str = rr.currentText()

            reps_float: int

            if raw_reps == "":
                reps_float = 1
            elif raw_reps.startswith("∞"):
                reps_float = -1
            else:
                reps_float = int(raw_reps)

            if combo is None:
                current_combo: QComboBox = self.existing_macro_combo
            else:
                current_combo = combo
            
            index: int = current_combo.currentIndex()

            _id: ObjectId = ObjectId(
                oid=self.existing_macro_combo.itemData(index))

            macro: Macro | None = self.controller.get_macro_by_id(_id=_id)
            if target is None:
                target: Target | None = self.get_current_target()

            if macro is not None:
                self.dispatcher.run(
                    macro=macro, reps=reps_float, speed=speed_float,target=target)

        except Exception as e:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(e)))

    def stop(self,_:bool=False,t:Target|None=None) -> None:
        target:Target|None

        if t is None:
            target = self.get_current_target()
        else:
            target = t

        self.dispatcher.stop(target)

    def toggle_pause(self,_:bool=False,t:Target|None=None) -> None:
        target:Target|None

        if t is None:
            target = self.get_current_target()
        else:
            target = t

        self.dispatcher.toggle_pause(target)

    def clear_log_field(self,_:bool=False,t:Target|None=None) -> None:
        log_field:QTextEdit
        progress_bar:QProgressBar
        if t is None:
            log_field = self.log_field
            progress_bar = self.progress_bar
        else:
            tmp_log_field: QTextEdit|None = self.get_item_by_id(slave_id=t.url,cls_type=QTextEdit,name="log_field")
            tmp_progress_bar:QProgressBar|None = self.get_item_by_id(slave_id=t.url,cls_type=QProgressBar,name="progress_bar")
            
            if tmp_log_field is None or tmp_progress_bar is None:
                return
            
            log_field = tmp_log_field
            progress_bar = tmp_progress_bar
        
        log_field.clear()
        progress_bar.setValue(0)
        progress_bar.hide()



app: QApplication = QApplication([])

window: MainWindow = MainWindow()
window.show()

app.exec()
