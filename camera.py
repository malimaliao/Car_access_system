# -*- coding:utf-8 -*-
# -*- 人生苦短，Python当歌
import cv2
import numpy as np


# 获取摄像头视频流，将图像流转换为图帧
class VideoCamera(object):
    def __init__(self, rtsp_url):
        self.cap = cv2.VideoCapture(rtsp_url)

    def __del__(self):
        self.cap.release()

    def get_frame(self):
        ret, frame_image = self.cap.read()
        if ret is False:
            print('debug：截获空图像，输出无信号动作 >>>')
            frame_image = cv2.imread('none.jpg')
        ret, jpeg = cv2.imencode('.jpg', frame_image)  # 从网络读取图像数据并压缩编码转换成图片格式
        return jpeg.tobytes()

    def get_screen(self, save_path):
        ret, frame_img = self.cap.read()
        img_file = save_path + '.jpg'
        cv2.imwrite(img_file, frame_img)  # 存储为图像
        return img_file


# 获取摄像头截图
'''
def get_img_from_camera_net(folder_path):
    cap = cv2.VideoCapture("rtsp://admin:12345@172.33.9.171/h264/ch1/main/av_stream")
    i = 1
    while i < 3:
        ret, frame = cap.read()
        cv2.imshow("capture", frame)
        print(str(i))
        cv2.imwrite(folder_path + str(i) + '.jpg', frame)  # 存储为图像
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        i += 1
    cap.release()
    cv2.destroyAllWindows()
'''