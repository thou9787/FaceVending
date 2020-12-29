# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 22:38:25 2019

@author: user
"""

from tkinter import *
import tkinter as tk
import tkinter.messagebox as tkmb
from PIL import ImageTk as itk, Image
import cv2
import sys,os,dlib,glob,numpy
from skimage import io
import imutils
import pymysql
import datetime

image1 = "Cola1.jpg"
image2 = "Sprite1.jpg"
image3 = "Fanta.jpg"

db = pymysql.connect(host='localhost', port=3306, 
                     user='root', passwd='', db='vendingmachine', charset='utf8')

cursor = db.cursor()


window = tk.Tk()
window.title('Vending_machine')
window.geometry('1000x600')

canvas = tk.Canvas(window, bg='gainsboro', height=280, width=700)

image_file1 = itk.PhotoImage(file=image1)
image_file2 = itk.PhotoImage(file=image2)
image_file3 = itk.PhotoImage(file=image3)

#展示圖片
image = canvas.create_image(115, 25, anchor='n', image=image_file1)
image = canvas.create_image(350, 25, anchor='n', image=image_file2)
image = canvas.create_image(585, 25, anchor='n', image=image_file3)

#展示畫布
canvas.grid()



var = tk.StringVar() 
l = tk.Label(window, textvariable=var, bg='white', font=('Arial', 12), width=30, height=2, compound='left')

#展示label
l.grid(row=0, column= 10)

on_hit = False #cancel
on_hit_1 = False #cola
on_hit_2 = False #sprite
on_hit_3 = False #fanta
on_hit_4 = False #confirm
on_hit_5 = False #facial
U_name = " " #username
#S_value = 0


def U_account(username):
    cursor.execute("SELECT Account FROM users WHERE name='%s'" % username)
    userACC = cursor.fetchone()
    return userACC[0]
#搜尋users table的Account
def D_id():
    cursor.execute("SELECT MAX(id) FROM purchaselog")
    result1 = cursor.fetchone()
    if not result1:
        return 20
    else:
        return int(result1[0]+1)
#搜尋productlog table的id並+1
def insertData(ProductId, U_name):
    purchaseTime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    OrderId = D_id()
    Account = U_account(U_name)
    cursor.execute("INSERT INTO purchaselog (id, Account, ProductId, CreateDateTime) VALUES ('%d', '%s', '%d', '%s')" % (OrderId, Account, ProductId, purchaseTime))
    db.commit()
#將資料插入purchaselog table    
def updateValue(u_name, price):
    global on_hit_5
    cursor.execute("SELECT StoredValue FROM users WHERE name = '%s'" % u_name)
    s_value = cursor.fetchone()
    S_value = int(s_value[0])
    if(S_value < price):
        var.set("Please add the value!")
    else:
        cursor.execute("UPDATE users SET StoredValue = StoredValue-'%d' WHERE name = '%s'" % (price, u_name))
        db.commit()
#更新帳戶餘額

#按鍵功能設定
def recognitionFace(filePath):
    global U_name, on_hit_5
    # 人臉68特徵點模型路徑
    predictor_path = "shape_predictor_68_face_landmarks.dat"

    # 人臉辨識模型路徑
    face_rec_model_path = "dlib_face_recognition_resnet_model_v1.dat"

    # 比對人臉圖片資料夾名稱(之後要改成server資料夾)
    faces_folder_path = "C:/Users/user/Desktop/python/Flask/rec"

    # 需要辨識的人臉圖片名稱
    #img_path = "D:\openCVimage\image1.jpg" #sys.argv[1]
    img_path = filePath

    # 載入人臉檢測器
    detector = dlib.get_frontal_face_detector()

    # 載入人臉特徵點檢測器
    sp = dlib.shape_predictor(predictor_path)

    # 載入人臉辨識檢測器
    facerec = dlib.face_recognition_model_v1(face_rec_model_path)

    # 比對人臉描述子列表
    descriptors = []

    # 比對人臉名稱列表
    candidate = []

    # 針對比對資料夾裡每張圖片做比對:
    # 1.人臉偵測
    # 2.特徵點偵測
    # 3.取得描述子
    for f in glob.glob(os.path.join(faces_folder_path, "*.jpg")):
        base = os.path.basename(f)
        # 依序取得圖片檔案人名
        candidate.append(os.path.splitext(base)[ 0])
        img = io.imread(f)

        # 1.人臉偵測
        dets = detector(img, 1)

        for k, d in enumerate(dets):
            # 2.特徵點偵測
            shape = sp(img, d)
 
            # 3.取得描述子，128維特徵向量
            face_descriptor = facerec.compute_face_descriptor(img, shape)

            # 轉換numpy array格式
            v = numpy.array(face_descriptor)
            descriptors.append(v)


    # 針對需要辨識的人臉同樣進行處理
    img = io.imread(img_path)
    dets = detector(img, 1)

    dist = []
    for k, d in enumerate(dets):
        shape = sp(img, d)
        face_descriptor = facerec.compute_face_descriptor(img, shape)
        d_test = numpy.array(face_descriptor)

        x1 = d.left()
        y1 = d.top()
        x2 = d.right()
        y2 = d.bottom()
        # 以方框標示偵測的人臉
        cv2.rectangle(img, (x1, y1), (x2, y2), ( 0, 255, 0), 4, cv2. LINE_AA)
 
        # 計算歐式距離
        for i in descriptors:
            dist_ = numpy.linalg.norm(i -d_test)
            dist.append(dist_)

    # 將比對人名和比對出來的歐式距離組成一個dict
    c_d = dict( zip(candidate,dist))

    # 根據歐式距離由小到大排序
    cd_sorted = sorted(c_d.items(), key = lambda d:d[ 1])
    # 取得最短距離就為辨識出的人名
    try:
        if(cd_sorted[0][1] < 0.4):
            userPic = cd_sorted[0][0] + '.jpg'
            cursor.execute("SELECT name, StoredValue FROM users WHERE faceImage = '%s'" % userPic)
            result = cursor.fetchall()
            U_name = "".join(result[0][0])
            S_value = int(result[0][1])
            var.set("Hello " + U_name + " $" + '%d' % S_value)
        else:
            var.set("Access denied, Please try again!")
            on_hit_5 = False
    except IndexError:
        var.set("Access denied, Please try again!")
        on_hit_5 = False
    #try...catch..Indexerror..not yet

def hit_cancel():
    global on_hit, on_hit_1, on_hit_2, on_hit_3
    if on_hit == False:
        on_hit = True
        var.set('')
        on_hit = False
    elif(on_hit_1 == True or on_hit_2 == True or on_hit_3 ==True):
        on_hit = True
        var.set('Cancel')
        on_hit = False
    else:
        on_hit = False
        var.set('')
        
def hit_cola():
    global on_hit, on_hit_1, on_hit_2, on_hit_3
    if  on_hit_1 == False:
         on_hit = False
         on_hit_1 = True
         on_hit_2 = False
         on_hit_3 = False
         var.set('Cola $20')
    else:
        on_hit_1 = False
        var.set('')
        
def hit_sprite():
    global on_hit, on_hit_1, on_hit_2, on_hit_3
    if on_hit_2 == False:
        on_hit_2 = True
        on_hit = False
        on_hit_1 = False
        on_hit_3 = False
        var.set('Sprite $30')
    else:
        on_hit_2 = False
        var.set('')
        
def hit_fanta():
    global on_hit, on_hit_1, on_hit_2, on_hit_3
    if on_hit_3 == False:
        on_hit = False
        on_hit_1 = False
        on_hit_2 = False
        on_hit_3 = True
        var.set('Fanta $25')
    else:
        on_hit_3 = False
        var.set('')
    
def hit_confirm():
    global on_hit_4, on_hit_1, on_hit_2, on_hit_3, on_hit_5, U_name
    if on_hit_5 == False:
        on_hit_4 = True
        var.set('Please log in first')
        on_hit_1 = False
        on_hit_2 = False
        on_hit_3 = False
        on_hit_4 = False
        on_hit_5 = False
        #如果還沒登入
    elif (on_hit_5 == True and on_hit_1 == True):
        on_hit_4 = True
        tkmb.showinfo("Vending", "Purchase Successfully!")
        var.set('')
        on_hit_1 = False
        on_hit_2 = False
        on_hit_3 = False
        on_hit_4 = False
        on_hit_5 = False
        price = 20
        P_id = 4
        updateValue(U_name, price)
        insertData(P_id, U_name)
        #登入買完Cola
    elif (on_hit_5 == True and on_hit_2 == True):
        on_hit_4 = True
        tkmb.showinfo("Vending", "Purchase Successfully!")
        var.set('')
        on_hit_1 = False
        on_hit_2 = False
        on_hit_3 = False
        on_hit_4 = False
        on_hit_5 = False
        price = 30
        P_id = 6
        updateValue(U_name, price)
        insertData(P_id, U_name)
        #登入買完Sprite
    elif (on_hit_5 == True and on_hit_3 == True):
        on_hit_4 = True
        tkmb.showinfo("Vending", "Purchase Successfully!")
        var.set('')
        on_hit_1 = False
        on_hit_2 = False
        on_hit_3 = False
        on_hit_4 = False
        on_hit_5 = False
        price = 25
        P_id = 5
        updateValue(U_name, price)
        insertData(P_id, U_name)
        #登入買完Fanta
    elif (on_hit_5 == True and (on_hit_1 == False and on_hit_2 == False and on_hit_3 == False)):
        on_hit_4 = True
        var.set('Please choose drinks first')
        on_hit_4 = False
        #登入還沒買飲料就按按鍵
    else:
        on_hit_4 = False
        var.set('Please log in first')
def hit_start():
    global on_hit_5
    if on_hit_5 == False:
        on_hit_5 = True
        cap = cv2.VideoCapture(0)
        i=1
        while(True):
    
            #從攝影機擷取影像
            ret, frame = cap.read()
            cv2.imshow('type S: confirm, ESC: cancel', frame)
            k = cv2.waitKey(1)
    
            if k==27:
                on_hit_5 = False
                break
            elif k==ord('s'):
            
                cv2.imwrite('D:/openCVimage/' + "image" + str(i) + '.jpg', frame)
                filePath = 'D:/openCVimage/' + "image" + str(i) + '.jpg'
                #cv2.imwrite('camera.jpg', frame)
                i+=1
                cap.release()
                cv2.destroyAllWindows()
                recognitionFace(filePath)
                break
        
        #圖片名改成username比較好
        #改成server路徑
    elif on_hit_5 == True:
        var.set("You are already logged in")

    
    
    
#展示按鍵
b = tk.Button(window, text='Start', bg='blue', font=('Arial', 12), width=10, height=1, command=hit_start)
b.place(x=792, y=200)

b1 = tk.Button(window, text='', bg='yellow', width=10, height=1, command=hit_cola)
b1.place(x=72, y=300)

b2 = tk.Button(window, text='', bg='yellow', width=10, height=1, command=hit_sprite)
b2.place(x=310, y=300)

b3 = tk.Button(window, text='', bg='yellow', width=10, height=1, command=hit_fanta)
b3.place(x=545, y=300)

b4 = tk.Button(window, text='Confirm', bg='green', font=('Arial', 12), width=10, height=1, command=hit_confirm)
b4.place(x=792, y=250)

b5 = tk.Button(window, text='Cancel', bg='red', font=('Arial', 12), width=10, height=1, command=hit_cancel)
b5.place(x=792, y=300)

window.mainloop()