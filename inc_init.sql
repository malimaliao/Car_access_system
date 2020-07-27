--
-- 由SQLiteStudio v3.2.1 产生的文件 周一 七月 27 10:59:17 2020
--
-- 文本编码：UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- 表：activity
DROP TABLE IF EXISTS activity;

CREATE TABLE activity (
    id          INTEGER       PRIMARY KEY AUTOINCREMENT
                              UNIQUE
                              NOT NULL,
    car_number  VARCHAR (20)  NOT NULL
                              UNIQUE,
    in_time     DATETIME,
    submit_time DATETIME,
    submit_ip   VARCHAR (32),
    submit_user VARCHAR (10),
    submit_note VARCHAR (200) 
);


-- 表：admin
DROP TABLE IF EXISTS admin;

CREATE TABLE admin (
    admin_id       INTEGER       PRIMARY KEY
                                 NOT NULL
                                 UNIQUE,
    admin_user     VARCHAR (10)  NOT NULL
                                 UNIQUE,
    admin_password VARCHAR (32)  NOT NULL,
    admin_nick     VARCHAR (20),
    admin_mobile   INTEGER (11),
    admin_note     VARCHAR (200),
    submit_time    DATETIME,
    submit_user    VARCHAR (20),
    submit_ip      VARCHAR (32) 
);


-- 表：car
DROP TABLE IF EXISTS car;

CREATE TABLE car (
    car_id      INTEGER       PRIMARY KEY AUTOINCREMENT
                              NOT NULL
                              UNIQUE,
    car_number  VARCHAR (20)  NOT NULL
                              UNIQUE,
    car_owner   VARCHAR (20)  NOT NULL,
    car_mobile  INTEGER (11)  NOT NULL,
    car_note    VARCHAR (200),
    submit_time DATETIME,
    submit_user VARCHAR (10),
    submit_ip   VARCHAR (32),
    update_time DATETIME,
    update_ip   VARCHAR (32),
    update_user VARCHAR (10),
    class_id    INTEGER (5)   NOT NULL
);


-- 表：class
DROP TABLE IF EXISTS class;

CREATE TABLE class (
    class_id     INTEGER       PRIMARY KEY AUTOINCREMENT
                               NOT NULL
                               UNIQUE,
    class_name   VARCHAR (10)  NOT NULL
                               UNIQUE,
    class_note   VARCHAR (200),
    submit_time  DATETIME,
    submit_user  VARCHAR (10),
    submit_ip    VARCHAR (32),
    parking_list VARCHAR (30) 
);


-- 表：log
DROP TABLE IF EXISTS log;

CREATE TABLE log (
    log_id      INTEGER       PRIMARY KEY AUTOINCREMENT,
    car_number  VARCHAR (20)  NOT NULL,
    log_time    DATETIME      NOT NULL,
    log_type    VARCHAR (10)  NOT NULL,
    submit_time DATETIME,
    submit_user VARCHAR (10),
    submit_ip   VARCHAR (32),
    submit_note VARCHAR (250) 
);


-- 表：parking
DROP TABLE IF EXISTS parking;

CREATE TABLE parking (
    parking_id   INTEGER       PRIMARY KEY AUTOINCREMENT,
    parking_name VARCHAR (20)  NOT NULL,
    parking_sum  INTEGER       NOT NULL,
    parking_note VARCHAR (255),
    submit_time  DATETIME,
    submit_user  VARCHAR (10),
    submit_ip    VARCHAR (32) 
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
