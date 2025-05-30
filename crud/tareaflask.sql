CREATE DATABASE IF NOT EXISTS `tareaflask` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

CREATE USER IF NOT EXISTS 'usertareaflask'@'%' IDENTIFIED BY 'cambiarcambiar';

GRANT SELECT, INSERT, UPDATE, DELETE ON `tareaflask`.* TO 'usertareaflask'@'%';

FLUSH PRIVILEGES;
