-- 1. Primero borro y creo la base de datos

DROP DATABASE IF EXISTS `tareaflask`;
CREATE DATABASE IF NOT EXISTS `tareaflask`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;
USE `tareaflask`;

-- 2. Tabla para los usuarios que se van a registrar

CREATE TABLE `usuarios` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `usuario` VARCHAR(100) NOT NULL,
  `hash` VARCHAR(150) NOT NULL,
  `tema` TINYINT(1) NOT NULL DEFAULT 0,     -- 0: tema claro, 1: tema oscuro
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuario` (`usuario`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci;

-- 3. Tabla para guardar los brokers de cada usuario

CREATE TABLE `brokers` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `dominio` VARCHAR(150) NOT NULL,
  `usuario_broker` VARCHAR(100) NOT NULL,
  `pass_encrypted` TEXT NOT NULL,
  `puerto_tls` INT(11) NOT NULL,
  `usuario_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_brokers_usuario_id` (`usuario_id`),
  CONSTRAINT `fk_brokers_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios`(`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci;


-- 4. Tabla para los dispositivos/nodos de cada usuario
--     - Un usuario no puede tener dos veces el mismo dispositivo
--     - Pero diferentes usuarios sí pueden tener el mismo dispositivo

CREATE TABLE `nodos` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `id_dispositivo` VARCHAR(50) NOT NULL,
  `broker_id` INT(11) NOT NULL,
  `usuario_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_nodos_broker_id` (`broker_id`),
  KEY `idx_nodos_usuario_id` (`usuario_id`),
  CONSTRAINT `fk_nodos_brokers`
    FOREIGN KEY (`broker_id`)
    REFERENCES `brokers`(`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_nodos_usuarios`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `usuarios`(`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  UNIQUE KEY `uq_usuario_dispositivo` (`usuario_id`, `id_dispositivo`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci;

-- 5. Creo el usuario de MySQL y le doy permisos

CREATE USER IF NOT EXISTS 'usertareaflask'@'%' 
  IDENTIFIED BY 'cambiarcambiar';

GRANT SELECT, INSERT, UPDATE, DELETE
  ON `tareaflask`.* 
  TO 'usertareaflask'@'%';

FLUSH PRIVILEGES;
