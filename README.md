# Car_access_system
https://github.com/malimaliao/Car_access_system


一个python学习测试作品，基于腾讯云+百度云API车牌识别系统，并采用flask构建的车辆出入登记。


***
### 运行环境

#### 核心环境
* Python 3
* Flask 1.1.2
* sqlite3

#### 扩展环境
* 支持rtsp://协议的摄像头

***
### 依赖库
* tencentcloud-sdk-python 3.0.223
* opencv-python 4.3.0.36
* configobj 5.0.6
* numpy 1.19.1
* requests 2.24.0

***
### 发现BUG
* camera.py 在接收rtsp的视频流，偶尔会触发错误：cv2.imencode('.jpg', None)


