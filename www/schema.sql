create database if not exists awesome;
use awesome;

create user 'wwwdata'@'localhost' identified by 'wwwdata';
grant select, insert, update, delete on awesome.* to 'wwwdata'@'localhost';

create table `users` (
  `id` varchar(50) not null,
  `name` varchar(50) not null,
  `passwd` varchar(50) not null,
  `image` varchar(500) not null,
  `email` varchar(50) not null,
  `admin` BOOLEAN not null,
  `createtime` DOUBLE not null,
  unique key `idx_email` (`email`),
  key `idx_createtime` (`createtime`),
  primary key(`id`)
) engine=innodb default charset=utf8mb4;

create table `blogs` (
  `id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(50) not null,
  `user_image` varchar(500) not null,
  `name` varchar(50) not null,
  `summary` varchar(200) not null,
  `content` MEDIUMTEXT not null,
  `createtime` DOUBLE not null,
  key `idx_createtime` (`createtime`),
  primary key(`id`)
) engine=innodb default charset=utf8mb4;

create table `comments` (
  `id` varchar(50) not null,
  `blog_id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(50) not null,
  `user_image` varchar(500) not null,
  `content` MEDIUMTEXT not null,
  `createtime` DOUBLE not null,
  key `idx_createtime` (`createtime`),
  primary key(`id`)
) engine=innodb default charset=utf8mb4;
