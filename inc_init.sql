--
-- 由SQLiteStudio v3.2.1 产生的文件 周五 七月 24 11:31:28 2020
--
-- 文本编码：UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- 表：car_activity
DROP TABLE IF EXISTS car_activity;

CREATE TABLE car_activity (
    id           INTEGER       PRIMARY KEY AUTOINCREMENT,
    car          VARCHAR (20)  NOT NULL,
    in_time      DATETIME,
    submit_time  DATETIME,
    submit_admin VARCHAR (10),
    submit_type  VARCHAR (20),
    submit_note  VARCHAR (200) 
);


-- 表：car_admin
DROP TABLE IF EXISTS car_admin;

CREATE TABLE car_admin (
    id             INTEGER,
    admin_name     VARCHAR (10)  NOT NULL,
    admin_password VARCHAR (32)  NOT NULL,
    admin_nick     VARCHAR (20),
    admin_mobile   INTEGER (11),
    admin_note     VARCHAR (200) 
);


-- 表：car_infos
DROP TABLE IF EXISTS car_infos;

CREATE TABLE car_infos (
    id           INTEGER      PRIMARY KEY AUTOINCREMENT,
    car_number   VARCHAR (20) NOT NULL,
    car_owner    VARCHAR (20) NOT NULL,
    car_type     VARCHAR (10) NOT NULL,
    car_mobile   INTEGER (11) NOT NULL,
    submit_time  DATETIME,
    submit_admin VARCHAR (10) 
);


-- 表：car_log
DROP TABLE IF EXISTS car_log;

CREATE TABLE car_log (
    id           INTEGER       PRIMARY KEY AUTOINCREMENT,
    car          VARCHAR (20)  NOT NULL,
    time         DATETIME      NOT NULL,
    type         VARCHAR (10)  NOT NULL,
    submit_time  DATETIME,
    submit_admin VARCHAR (10),
    submit_note  VARCHAR (250) 
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
