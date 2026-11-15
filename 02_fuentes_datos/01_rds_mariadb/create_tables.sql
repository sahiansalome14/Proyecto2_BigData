CREATE TABLE stars (
    star_id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE planetary_systems (
    system_id INT AUTO_INCREMENT PRIMARY KEY,
    star_id INT NOT NULL UNIQUE,
    sy_dist DECIMAL(12,4),
    sy_pnum INT,
    FOREIGN KEY (star_id)
        REFERENCES stars(star_id)
) ENGINE=InnoDB;