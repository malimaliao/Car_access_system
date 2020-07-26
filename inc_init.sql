--
-- 由SQLiteStudio v3.2.1 产生的文件 周日 七月 26 17:41:34 2020
--
-- 文本编码：UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- 表：activity
CREATE TABLE activity (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, car_number VARCHAR (20) NOT NULL UNIQUE, in_time DATETIME, submit_time DATETIME, submit_ip VARCHAR (32), submit_user VARCHAR (10), submit_note VARCHAR (200));

-- 表：admin
CREATE TABLE admin (admin_id INTEGER PRIMARY KEY NOT NULL UNIQUE, admin_user VARCHAR (10) NOT NULL UNIQUE, admin_password VARCHAR (32) NOT NULL, admin_nick VARCHAR (20), admin_mobile INTEGER (11), admin_note VARCHAR (200), submit_time DATETIME, submit_user VARCHAR (20), submit_ip VARCHAR (32));

-- 表：car
CREATE TABLE car (car_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, car_number VARCHAR (20) NOT NULL UNIQUE, car_owner VARCHAR (20) NOT NULL, car_mobile INTEGER (11) NOT NULL, car_note VARCHAR (200), submit_time DATETIME, submit_user VARCHAR (10), submit_ip VARCHAR (32), update_time DATETIME, update_ip VARCHAR (32), update_user VARCHAR (10), class_id INTEGER (5) NOT NULL);
INSERT INTO car (car_id, car_number, car_owner, car_mobile, car_note, submit_time, submit_user, submit_ip, update_time, update_ip, update_user, class_id) VALUES (1, '粤B12345', '张三', 13800138000, '', '2020-07-26 17:33:38', 'admin', '127.0.0.1', NULL, NULL, NULL, 2);
INSERT INTO car (car_id, car_number, car_owner, car_mobile, car_note, submit_time, submit_user, submit_ip, update_time, update_ip, update_user, class_id) VALUES (2, '粤BN1341', '李四', 13800138000, '', '2020-07-26 17:34:10', 'admin', '127.0.0.1', NULL, NULL, NULL, 2);
INSERT INTO car (car_id, car_number, car_owner, car_mobile, car_note, submit_time, submit_user, submit_ip, update_time, update_ip, update_user, class_id) VALUES (3, '粤C9894', '林总', 13800138000, '', '2020-07-26 17:34:49', 'admin', '127.0.0.1', NULL, NULL, NULL, 1);
INSERT INTO car (car_id, car_number, car_owner, car_mobile, car_note, submit_time, submit_user, submit_ip, update_time, update_ip, update_user, class_id) VALUES (4, '京CK18911', '刘局长', 154415121, '', '2020-07-26 17:41:09', 'admin', '127.0.0.1', NULL, NULL, NULL, 1);

-- 表：class
CREATE TABLE class (class_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, class_name VARCHAR (10) NOT NULL UNIQUE, class_note VARCHAR (200), submit_time DATETIME, submit_user VARCHAR (10), submit_ip VARCHAR (32), parking_list VARCHAR (30));
INSERT INTO class (class_id, class_name, class_note, submit_time, submit_user, submit_ip, parking_list) VALUES (1, '客人', '客户、供应商、外来车辆', '2020-07-26 14:19:01', 'admin', '127.0.0.1', '1,3');
INSERT INTO class (class_id, class_name, class_note, submit_time, submit_user, submit_ip, parking_list) VALUES (2, '员工', '', '2020-07-26 14:25:37', 'admin', '127.0.0.1', '3');
INSERT INTO class (class_id, class_name, class_note, submit_time, submit_user, submit_ip, parking_list) VALUES (3, 'VP', 'VP、老板', '2020-07-26 14:26:13', 'admin', '127.0.0.1', '1,2,3');

-- 表：log
CREATE TABLE log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, car_number VARCHAR (20) NOT NULL, log_time DATETIME NOT NULL, log_type VARCHAR (10) NOT NULL, submit_time DATETIME, submit_user VARCHAR (10), submit_ip VARCHAR (32), submit_note VARCHAR (250));

-- 表：parking
CREATE TABLE parking (parking_id INTEGER PRIMARY KEY AUTOINCREMENT, parking_name VARCHAR (20) NOT NULL, parking_sum INTEGER NOT NULL, parking_note VARCHAR (255), submit_time DATETIME, submit_user VARCHAR (10), submit_ip VARCHAR (32));
INSERT INTO parking (parking_id, parking_name, parking_sum, parking_note, submit_time, submit_user, submit_ip) VALUES (1, '客户保留车位', 10, '给客户预留的车位', '2020-07-26 13:43:07', 'admin', '127.0.0.1');
INSERT INTO parking (parking_id, parking_name, parking_sum, parking_note, submit_time, submit_user, submit_ip) VALUES (2, 'VP车位', 10, '领导高层专属保留车位', '2020-07-26 14:02:31', 'admin', '127.0.0.1');
INSERT INTO parking (parking_id, parking_name, parking_sum, parking_note, submit_time, submit_user, submit_ip) VALUES (3, '普通车位', 80, '', '2020-07-26 14:02:47', 'admin', '127.0.0.1');
INSERT INTO parking (parking_id, parking_name, parking_sum, parking_note, submit_time, submit_user, submit_ip) VALUES (4, '保安', 5, '', '2020-07-26 14:55:20', 'admin', '127.0.0.1');

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
