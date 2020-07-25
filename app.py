# -*- coding:utf-8 -*-
# -*- 人生苦短，Python当歌
# sqlite
from __future__ import with_statement
from contextlib import closing
import sqlite3
# flask
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response
# core
import os
import datetime
import base64
import json
# 自定义
from camera import VideoCamera

# 腾讯SDK
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

# ini
from configobj import ConfigObj

app = Flask(__name__)

APP_name = 'Car Access System'
APP_description = '暂无介绍'
APP_version = '0.1'
APP_database = 'car_data.db'
APP_config_file = 'inc_config.ini'

APP_basedir = os.path.abspath(os.path.dirname(__file__))  # 取当前程序运行目录，D:\MyPython\test\QQ_bar
APP_file_type = ['png', 'jpg', 'jpeg']
APP_uploads = os.path.join(APP_basedir, 'static', 'uploads')

# flask 登录会话所需参数
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config['SECRET_KEY'] = 'c9d20df0366cec4e7561c0'  # flask会话所需，防止csrf跨站所需秘钥变量，暂时没什么用


# 初始化数据库
def init_db():
    # 通过sql脚本提交方式，初始化并建立一个数据库
    with closing(connect_db()) as db:
        with app.open_resource('inc_init.sql') as f:
            sql = f.read().decode('utf-8')
            db.cursor().executescript(sql)
        db.commit()


def connect_db():
    return sqlite3.connect(APP_database)


# 获取摄像头视频帧图像
def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# flask 请求
@app.before_request
def before_request():
    g.db = connect_db()


# flask 请求结束
@app.after_request
def after_request(response):
    g.db.close()
    return response


# flask 自定义错误
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# 网站根目录
@app.route('/')
def system_index():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    _camera_in_rtsp_img = APP_config_ini['camera_in']['rtsp']
    if _camera_in_rtsp_img == "":
        _camera_in_rtsp_img = '/static/img/live.jpg'
    else:
        _camera_in_rtsp_img = '/api/camera_live_in'
    _camera_out_rtsp_img = APP_config_ini['camera_out']['rtsp']
    if _camera_out_rtsp_img == "":
        _camera_out_rtsp_img = '/static/img/live.jpg'
    else:
        _camera_out_rtsp_img = '/api/camera_live_out'
    return render_template(
        'index.html',
        app_config_camera_in_rtsp_img=_camera_in_rtsp_img,
        app_config_camera_in_web=APP_config_ini['camera_in']['web'],
        app_config_camera_in_name=APP_config_ini['camera_in']['name'],
        app_config_camera_in_note=APP_config_ini['camera_in']['note'],
        app_config_camera_out_rtsp_img=_camera_out_rtsp_img,
        app_config_camera_out_web=APP_config_ini['camera_out']['web'],
        app_config_camera_out_name=APP_config_ini['camera_out']['name'],
        app_config_camera_out_note=APP_config_ini['camera_in']['note'],
    )


# /login/
@app.route('/login/')
def system_login():
    return render_template('login.html', APP_version=APP_version, APP_name=APP_name, APP_description=APP_description)


# /login_check/
@app.route('/login_check/', methods=['POST'])
def system_login_check():
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    _config_admin_user = APP_config_ini['system']['admin_user']
    _config_admin_pass = APP_config_ini['system']['admin_pass']
    if _config_admin_user == '' or _config_admin_pass == '':
        flash('不允许使用空账号密码登录！')
        return redirect(url_for('system_login'))
    if _config_admin_user == 'admin' and _config_admin_pass == 'admin':
        flash('系统现在无法让您登录！因为安全考虑，您必须先在系统文件夹下修改inc_config.ini文件中的默认账号密码后，才可以进行登录')
        return redirect(url_for('system_login'))
    else:
        _login_user = request.form.get('login_user')
        _login_pass = request.form.get('login_pass')
        if _login_user == _config_admin_user and _login_pass == _config_admin_pass:
            session['APP_system_user'] = _login_user
            session['APP_system_pass'] = _login_pass
            return redirect(url_for('system_index'))
        else:
            flash('账号密码不正确！')  # 密码错误！
            return redirect(url_for('system_login'))


# /logout/
@app.route('/logout/')
def logout():
    session.pop('APP_system_user')  # 删除session
    session.pop('APP_system_pass')  # 删除session
    flash('您已退出登录！')  # 密码错误！
    return redirect(url_for('system_login'))


# 配置表单(管理后台配置)
@app.route('/system/config/')
def system_config():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    return render_template(
        'config.html',
        app_config_system_admin_user=APP_config_ini['system']['admin_user'],
        app_config_system_admin_pass=APP_config_ini['system']['admin_pass'],
        app_config_camera_in_ip=APP_config_ini['camera_in']['ip'],
        app_config_camera_in_web=APP_config_ini['camera_in']['web'],
        app_config_camera_in_name=APP_config_ini['camera_in']['name'],
        app_config_camera_in_rtsp=APP_config_ini['camera_in']['rtsp'],
        app_config_camera_in_note=APP_config_ini['camera_in']['note'],
        app_config_camera_out_ip=APP_config_ini['camera_out']['ip'],
        app_config_camera_out_web=APP_config_ini['camera_out']['web'],
        app_config_camera_out_name=APP_config_ini['camera_out']['name'],
        app_config_camera_out_rtsp=APP_config_ini['camera_out']['rtsp'],
        app_config_camera_out_note=APP_config_ini['camera_in']['note'],
        app_config_tencent_sdk_api_id=APP_config_ini['tencent_sdk']['api_id'],
        app_config_tencent_sdk_api_key=APP_config_ini['tencent_sdk']['api_key'],
        app_config_tencent_sdk_api_area=APP_config_ini['tencent_sdk']['api_area'],
    )


# 配置保存
@app.route('/system/config/save', methods=['POST'])
def system_config_save():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    _app_config_system_admin_user = request.form.get('system_admin_user')
    _app_config_system_admin_pass = request.form.get('system_admin_pass')
    _app_config_camera_in_ip = request.form.get('camera_in_ip')
    _app_config_camera_in_web = request.form.get('camera_in_web')
    _app_config_camera_in_name = request.form.get('camera_in_name')
    _app_config_camera_in_rtsp = request.form.get('camera_in_rtsp')
    _app_config_camera_in_note = request.form.get('camera_in_note')
    _app_config_camera_out_ip = request.form.get('camera_out_ip')
    _app_config_camera_out_web = request.form.get('camera_out_web')
    _app_config_camera_out_name = request.form.get('camera_out_name')
    _app_config_camera_out_rtsp = request.form.get('camera_out_rtsp')
    _app_config_camera_out_note = request.form.get('camera_out_note')
    _app_config_tencent_sdk_api_id = request.form.get('tencent_sdk_api_id')
    _app_config_tencent_sdk_api_key = request.form.get('tencent_sdk_api_key')
    _app_config_tencent_sdk_api_area = request.form.get('tencent_sdk_api_area')
    print(_app_config_system_admin_user, _app_config_camera_in_note, _app_config_camera_out_note)
    if _app_config_system_admin_user == '' or _app_config_system_admin_pass == '':
        print('账号密码不能为空')
        flash(u'账号密码不能为空!', 'msg_error')  # 用flash()向下一个请求闪现一条信息
    else:
        APP_config_ini['camera_in']['ip'] = _app_config_camera_in_ip
        APP_config_ini['camera_in']['web'] = _app_config_camera_in_web
        APP_config_ini['camera_in']['name'] = _app_config_camera_in_name
        APP_config_ini['camera_in']['rtsp'] = _app_config_camera_in_rtsp
        APP_config_ini['camera_in']['note'] = _app_config_camera_in_note

        APP_config_ini['camera_out']['ip'] = _app_config_camera_out_ip
        APP_config_ini['camera_out']['web'] = _app_config_camera_out_web
        APP_config_ini['camera_out']['name'] = _app_config_camera_out_name
        APP_config_ini['camera_out']['rtsp'] = _app_config_camera_out_rtsp
        APP_config_ini['camera_out']['note'] = _app_config_camera_out_note

        APP_config_ini['tencent_sdk']['api_id'] = _app_config_tencent_sdk_api_id
        APP_config_ini['tencent_sdk']['api_key'] = _app_config_tencent_sdk_api_key
        APP_config_ini['tencent_sdk']['api_area'] = _app_config_tencent_sdk_api_area

        APP_config_ini['system']['admin_user'] = _app_config_system_admin_user
        APP_config_ini['system']['admin_pass'] = _app_config_system_admin_pass
        APP_config_ini.write()
        flash(u'修改成功!', 'msg_ok')  # 用flash()向下一个请求闪现一条信息
    return redirect(url_for('system_config'))  # 重定向，跳转


# 上传表单(web调试用，后面计划更改为ajax返回测试结果)
@app.route('/system/upload/test/')
def system_upload_img():
    return render_template('upload.html')


# api ：车牌号图片上传服务器+ 腾讯识别（返回car）
@app.route('/api/v1/upload', methods=['GET', 'POST'])
def system_upload_car_img():
    _car = dict()
    img = request.files.get('uploadedfile')  # 获取图片文件，E4A上传器固定name
    _file_name = img.filename  # test.jpg
    _file_type = _file_name.split(".")[1]  # jpg
    if _file_type in APP_file_type:
        _save_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S_%f')
        _save_name = _save_time + '.' + _file_type  # 图片名称，以时间+文件后缀命名
        _save_path = os.path.join(APP_basedir, 'static', 'uploads', _save_name)
        img.save(_save_path)  # 保存图片
        print('上传图片：' + _file_name, '保存位置：' + _save_path)
        # 腾讯api处理 开始 =============================================
        print('识别图片：' + _save_path)
        img_base64 = img_to_base64(_save_path)
        # print(img_base64)
        _car = Tencent_car_api(img_base64)
        # _car['data'] = {"Number": "渝AN7968", "Confidence": 99, "RequestId": "bc9f8509-1d4b-4990-9557-03b0f17e7eba"}
        # _car['code'] = 1（识别成功），0（识别失败）
        # 腾讯api处理 结束 =============================================
    else:
        _car['code'] = -1  # -1 不支持的图片格式
        _car['data'] = ''
        _car['error'] = '不支持的图片格式'
        _car['car_code_service'] = '1.0'  # 该字段将作为E4A APP校验内容是否是所需的json格式返回

    print(_car)
    _car = json.dumps(_car)
    return _car


# api 摄像头web直播 in
@app.route('/api/camera_live_in')
def system_video_feed_in():
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    camera_url = APP_config_ini['camera_in']['rtsp']
    return Response(gen(VideoCamera(camera_url)), mimetype='multipart/x-mixed-replace; boundary=frame')


# api 摄像头web直播 out
@app.route('/api/camera_live_out')
def system_video_feed_out():
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    camera_url = APP_config_ini['camera_out']['rtsp']
    return Response(gen(VideoCamera(camera_url)), mimetype='multipart/x-mixed-replace; boundary=frame')


# api 摄像头web拍照 in
@app.route('/api/camera_screen_in')
def system_camera_screen_in():
    _car = dict()
    _save_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S_%f')
    _save_path = os.path.join(APP_basedir, 'static', 'uploads', _save_time)  # 保存路径 d:\test\2020151413_303 ，不含后缀
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    camera_url = APP_config_ini['camera_in']['rtsp']
    if camera_url == '':
        print('in 摄像头未配置')
        return 'in 摄像头未配置'
    _save_file = VideoCamera(camera_url).get_screen(_save_path)
    print('拍照存储：', _save_file)
    # 腾讯api处理 开始 =============================================
    print('识别图片：', _save_file)
    img_base64 = img_to_base64(_save_file)
    _car = Tencent_car_api(img_base64)
    # 腾讯api处理 结束 =============================================
    print('识别结果：', _car)
    if _car['code'] == 1:
        #  D:\MyPython\test\QQ_bar\static\uploads\20200723174136_554780.jpg
        os.rename(_save_file, _save_file.replace(_save_time, _save_time + '_' + _car['number']))
    return _car


# api 摄像头web拍照 out
@app.route('/api/camera_screen_out')
def system_camera_screen_out():
    _car = dict()
    _save_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S_%f')
    _save_path = os.path.join(APP_basedir, 'static', 'uploads', _save_time)  # 保存路径 d:\test\2020151413_303 ，不含后缀
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    camera_url = APP_config_ini['camera_out']['rtsp']
    if camera_url == '':
        print('out 摄像头未配置')
        return 'out 摄像头未配置'
    _save_file = VideoCamera(camera_url).get_screen(_save_path)
    print('拍照存储：', _save_file)
    # 腾讯api处理 开始 =============================================
    print('识别图片：', _save_file)
    img_base64 = img_to_base64(_save_file)
    _car = Tencent_car_api(img_base64)
    # 腾讯api处理 结束 =============================================
    print('识别结果：', _car)
    if _car['code'] == 1:
        #  D:\MyPython\test\QQ_bar\static\uploads\20200723174136_554780.jpg
        os.rename(_save_file, _save_file.replace(_save_time, _save_time + '_' + _car['number']))
    return _car


# 腾讯车牌识别API ，返回一个字典 {'code':1, 'data': '识别失败, 'error': 'OCR无法识别'}
def Tencent_car_api(img_base64):
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    car = dict()
    try:
        cred = credential.Credential(APP_config_ini['tencent_sdk']['api_id'], APP_config_ini['tencent_sdk']['api_key'])
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ocr_client.OcrClient(cred, APP_config_ini['tencent_sdk']['api_area'], clientProfile)

        req = models.LicensePlateOCRRequest()
        params = '{\"ImageBase64\":\"' + img_base64 + '\"}'
        req.from_json_string(params)

        resp = client.LicensePlateOCR(req)
        # print(resp.to_json_string())
        # {"Number": "渝AN7968", "Confidence": 99, "RequestId": "bc9f8509-1d4b-4990-9557-03b0f17e7eba"}
        _json_data_text = resp.to_json_string()  # json格式化的文本字符串
        _json_data_dict = json.loads(_json_data_text)  # 将腾讯json字符串转换为字典

        car['number'] = _json_data_dict['Number']
        car['confidence'] = _json_data_dict['Confidence']
        car['requestId'] = _json_data_dict['RequestId']

        car['code'] = 1
        car['data'] = '识别成功'
        car['error'] = ''
        car['car_code_service'] = '1.0'  # 该字段将作为E4A APP校验内容是否是所需的json格式返回
    except TencentCloudSDKException as err:
        car['code'] = 0
        car['data'] = '识别出错'
        car['car_code_service'] = '1.0'  # 该字段将作为E4A APP校验内容是否是所需的json格式返回
        error = str(err)
        print(error)
        if 'FailedOperation.DownLoadError' in error:
            car['error'] = '文件下载失败'
        if 'FailedOperation.ImageDecodeFailed' in error:
            car['error'] = '图片解码失败'
        if 'FailedOperation.OcrFailed' in error:
            car['error'] = 'OCR识别失败'
        if 'FailedOperation.UnKnowError' in error:
            car['error'] = '未知错误'
        if 'FailedOperation.UnOpenError' in error:
            car['error'] = '服务未开通'
        if 'LimitExceeded.TooLargeFileError' in error:
            car['error'] = '文件内容太大'
        if 'ResourcesSoldOut.ChargeStatusException' in error:
            car['error'] = '云识别系统计费状态异常'
        if 'secret id should not be none' in error:
            car['error'] = '云识别系统未配置'
    return car


# 图片转换base64
def img_to_base64(img_file):
    with open(img_file, "rb") as f:  # 转为二进制格式
        base64_data_bytes = base64.b64encode(f.read())  # 使用base64进行加密,bytes类型
        base64_data_str = base64_data_bytes.decode()  # python3 转换为str
        ext = img_file.split(".")[-1]  # 取文件后缀名
        src = "data:image/{ext};base64,{data}".format(ext=ext, data=base64_data_str)  # 拼接含格式介绍的base64文本
        return src


if __name__ == '__main__':
    if os.path.exists(APP_database):
        print('--- 载入数据库', APP_database)
    else:
        print('--- 初始数据库', APP_database)
        init_db()
    if os.path.exists(APP_uploads):
        print('--- 读入上传库 ', APP_uploads)
    else:
        print('--- 初始图片库 ', APP_uploads)
        os.makedirs(APP_uploads)
    if not os.path.exists(APP_config_file):
        print('--- 初始配置文件 ', APP_config_file)
        APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
        APP_config_ini['camera_in'] = {}
        APP_config_ini['camera_in']['ip'] = '192.168.1.101'
        APP_config_ini['camera_in']['web'] = 'http://192.168.1.101:8080'
        APP_config_ini['camera_in']['name'] = 'A1'
        APP_config_ini['camera_in']['rtsp'] = ''
        APP_config_ini['camera_in']['note'] = ''
        APP_config_ini['camera_out'] = {}
        APP_config_ini['camera_out']['ip'] = '192.168.1.102'
        APP_config_ini['camera_out']['web'] = 'http://192.168.1.102:8080'
        APP_config_ini['camera_out']['name'] = 'A2'
        APP_config_ini['camera_out']['rtsp'] = ''
        APP_config_ini['camera_out']['note'] = ''
        APP_config_ini['tencent_sdk'] = {}
        APP_config_ini['tencent_sdk']['api_id'] = ''
        APP_config_ini['tencent_sdk']['api_key'] = ''
        APP_config_ini['tencent_sdk']['api_area'] = ''
        APP_config_ini['system'] = {}
        APP_config_ini['system']['admin_user'] = 'admin'
        APP_config_ini['system']['admin_pass'] = 'admin'
        APP_config_ini.write()
    # flask run
    app.run(host='0.0.0.0', port=5000, debug=True)
