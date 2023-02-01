import subprocess
import sys
import os

import configparser
import filetype
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, \
    QTextBrowser, QProgressBar, QTextEdit, QTabWidget


class path_textBrower(QTextBrowser):
    def __init__(self):
        super(path_textBrower, self).__init__()
        self.setAcceptDrops(True)
        self.urls_string_files = []

    def dragEnterEvent(self, e):

        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        pass

    # 遍历拖入的文件夹里的压缩文件和拖入的压缩文件
    # 返回给Demo第一次需要解压文件列表
    def dropEvent(self, e):
        urls = [path for path in e.mimeData().urls()]
        achieve_exname = ('zip', 'rar', '7z')
        urls_string_files = []
        urls_string_dirs = []
        for url in urls:
            if os.path.isdir(url.path()[1:]):  # [1:]去除路径前的/字符
                urls_string_dirs.append(url.path()[1:])
            else:
                file_kind = filetype.guess(url.path()[1:])
                if file_kind is not None and file_kind.extension in achieve_exname:
                    urls_string_files.append(url.path()[1:])

        # 深度遍历下
        for url in urls_string_dirs:
            if os.path.isdir(url):
                for root, dirs, files in os.walk(url):
                    for file in files:
                        file_kind = filetype.guess(os.path.join(root, file))
                        if file_kind is not None and file_kind.extension in achieve_exname:
                            urls_string_files.append(os.path.join(root, file))

        if urls_string_files == []:
            self.setText('没有发现压缩文件')
        else:
            self.setText('\n'.join(urls_string_files))
            self.urls_string_files = urls_string_files


class Demo(QTabWidget):  # 1
    def __init__(self):
        super(Demo, self).__init__()
        self.thread_1 = None

        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.addTab(self.tab1, 'JXL')
        self.addTab(self.tab2, '解压')
        self.button1 = QPushButton('开始', self)
        self.button1.clicked.connect(self.run_py)
        self.button2 = QPushButton('解压', self)
        self.button2.clicked.connect(self.extract_py)
        self.input_textBrower_logs = path_textBrower()
        self.output1_textBrower_logs = QTextBrowser(self)
        self.output2_textBrower_logs = QTextBrowser(self)
        self.password_texteditor_logs = QTextEdit(self)
        self.password_texteditor_logs.textChanged.connect(self.passwordListChanged)
        self.progressBar_all = QProgressBar(self)

        self.urls_string_files = []
        self.urls_string_dirs = []
        conf = configparser.ConfigParser()
        conf.read(".\\TEST.ini", encoding='utf-8')
        self.passwordList = conf.defaults()['passwords'].split(',')
        self.password_texteditor_logs.setText('\n'.join(self.passwordList))
        self.layout_init()
        self.resize(700, 700)

        # self.bm = bookManager()
        # self.pathList = [r'C:\Users\lyy\workwork\djangoProject5\app01\static\jxl\真·中华小当家 Vol.12']
        # self.fileCount = 0
        # self.picDict = self.scanPics()
        # self.multiNum = multiNum

        # for list in self.picDict.values():
        #     self.fileCount += len(list)

        # self.input_textBrower_logs.setText('\n'.join(self.picList))
        # self.progressBar_all.setRange(0, self.fileCount // self.multiNum)
        # self.progressBar_all.setValue(0)

    def passwordListChanged(self):
        self.passwordList = list(filter(bool, self.password_texteditor_logs.toPlainText().split('\n')))
        conf = configparser.ConfigParser()
        conf.read(".\\TEST.ini", encoding='utf-8')
        if (conf.defaults()['passwords'].split(',') != self.passwordList):
            conf.set('DEFAULT', 'passwords', ','.join(self.passwordList))
            conf.write(open(".\\TEST.ini", "w", encoding='utf-8'))
            print("passwordListChanged", self.passwordList)
        else:
            pass

    def scanPics(self):
        tempDict = {'jpg': [], 'png': []}
        for rootPath in self.pathList:
            for root, dirs, files in os.walk(rootPath):
                for file in files:
                    kind = filetype.guess(f'''{root}\\{file}''')
                    if (kind == None):
                        continue
                    try:
                        ext = kind.extension  # 能被filetype识别到的文件类型
                        if (ext == 'jpg'):
                            tempDict['jpg'].append(f'{root}\\{file}')
                        if (ext == 'png'):
                            tempDict['png'].append(f'{root}\\{file}')
                    except Exception as ex:
                        print(ex)
        return tempDict

    def layout_init(self):

        self.h_layout3 = QHBoxLayout()
        self.h_layout3.addWidget(self.button1)
        self.h_layout3.addWidget(self.button2)

        self.v_layout = QVBoxLayout()
        self.v_layout.addLayout(self.h_layout3)
        self.v_layout.addWidget(self.input_textBrower_logs)
        self.v_layout.addWidget(self.output1_textBrower_logs)

        self.h_layout4 = QHBoxLayout()
        self.h_layout4.addWidget(self.password_texteditor_logs)
        self.h_layout4.addWidget(self.output2_textBrower_logs)
        self.h_layout4.setStretch(1, 3)

        self.v_layout.addLayout(self.h_layout4)
        self.v_layout.addWidget(self.progressBar_all)
        # self.setTabText(1, "个人详细信息")
        self.tab1.setLayout(self.v_layout)
        self.tab2.setLayout(self.v_layout)
        # self.setLayout(self.v_layout)

    def run_py(self):
        self.progressBar_all.setValue(0)
        self.thread_1 = Runthread(picsDic=self.picDict, multiNum=self.multiNum)
        self.thread_1.progressBarValue.connect(self.callback)
        self.thread_1.start()

    # 回传进度条参数
    def callback(self, i):
        self.progressBar_all.setValue(i)

    def extract_py(self):
        self.progressBar_all.setRange(0, len(self.input_textBrower_logs.urls_string_files))
        self.progressBar_all.setValue(0)
        self.thread_1 = bandizip_extract_thread(self.input_textBrower_logs.urls_string_files, self.passwordList)
        self.thread_1.progressBarValue.connect(self.callback)
        self.thread_1.output1_set.connect(self.setOutput1Text)
        self.thread_1.output1_append.connect(self.appendOutput1Text)
        self.thread_1.output2_append.connect(self.appendOutput2Text)
        self.output2_textBrower_logs.setText('')
        self.thread_1.start()

    def appendOutput1Text(self, index):
        textList1 = self.input_textBrower_logs.urls_string_files[:index]
        textList2 = self.input_textBrower_logs.urls_string_files[index:]
        self.output1_textBrower_logs.setText('\n'.join(textList1))
        self.input_textBrower_logs.setText('\n'.join(textList2))

    def appendOutput2Text(self, text):
        self.output2_textBrower_logs.append(text)

    def setOutput1Text(self, text):
        self.output1_textBrower_logs.setText(text)

    def setOutput2Text(self, text):
        self.output2_textBrower_logs.setText(text)


class bandizip_extract_thread(QThread):
    progressBarValue = pyqtSignal(int)  # 更新进度条
    signal_done = pyqtSignal(int)  # 是否结束信号

    output1_set = pyqtSignal(str)
    output2_append = pyqtSignal(str)
    output1_append = pyqtSignal(str)

    def __init__(self, urls_string_files, passwordList):
        super(bandizip_extract_thread, self).__init__()
        self.passwordList = passwordList
        self.urls_string_files = urls_string_files

    def run(self):
        archives1 = []
        archives1DirsSet = set()
        for file_path, index in zip(self.urls_string_files, range(1, len(self.urls_string_files) + 1)):
            self.bandizip_extract(file_path, 'archives1')
            self.progressBarValue.emit(index)
            # new_file_path = os.path.join(os.path.dirname(file_path), 'archives1', os.path.basename(file_path))
            # self.output1_append.emit(new_file_path)
            archives1DirsSet.add(os.path.join(os.path.dirname(file_path), 'archives1'))
        # 工序2
        #  遍历所有archieves1文件夹
        for extractDir in archives1DirsSet:
            for root, dirs, files in os.walk(extractDir):
                for file in files:
                    file_kind = filetype.guess(os.path.join(root, file))
                    if file_kind is not None and file_kind.extension in ('rar', 'zip', '7z'):
                        archives1.append(os.path.join(root, file))
        self.output1_set.emit('\n'.join(archives1))
        self.progressBarValue.emit(0)
        #  再次开始解压
        for file, index2 in zip(archives1, range(1, len(archives1) + 1)):
            log = self.bandizip_extract(file, 'archives2')
            self.output2_append.emit(log)
            self.progressBarValue.emit(index2)
        self.output2_append.emit('结束哩')

    # for file_path, index in zip(self.urls_string_files, range(1, len(self.urls_string_files) + 1)):
    #     self.bandizip_extract(file_path)
    #     self.progressBarValue.emit(index)
    #     self.output1_append.emit(index)

    def bandizip_extract(self, file_path, archivesName):
        if not os.path.exists(os.path.join(os.path.dirname(file_path), archivesName)):
            os.mkdir(os.path.join(os.path.dirname(file_path), archivesName))
        if os.path.exists(file_path):
            for password in self.passwordList:
                try:
                    task = subprocess.run(
                        [r'C:\Program Files\Bandizip\bz.exe', 'x', '-aoa', file_path,
                         os.path.join(os.path.dirname(file_path), archivesName)], shell=True,
                        input=f'{password}\n'.encode('gbk'),
                        check=True, capture_output=True
                    )  # 解压覆盖模式
                    # output = task.stdout.decode('gbk')[92:].split('\r\n')
                    if task.stdout:
                        print(task.stdout.decode('utf-8'))
                    break
                except subprocess.CalledProcessError as err:
                    print(err.output.decode('utf-8'))
                # out, err = extract_task.communicate()
                # print(out.decode('gbk'))
                # extract_task.stdin.write(b'123456789')
                # out, err = extract_task.communicate(input=password.encode('gbk'))
                # print(out.decode('gbk'))
                # print(err.decode('gbk'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = Demo()

    demo.show()  # 7
    sys.exit(app.exec_())
