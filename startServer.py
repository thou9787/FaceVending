# Vending Machine

# plug in web server
from flask import Flask, render_template, request, redirect

# video capture
from tkinter import *
import tkinter as tk
import tkinter.messagebox as tkmb
from PIL import ImageTk as itk, Image
import cv2

# face recognition
import sys,os,dlib,glob,numpy
from skimage import io
#import cv2
import imutils

from shutil import copyfile
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World!'

def captureFace(filePath):
    cap = cv2.VideoCapture(0)
    #i=1
    while(True):
    
        #從攝影機擷取影像
        ret, frame = cap.read()
        cv2.imshow("type Enter: confirm, ESC: cancel ", frame)
        k = cv2.waitKey(1) & 0xFF
    
        if k == 27:
            break
        #elif k==ord('s'):
        elif k == 13:            
            cv2.imwrite(filePath, frame)
            #i+=1
            break
        #圖片名改成username比較好
        #改成server路徑
    
    cap.release()
    cv2.destroyAllWindows()

def recognitionFace(filePath):
    # 人臉68特徵點模型路徑
    predictor_path = "shape_predictor_68_face_landmarks.dat"

    # 人臉辨識模型路徑
    face_rec_model_path = "dlib_face_recognition_resnet_model_v1.dat"

    # 比對人臉圖片資料夾名稱(之後要改成server資料夾)
    faces_folder_path = "./rec"

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
    if (len(cd_sorted) > 0):
        return cd_sorted[ 0][ 0]
    else:
        return 'failure'

@app.route('/Capture/<fileName>')
def Capture(fileName):
    tempFile = 'D:/openCVimage/' + fileName
    captureFace(tempFile)
    copyfile(tempFile, 'rec/' + fileName)
    
    return redirect('http://localhost/VendingMachine/')

@app.route('/Recognition')
def Recognition():
    tempFile = 'openCVimage/' + str(int(datetime.now().timestamp())) + '.jpg'
    captureFace(tempFile)
    resultFileName = recognitionFace(tempFile)
    redirectUrl = 'http://localhost/VendingMachine/Controller/faceLogin.php?faceFile=' + resultFileName
    
    #redirect(redirectUrl)
    return redirect(redirectUrl)

@app.route('/checkkey')
def CheckKey():
    while(True):
        k = cv2.waitKey(1) & 0xFF    
        if k == 27:
            break
    
    return str(k)

if __name__ == '__main__':
    app.run(debug=True)




