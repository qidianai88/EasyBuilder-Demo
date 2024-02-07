# This is a sample Python script.
# -*- coding:utf-8 -*-
from typing import Union
from tkinter import *
from tkinter import StringVar,  filedialog,  messagebox
import cv2
import os
from PIL import Image,ImageTk
import tkinter
import random

import base64
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

import numpy as np


def show_cv_img(img):
    image_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    # 显示或保存PIL图像
    image_pil.show()  # 在新窗口中显示图像


class SourcePortAdapter(HTTPAdapter):
    """"Transport adapter" that allows us to set the source port."""

    def __init__(self, port, *args, **kwargs):
        self.poolmanager = None
        self._source_port = port
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, source_address=('', self._source_port))

class PreviewDialog:
    def __init__( self,root):

        self.root = root
        # ui placement
        self.root.geometry("720x620")


        tkinter.Label(self.root, text="URL:").place(x=20, y=10)
        url = None
        if  os.path.exists('url.txt'):
            f = open('url.txt', 'r')
            url =f.read()
            f.close()
        self.URL = StringVar()
        if url is None or url=='':
            self.URL.set('http://192.168.0.103:8080/rest/ai_detect_server/v1/ai_detect')
        else:
            self.URL.set(url)
        tkinter.Entry(self.root, width=90,
                 textvariable=self.URL).place(x=80, y=10)


        tkinter.Label(self.root, text="图片:").place(x=20, y=40)
        self.img_path = tkinter.StringVar()
        tkinter.Entry(self.root, width=50,
                 textvariable=self.img_path).place(x=80, y=40)
        tkinter.Button(self.root, command=self.select_img, text="选择图片").place(x=440, y=35)

        # 图片显示区域
        self.img_panel = tkinter.Label(self.root,bitmap="gray50", width=700,height=500, relief=GROOVE)
        self.img_panel.place(x=10, y=65)

        tkinter.Button(self.root, command=self.__cancel, text="取消").place(x=150, y=585)
        tkinter.Button(self.root, command=self.__detect, text="识别图片内容").place(x=250, y=585)


    def select_img(self):
        filename = filedialog.askopenfilename()
        if filename is not None and filename != '':
            self.img_path.set(filename)
            img = cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.show_img(img)

    def show_img(self,img):
        cv2image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 转换颜色从BGR到RGB
        current_image = Image.fromarray(cv2image)  # 将图像转换成Image对象
        imgtk = ImageTk.PhotoImage(image=current_image)
        self.img_panel.config(image=imgtk)
        self.img_panel.image=imgtk

    def __detect(self):
        self.save_url()
        filename = self.img_path.get()
        if filename == "":
            tkinter.messagebox.showinfo('提示', '请选择测试图片！')
            return

        with open(filename,"rb") as f:  # 转为二进制格式
            base64_data = base64.b64encode(f.read())  # 使用base64进行加密
            print(base64_data)

        headers = {'Content-Type': 'application/json'}
        datas = json.dumps({"model":"qdian80",
                        "image_name":'test.jpg',
                        "image_type":'jpg',
                        "image": str(base64_data, encoding = "utf-8") })
        r = requests.post(self.URL.get(), data=datas, headers=headers)
        print(r.text)

        result = json.loads(r.text)
        if result['result'] != 'ok':
            return

        img = cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_COLOR)

        for obj in result["boxInfo"]:
            label = f'class id:{int(obj["object_id"])} score:{obj["score"]:.2f}'
            box =[obj["left"],obj["top"],obj["right"],obj["bottom"]]
            plot_one_box(box,img,label=label)

        import threading
        t = threading.Thread(target=show_cv_img, args=(img,))
        t.start()


    def __cancel(self):
        self.root.destroy()

    def save_url(self):
        url = self.URL.get()
        if url is None or url =='':
            return
        f = open('url.txt', 'w')
        f.write(url)
        f.close()

def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c1 = (int(x[0]), int(x[1])+t_size[1])
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


if __name__ == '__main__':

    root = tkinter.Tk()
    root.title('起点AI训练平台')
    sys = PreviewDialog(root)

    root.mainloop()

