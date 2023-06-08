import tkinter
import socket
from tkinter import ttk
import time
import datetime
import threading
import subprocess
import codecs

global SERVER_IP, SERVER_PORT, CLIENT_PORT
SERVER_IP = 'localhost'
SERVER_PORT = 8887
CLIENT_PORT = 9999

MAX_DATA_BYTES = 16380
PAUSE = 0.01 #пауза между отправками данных
CONNECTION_CHECK_DELAY = 1.5 #раз во сколько секунд проверять соединение с сервером
COMMAND_ENTRY_LEN = 90 #сколько символов вмещается в консольный вывод
MAX_STR_IN_CONSOLE_OUTPUT = 800 #сколько максимум строк можно вывести в консоль 



class GUI():
    def __init__(self):

        self.started = False #флаг, что поток запущен
        self.create_window()
        self.create_gui_elements()
        self.socket = Socket(output=self.console_output, connection_status=self.connection_bar)
        self.window.mainloop()

    def create_window(self):
        self.window = tkinter.Tk()
        self.window.title('RemoteController by Dragmor')
        self.window.wm_iconbitmap("icon.ico")
        self.window.resizable(width=False, height=False)

    def create_gui_elements(self):
        #==========ВЕРХНЯЯ ПАНЕЛЬ==========#
        self.tab_control = ttk.Notebook(self.window) #верхняя панель
        self.tab_main = tkinter.Frame(self.tab_control, border=5) #вкладка ГЛАВНАЯ
        self.tab_tasks = tkinter.Frame(self.tab_control, background='white', border=5) #вкладка ЗАДАЧИ
        self.tab_terminal = tkinter.Frame(self.tab_control, border=5) #вкладка ТЕРМИНАЛ
        #
        self.tab_control.add(self.tab_main, text='главная')
        self.tab_control.add(self.tab_terminal, text='консоль')
        self.tab_control.add(self.tab_tasks, text='задачи')
        #======ОСТОЯНИЕ_ПОДКЛЮЧЕНИЯ========#
        self.connection_bar = tkinter.Label(self.window, 
            text='нет соединения с сервером', bg='pink', font='calibri', relief='sunken')
        #=======РАССТАНОВКА ЭЛЕМЕНТОВ======#
        self.connection_bar.pack(fill='both') #панель состояния подключения
        self.tab_control.pack(expand=1, fill='both') #панель вкладок
        #====ЭЛЕМЕНТЫ_НА_ВКЛАДКЕ_ГЛАВНАЯ=====#
        self.ipports_frame = tkinter.Frame(self.tab_main)
        self.ipports_frame.pack(side='left', anchor='n')
        self.server_ip_frame = tkinter.Frame(self.ipports_frame, padx=5)
        self.server_port_frame = tkinter.Frame(self.ipports_frame, padx=5)
        self.client_port_frame = tkinter.Frame(self.ipports_frame, padx=5)

        self.text_server_ip = tkinter.Label(self.server_ip_frame, text='ipv4 адрес сервера')
        self.server_ip_entry = tkinter.Entry(self.server_ip_frame, border=5)#, width=70)
        self.text_server_ip.pack()
        self.server_ip_entry.pack()

        self.text_server_port = tkinter.Label(self.server_port_frame, text='порт сервера')
        self.server_port_entry = tkinter.Entry(self.server_port_frame, border=5, width=12)#, width=70)
        self.text_server_port.pack()
        self.server_port_entry.pack()

        self.text_client_port = tkinter.Label(self.client_port_frame, text='порт приёма')
        self.client_port_entry = tkinter.Entry(self.client_port_frame, border=5, width=12)#, width=70)
        self.text_client_port.pack()
        self.client_port_entry.pack()

        #вставляю в поля ввода дефолтные данные
        temp_server_ip = tkinter.StringVar()
        temp_server_port = tkinter.StringVar()
        temp_client_port = tkinter.StringVar()
        #
        temp_server_ip.set(SERVER_IP)
        temp_server_port.set(SERVER_PORT)
        temp_client_port.set(CLIENT_PORT)
        #
        self.server_ip_entry.configure(textvariable=temp_server_ip)    
        self.server_port_entry.configure(textvariable=temp_server_port)
        self.client_port_entry.configure(textvariable=temp_client_port)




        #поля ввода данных для подключения
        self.server_ip_frame.pack(side='left', anchor='n')
        self.server_port_frame.pack(side='left', anchor='n')
        self.client_port_frame.pack(side='left', anchor='n')
        #кнопки подключения
        self.button_connect = tkinter.Button(self.tab_main, text='подключиться', command=self.try_connect)
        self.button_autoconnect = tkinter.Button(self.tab_main, text='автоподключение по ip')
        #настройки вида окна
        self.button_topmost = tkinter.Button(self.tab_main, text='поверх всех окон', bg='pink', command=self.topmost)
        self.alpha_button = tkinter.Button(self.tab_main, text='эффект прозрачности', bg='pink',command=self.set_alpha)


        self.button_connect.pack(fill='both')
        self.button_autoconnect.pack(fill='both')
        self.button_topmost.pack(side='bottom', fill='both')
        self.alpha_button.pack(side='bottom', fill='both')

        
        #====ЭЛЕМЕНТЫ_НА_ВКЛАДКЕ_ЗАДАЧИ====#
        #расставляю панели задач
        self.tasks = []
        for task in range(9):
            self.tasks.append(Task(task))
            self.tasks[-1].frame = tkinter.Frame(self.tab_tasks, border=1, relief='groove')
            self.tasks[-1].create_elements()
            self.tasks[-1].execute_now_button = tkinter.Button(self.tasks[-1].frame, text="выполнить сейчас" , bg='lightgreen', width=15, 
                command=(lambda self=self, task_id=task: self.command_by_task_id(task_id)))
            self.tasks[-1].execute_now_button.pack(side="left")
            self.tasks[-1].frame.pack()

        self.btn_start_tasks_timer = tkinter.Button(self.tab_tasks, text='запустить таймер', font='calibri', bg='lightgreen', command=self.start_timer)
        self.btn_start_tasks_timer.pack(side='bottom', fill='both')  
        #====ЭЛЕМЕНТЫ_НА_ВКЛАДКЕ_КОНСОЛЬ===#
        self.console_frame = tkinter.Frame(self.tab_terminal) 

        self.command_frame = tkinter.Frame(self.console_frame) #фрейм кнопки и поля ввода команды
        self.command_entry = tkinter.Entry(self.command_frame, border=5, width=70)
        self.btn_send_command = tkinter.Button(self.command_frame, text='отправить', font='system', bg='lightgreen', command=self.send_command_from_console)
        self.console_output = tkinter.Listbox(self.console_frame, relief="sunken", activestyle='none', bg='black', fg='green', height=15, border=5)
        self.console_output.bind("<Double-ButtonPress>", self.copy_text_to_entry)
        self.command_entry.bind("<Key-Return>", self.send_command_from_console)
        #
        self.console_output.pack(side='top', fill='both')
        self.command_entry.pack(side="left", anchor='n', fill='both')
        self.btn_send_command.pack(anchor='n', fill='both')
        self.command_frame.pack(side='bottom',fill='both')
        #
        self.console_frame.pack(side='bottom',fill='both')
        self.command_entry.focus()
        
        #==================================#

    def try_connect(self):
        global SERVER_IP, SERVER_PORT, CLIENT_PORT
        '''метод перезапуска прослушивания порта'''
        try:
            temp_server_ip = self.server_ip_entry.get()
            temp_server_port = int(self.server_port_entry.get())
            temp_client_port = int(self.client_port_entry.get())
            SERVER_IP = temp_server_ip
            SERVER_PORT = temp_server_port
            CLIENT_PORT = temp_client_port
        except:
            return
        try:
            temp_socket = self.socket
            #завершаю потоки
            self.socket.socket.close()
            self.socket.check_counter = -1
            del self.socket
            self.connection_bar.configure(text='нет соединения с сервером', bg='pink')
            self.socket = Socket(output=self.console_output, connection_status=self.connection_bar)
        except:
            self.socket = temp_socket
         

    def set_alpha(self, *args):
        '''регулирует прозрачность окна'''
        if self.window.wm_attributes('-alpha') == 1.0:
            self.alpha_button.configure(bg='lightgreen')
            self.window.wm_attributes('-alpha', 0.75)
        else:
            self.alpha_button.configure(bg='pink')
            self.window.wm_attributes('-alpha', 1.0)

    def topmost(self):
        '''поверх всех окон'''
        if self.window.wm_attributes("-topmost") == 0:
            self.window.wm_attributes("-topmost", True)
            self.button_topmost.configure(bg='lightgreen')
        else:
            self.window.wm_attributes("-topmost", False)
            self.button_topmost.configure(bg='pink')


    def start_timer(self):
        '''таймер выполнения задач'''
        if self.started == False:
            self.started = True
            self.btn_start_tasks_timer.configure(text='пауза', bg='lightyellow')
            self.thread = threading.Thread(target=self.timer_thread)
            self.thread.daemon = True
            self.thread.start()
        else:
            self.started = False
            self.btn_start_tasks_timer.configure(text='запустить таймер', bg='lightgreen')


    def timer_thread(self):
        '''поток таймера'''
        while self.started:
            for obj in self.tasks:
                if obj.refresh_time() == True:
                    if obj.check_start() == True:
                        self.command_by_task_id(obj.id)
            time.sleep(0.3)

    def send_command_from_console(self, *args):
        '''отправка команды из консоли'''
        if self.command_entry.get() == '':
            return
        command = self.command_entry.get()
        self.send_command(command)

    def command_by_task_id(self, task_id):
        '''выполняет команду по нажатию кнопки "запустить сейчас"'''
        command = self.tasks[task_id].command_enter.get()
        if command == '':
            return
        self.send_command(command)

    def send_command(self, command):
        '''отправка команды'''
        if command == '' or command == None:
            return
        self.console_output.insert(self.console_output.size(), command) #вставляю в консоль отправляемый текст
        self.console_output.itemconfig(self.console_output.size()-1, foreground='orange') #перекрашиваю введённую команду в другой цвет
        self.console_output.see(self.console_output.size()) #прокручиваю список выведенного текста
        self.socket.send_data(command)

    def copy_text_to_entry(self, event):
        self.command_entry.delete(0, len(self.command_entry.get()))
        self.command_entry.insert(0, self.console_output.get(self.console_output.curselection()))
        self.console_output.get(self.console_output.curselection()) #получаю текст выбранного пункта
        self.command_entry.focus()


class Socket():
    def __init__(self, output, connection_status):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", CLIENT_PORT))
        self.address = (SERVER_IP, SERVER_PORT) # адрес клиента
        self.connection_bar = connection_status
        self.console_output = output
        #прослушивание сокета
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        #проверка соединения с сервером
        self.check_counter = 0 #счётчик для проверки соединения
        self.connection_thread = threading.Thread(target=self.connection_checker)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        #
        

    def connection_checker(self):
        while self.check_counter >= 0:
            temp = self.check_counter
            self.send_data('[chk?]')
            time.sleep(CONNECTION_CHECK_DELAY*1.2)
            if temp != self.check_counter and self.check_counter >= 0: #если соединение есть
                self.connection_bar.configure(text='соединение установлено', bg='lightgreen')
            else:
                if self.check_counter < 0:
                    break
                self.connection_bar.configure(text='нет соединения с сервером', bg='pink')


    def listen(self):
        '''метод слушает порт'''
        try:
            while True:
                data, address = self.socket.recvfrom(MAX_DATA_BYTES) 
                decoded_data = codecs.decode(data) # раскодирую принятую информацию
                if decoded_data == '[chk!]':
                    self.connection_bar.configure(text='соединение установлено', bg='lightgreen')
                    self.check_counter+=1
                    if self.check_counter > 10:
                        self.check_counter = 0
                else:
                    self.write_to_output(decoded_data)
        except:
            return
            
    def send_data(self, data):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data.encode('utf-8'), self.address)
        client_socket.close()

    def write_to_output(self, data):
        data = data.split('\n')
        for d in data:
            if len(d) > COMMAND_ENTRY_LEN:
                temp_text = d
                while len(temp_text) > 0:
                    temp = temp_text[:COMMAND_ENTRY_LEN]
                    temp_text = temp_text[COMMAND_ENTRY_LEN:]
                    self.console_output.insert(self.console_output.size(), temp)
                if len(temp_text) > 0:
                    self.console_output.insert(self.console_output.size(), temp)
            else:
                self.console_output.insert(self.console_output.size(), d)
        if self.console_output.size() > MAX_STR_IN_CONSOLE_OUTPUT:
            self.console_output.delete(0, self.console_output.size()-MAX_STR_IN_CONSOLE_OUTPUT)
        self.console_output.see(self.console_output.size())
        

    def processing_bufer(self, bufer, file_name = ''):
        """метод передаёт пакеты данных"""
        while len(bufer) > 0:#пока есть что передавать (в буфере или в пакете),
                             #передаю эти данные в цикле
            pack = ''        #в эту переменную формируется пакет данных
            pack += bufer[:MAX_DATA_BYTES // 8] #формирую пакет
            bufer = bufer[MAX_DATA_BYTES // 8:]
            if len(bufer) == 0:
                break
            time.sleep(PAUSE)
            self.send_data(data=pack)
            pack = ''
        # проверяю буфер пакетов
        if len(pack) > 0:  #если пакет данных не пустой
            time.sleep(PAUSE)
            self.send_data(data=pack)
        pack = '' #обнуляю значение пакета

class Task():
    def __init__(self, task_id):
        self.id = task_id
        self.executed = False
        if self.id%2 != 0:
            self.bg_color = 'white'
        else:
            self.bg_color = 'lightgray'

    def create_elements(self):
        self.text_exec = tkinter.Label(self.frame, text="выполнить ", font='system')
        self.command_enter = tkinter.Entry(self.frame, borderwidth=5, width=20)
        self.text_in_time = tkinter.Label(self.frame, text="в ", font='system')
        hours_values = ['']+list(range(0, 24))
        minutes_values = ['']+list(range(0, 60))
        self.hours_enter = tkinter.Spinbox(self.frame, values=hours_values, width=2, wrap=True)
        self.minutes_enter = tkinter.Spinbox(self.frame, values=minutes_values, width=2, wrap=True)
        self.timer = tkinter.Label(self.frame, text="до запуска:", width=20, font='calibri', fg='blue')
        # self.execute_now_button = tkinter.Button(self.frame, text="выполнить сейчас" , bg='lightgreen', width=15, command=exit)
        #устанавливаю цвета
        self.frame.configure(background=self.bg_color)
        self.text_exec.configure(bg=self.bg_color)
        self.text_in_time.configure(bg=self.bg_color)
        self.timer.configure(bg=self.bg_color)

        #размещаю элементы упарвления
        self.text_exec.pack(side="left")
        self.command_enter.pack(side="left")
        self.text_in_time.pack(side="left")
        self.hours_enter.pack(side="left")
        self.minutes_enter.pack(side="left")
        self.timer.pack(side="left")
        # self.execute_now_button.pack(side="left")

    def refresh_time(self):
        '''метод обновляет текущее время до выполнения задачи,
        и возвращает True, если настало время выполнения, иначе False'''
        if self.hours_enter.get() == '' or self.minutes_enter.get() == '':
            return False
        exec_time = datetime.timedelta(
         hours=int(self.hours_enter.get()),
         minutes=int(self.minutes_enter.get()),
         seconds=0) 
        now_time = datetime.timedelta(
         hours=time.localtime().tm_hour,
         minutes= time.localtime().tm_min,
         seconds=time.localtime().tm_sec)
        #разница во времени
        delta = str(exec_time-now_time).split()[-1] 
        #вывожу время до запуска
        self.timer.configure(text='до запуска: %s' %(delta))
        #сброс флага, что задача была выполнена
        if exec_time-now_time < datetime.timedelta(hours=0, minutes=0, seconds=0) and self.executed == True:
            self.executed = False
        #проверка, подошло-ли время запуска
        if exec_time-now_time == datetime.timedelta(hours=0, minutes=0, seconds=0):
            return True
        else:
            return False

    def check_start(self):
        '''метод проверяет, была ли уже выполнена задача'''
        if self.executed == False:
            self.executed = True
            return True
        else:
            return False

if __name__ == "__main__":
    app = GUI()




'''

'''