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
# HTTP
import requests
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


# 连接数据库
def connect_db():
    return sqlite3.connect(APP_database)


# 根据语句查询数量
def db_query_sum(sql_text):
    try:
        cur = g.db.execute(sql_text)
        data = cur.fetchall()
        return len(data)
    except sqlite3.Error as e:
        return -1


# 获取摄像头视频帧图像
def gen(camera, rtsp_url):
    while True:
        frame = camera.get_frame(rtsp_url)
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
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    _config_admin_user = APP_config_ini['system']['admin_user']
    _config_admin_pass = APP_config_ini['system']['admin_pass']
    if _config_admin_user == 'admin' and _config_admin_pass == 'admin':
        flash('出于安全考虑，系统现在无法让您登录！'
              '您必须先在系统文件夹下修改inc_config.ini文件中的默认账号密码后，再次刷新本网页才可以进行登录。')
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
        app_config_system_sdk=APP_config_ini['system']['sdk'],
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
        app_config_baidu_sdk_api_ak=APP_config_ini['baidu_sdk']['AppID'],
        app_config_baidu_sdk_api_ck=APP_config_ini['baidu_sdk']['APIKey'],
    )


# 配置保存
@app.route('/system/config/save', methods=['POST'])
def system_config_save():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    _app_config_system_admin_user = request.form.get('system_admin_user')
    _app_config_system_admin_pass = request.form.get('system_admin_pass')
    _app_config_system_sdk = request.form.get('system_sdk')
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
    _app_config_baidu_sdk_ak = request.form.get('baidu_sdk_api_ak')
    _app_config_baidu_sdk_ck = request.form.get('baidu_sdk_api_ck')
    # print(_app_config_system_admin_user, _app_config_camera_in_note, _app_config_camera_out_note)
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

        APP_config_ini['baidu_sdk']['AppID'] = _app_config_baidu_sdk_ak
        APP_config_ini['baidu_sdk']['APIKey'] = _app_config_baidu_sdk_ck

        APP_config_ini['system']['admin_user'] = _app_config_system_admin_user
        APP_config_ini['system']['admin_pass'] = _app_config_system_admin_pass
        APP_config_ini['system']['sdk'] = _app_config_system_sdk
        APP_config_ini.write()
        flash(u'修改成功!', 'msg_ok')  # 用flash()向下一个请求闪现一条信息
    return redirect(url_for('system_config'))  # 重定向，跳转


# 车辆登记列表
@app.route('/car/list/')
def system_car_list():
    try:
        cur = g.db.execute('SELECT * FROM car;')
        data = cur.fetchall()
        return render_template('car_list.html', data_list=data)
    except sqlite3.Error as e:
        flash(u'数据库出现异常，此功能暂时不可用！' + str(e), 'msg_error')
        return render_template('car_list.html', data_list=[])


# 车辆登记 列表
@app.route('/car/add/')
def system_car_add():
    region_list = ['京', '津', '沪', '黑', '吉', '辽', '蒙', '晋', '陕', '甘', '青', '新', '宁', '冀', '鲁', '豫', '苏',
                   '浙', '皖', '湘', '鄂', '赣', '川', '黔', '滇', '桂', '粤', '闽', '藏', '琼', '渝', '台', '港', '澳']
    try:
        cur = g.db.execute('SELECT * FROM class;')
        data = cur.fetchall()
        return render_template('car_add.html', region_list=region_list, data_list=data)
    except sqlite3.Error as e:
        flash(u'数据库出现异常，此功能暂时不可用！' + str(e), 'msg_error')
        return render_template('car_add.html', region_list=region_list, data_list=[])


# 车辆登记 保存
@app.route('/car/add/save', methods=['POST'])
def system_car_add_save():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    _car_region = request.form.get('car_region')
    _car_code = request.form.get('car_code')
    _car_owner = request.form.get('car_owner')
    _car_mobile = request.form.get('car_mobile')
    _car_note = request.form.get('car_note')
    _class_id = request.form.get('class_id')
    if _car_region is None or _car_code is None or _car_owner is None or _car_mobile is None or _class_id is None:
        flash(u'缺少必要参数，请检查必填项或必选项是否都正确填写或选择！', 'msg_error')
        return redirect(url_for('system_car_add'))
    if _car_region == '' or _car_code == '' or _car_owner == '' or _car_mobile == '' or _class_id == '':
        flash(u'必要参数不能为空值！车牌号、车主、手机号码、车辆分类都是必须的', 'msg_warning')
        return redirect(url_for('system_car_add'))
    # 审查 查重
    _car_number = _car_region + _car_code
    if db_query_sum("SELECT car_number FROM car WHERE car_number = '" + _car_number + "'") > 0:
        flash(u'该条目已存在，无需再次添加！重复的项为：' + _car_number, 'msg_warning')
        return redirect(url_for('system_car_add'))
    # 审查OK 开始写库
    _post_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _post_user = session.get('APP_system_user')
    _post_ip = request.remote_addr
    _post_data = [_car_number, _car_owner, _car_mobile, _car_note, _post_time, _post_user, _post_ip, _class_id]
    try:
        g.db.execute('INSERT INTO car (car_number, car_owner, car_mobile, car_note, submit_time, submit_user, submit_ip, class_id) values (?, ?, ?, ?, ?, ?, ?, ?)', _post_data)
        g.db.commit()
        flash(u'您成功添加了一条数据！', 'msg_ok')
        return redirect(url_for('system_car_list'))
    except sqlite3.Error as e:
        flash(u'数据提交失败！' + str(e), 'msg_error')
        return redirect(url_for('system_car_add'))


#  根据传入的list字符查询车位区域列表
def db_query_parking(parking_list_text):
    parking_list = []
    _parking_list = parking_list_text.split(",")
    for _parking in _parking_list:
        try:
            cur = g.db.execute("SELECT * FROM parking WHERE parking_id = '" + _parking + "';")
            park_list = cur.fetchall()
            # print('db_query_parking()', park_list)
            parking_list.append(park_list)
        except sqlite3.Error as e:
            print('db_query_parking()', '查询错误')
    return parking_list


app.add_template_global(db_query_parking, 'db_query_parking')  # flask 在jinja2模板引擎注册一个自定义函数


# 车辆类型 列表
@app.route('/class/list/')
def system_class_list():
    try:
        cur = g.db.execute('SELECT * FROM class;')
        data = cur.fetchall()
        return render_template('class_list.html', data_list=data)
    except sqlite3.Error as e:
        flash(u'数据库出现异常，此功能暂时不可用！' + str(e), 'msg_error')
        return render_template('class_list.html', data_list=[])


# 车辆类型 新建
@app.route('/class/add/')
def system_class_add():
    try:
        cur = g.db.execute('SELECT * FROM parking;')
        parking_list = cur.fetchall()
        return render_template('class_add.html', parking_list=parking_list)
    except sqlite3.Error as e:
        flash(u'数据库出现异常，此功能暂时不可用！' + str(e), 'msg_error')
        return render_template('class_add.html', parking_list=[])


# 车辆类别 保存
@app.route('/class/add/save', methods=['POST'])
def system_class_add_save():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    _class_name = request.form.get('car_type_name')
    _class_note = request.form.get('car_type_note')
    _class_parking_list = request.values.getlist("car_parking")
    if _class_name is None or _class_note is None or _class_parking_list is None:
        flash(u'缺少参数!', 'msg_error')
        return redirect(url_for('system_class_add'))
    if _class_name == '':
        flash(u'必要参数不能为空值!', 'msg_error')
        return redirect(url_for('system_class_add'))
    if len(_class_parking_list) < 1:
        flash(u'车位权限区域不能为空，您建立该类别应该至少指定一个停放车位区域权限', 'msg_error')
        return redirect(url_for('system_class_add'))
    if db_query_sum("SELECT class_name FROM class WHERE class_name = '" + _class_name + "'") > 0:
        flash(u'该条目已存在，无需再次添加！', 'msg_warning')
        return redirect(url_for('system_class_add'))
    # 审查ok 开始写库
    _post_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _post_user = session.get('APP_system_user')
    _post_ip = request.remote_addr
    _post_parking = ','.join(_class_parking_list)
    _post_data = [_class_name, _class_note, _post_time, _post_user, _post_ip, _post_parking]
    try:
        g.db.execute('INSERT INTO class (class_name, class_note, submit_time, submit_user, submit_ip, parking_list) values (?, ?, ?, ?, ?, ?)', _post_data)
        g.db.commit()
        flash(u'您成功添加了一条数据！', 'msg_ok')
        return redirect(url_for('system_class_list'))
    except sqlite3.Error as e:
        flash(u'数据提交失败！' + str(e), 'msg_error')
        return redirect(url_for('system_class_add'))


# 车位 列表
@app.route('/parking/list/')
def system_parking_list():
    try:
        cur = g.db.execute('SELECT * FROM parking;')
        data = cur.fetchall()
        return render_template('parking_list.html', data_list=data)
    except sqlite3.Error as e:
        flash(u'数据库出现异常，此功能暂时不可用！' + str(e), 'msg_error')
        return render_template('parking_list.html', data_list=[])


# 车位 新建
@app.route('/parking/add/')
def system_parking_add():
    return render_template('parking_add.html')


# 车位 保存
@app.route('/parking/add/save', methods=['POST'])
def system_parking_add_save():
    if not session.get('APP_system_user'):
        return redirect(url_for('system_login'))
    _parking_name = request.form.get('parking_name')
    _parking_sum = request.form.get('parking_sum')
    _parking_note = request.form.get('parking_note')
    if _parking_name is None or _parking_sum is None or _parking_note is None:
        flash(u'缺少参数!', 'msg_error')
        return redirect(url_for('system_parking_add'))
    if _parking_name == '' or _parking_sum == '':
        flash(u'必要参数不能为空值!', 'msg_error')
        return redirect(url_for('system_parking_add'))
    if db_query_sum("SELECT parking_name FROM parking WHERE parking_name = '" + _parking_name + "'") > 0:
        flash(u'该条目已存在，无需再次添加！', 'msg_warning')
        return redirect(url_for('system_parking_add'))
    # 审查ok 开始写库
    _post_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _post_user = session.get('APP_system_user')
    _post_ip = request.remote_addr
    _post_data = [_parking_name, _parking_sum, _parking_note, _post_time, _post_user, _post_ip]
    try:
        g.db.execute(
            'insert into parking (parking_name, parking_sum, parking_note, submit_time, submit_user, submit_ip) values (?, ?, ?, ?, ?, ?)',
            _post_data)
        # 使用问号标记来构建 SQL 语句。否则，当使用格式化字符串构建 SQL 语句时， 应用容易遭受 SQL 注入。
        g.db.commit()
        flash(u'您成功添加了一条数据！', 'msg_ok')
        return redirect(url_for('system_parking_list'))
    except sqlite3.Error as e:
        flash(u'数据提交失败！' + str(e), 'msg_error')
        return redirect(url_for('system_parking_add'))


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
        APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
        if APP_config_ini['system']['sdk'] == '1':
            _car = Tencent_car_api(img_base64)
        else:
            _car = baidu_car_api(img_base64)
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
    return Response(gen(VideoCamera(camera_url), camera_url), mimetype='multipart/x-mixed-replace; boundary=frame')


# api 摄像头web直播 out
@app.route('/api/camera_live_out')
def system_video_feed_out():
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    camera_url = APP_config_ini['camera_out']['rtsp']
    return Response(gen(VideoCamera(camera_url), camera_url), mimetype='multipart/x-mixed-replace; boundary=frame')


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
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    if APP_config_ini['system']['sdk'] == '1':
        _car = Tencent_car_api(img_base64)
    else:
        _car = baidu_car_api(img_base64)
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
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    if APP_config_ini['system']['sdk'] == '1':
        _car = Tencent_car_api(img_base64)
    else:
        _car = baidu_car_api(img_base64)
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


# 百度SDK
def baidu_car_api(img_base64):
    APP_config_ini = ConfigObj(APP_config_file, encoding='UTF8')
    car = dict()
    # 百度鉴权 START
    try:
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + APP_config_ini['baidu_sdk']['AppID'] + '&client_secret=' + APP_config_ini['baidu_sdk']['APIKey']
        response = requests.get(host)
        if response:
            _sdk_json = response.json()
            print('百度SDK：鉴权成功，' + _sdk_json['access_token'])
            if 'access_token' in _sdk_json:
                _sdk_token = _sdk_json['access_token']
                params = {"image": img_base64}
                request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/license_plate"
                request_url = request_url + "?access_token=" + _sdk_token
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                response = requests.post(request_url, data=params, headers=headers)
                _bd_api_json = response.json()
                if 'words_result' in _bd_api_json:
                    print('百度SDK：识别成功，', _bd_api_json['words_result'])
                    car['number'] = _bd_api_json['words_result']['number']
                    car['confidence'] = 99  # 可信度，此处百度与腾讯不同，拆分进行计算，后续改进，此处固定
                    car['requestId'] = _bd_api_json['log_id']
                    car['code'] = 1
                    car['data'] = '识别成功'
                    car['error'] = ''
                elif 'error_code' in _bd_api_json:
                    # print('百度SDK：识别失败，' + _bd_api_json['error_msg'])
                    car['code'] = 0
                    car['data'] = '识别出错'
                    car['error'] = '百度SDK：识别失败，' + _bd_api_json['error_msg']
                else:
                    # print('百度SDK：识别异常，', _bd_api_json)
                    car['code'] = 0
                    car['data'] = '识别出错'
                    car['error'] = '百度SDK：识别异常' + str(_bd_api_json)
            elif 'error' in _sdk_json:
                # print('百度SDK：鉴权请求失败，服务不可用' + _sdk_json['error'] + ',' + _sdk_json['error_description'])
                car['code'] = 0
                car['data'] = '识别出错'
                car['error'] = '百度SDK：鉴权请求失败，服务不可用' + _sdk_json['error'] + ',' + _sdk_json['error_description']
            else:
                # print('百度SDK：鉴权请求返回资源未知，服务不可用')
                car['code'] = 0
                car['data'] = '识别出错'
                car['error'] = '百度SDK：鉴权请求返回资源未知，服务不可用'
        else:
            # print('百度SDK：鉴权请求返回资源为空，服务不可用')
            car['code'] = 0
            car['data'] = '识别出错'
            car['error'] = '百度SDK：鉴权请求返回资源为空，服务不可用'
    except Exception as error:
        # print('百度SDK：鉴权请求访问失败，服务不可用', str(error))
        car['code'] = 0
        car['data'] = '识别出错'
        car['error'] = '百度SDK：鉴权请求访问失败，服务不可用' + str(error)
    # 汇聚结果
    car['car_code_service'] = '1.0'
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
        APP_config_ini['baidu_sdk'] = {}
        APP_config_ini['baidu_sdk']['AppID'] = ''
        APP_config_ini['baidu_sdk']['APIKey'] = ''
        APP_config_ini['system'] = {}
        APP_config_ini['system']['admin_user'] = 'admin'
        APP_config_ini['system']['admin_pass'] = 'admin'
        APP_config_ini['system']['sdk'] = 1
        APP_config_ini.write()
    # flask run
    app.run(host='0.0.0.0', port=5000, debug=True)
