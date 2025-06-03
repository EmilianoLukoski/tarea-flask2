-- -----------------------------------------------------
-- 1. Eliminación (opcional) y creación de la base de datos
-- -----------------------------------------------------
DROP DATABASE IF EXISTS `tareaflask`;
CREATE DATABASE IF NOT EXISTS `tareaflask`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;
USE `tareaflask`;



-- -----------------------------------------------------
-- 2. Tabla de usuarios
-- -----------------------------------------------------
CREATE TABLE `usuarios` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `usuario` VARCHAR(100) NOT NULL,
  `hash` VARCHAR(150) NOT NULL,
  `tema` TINYINT(1) NOT NULL DEFAULT 0,     -- 0: claro, 1: oscuro
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuario` (`usuario`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci;



-- -----------------------------------------------------
-- 3. Tabla de brokers (vinculada a usuarios.id)
-- -----------------------------------------------------
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



-- -----------------------------------------------------
-- 4. Tabla de nodos/dispositivos (vinculada a brokers.id)
--     - Un mismo broker no podrá cargar dos veces el mismo id_dispositivo.
--     - Diferentes brokers (incluso de distinto usuario) pueden tener el mismo id_dispositivo.
-- -----------------------------------------------------
CREATE TABLE `nodos` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `id_dispositivo` VARCHAR(50) NOT NULL,
  `broker_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_nodos_broker_id` (`broker_id`),
  CONSTRAINT `fk_nodos_brokers`
    FOREIGN KEY (`broker_id`)
    REFERENCES `brokers`(`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  UNIQUE KEY `uq_broker_dispositivo` (`broker_id`, `id_dispositivo`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci;



-- -----------------------------------------------------
-- 5. Creación de usuario MySQL y asignación de privilegios
-- -----------------------------------------------------
CREATE USER IF NOT EXISTS 'usertareaflask'@'%' 
  IDENTIFIED BY 'cambiarcambiar';

GRANT SELECT, INSERT, UPDATE, DELETE
  ON `tareaflask`.* 
  TO 'usertareaflask'@'%';

FLUSH PRIVILEGES;
