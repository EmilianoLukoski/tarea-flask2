CREATE DATABASE IF NOT EXISTS `tareaflask` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `tareaflask`;

CREATE TABLE `usuarios` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `usuario` VARCHAR(100) NOT NULL,
  `hash` VARCHAR(150) NOT NULL,
  `tema` TINYINT(1) NOT NULL DEFAULT 0,  -- 0: claro, 1: oscuro
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario` (`usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

COMMIT;
