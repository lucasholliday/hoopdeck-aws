CREATE DATABASE IF NOT EXISTS hoopdeck;

USE hoopdeck;

DROP TABLE IF EXISTS teams;

DROP USER IF EXISTS 'hoopdeck-read-only';
DROP USER IF EXISTS 'hoopdeck-read-write';


CREATE USER 'hoopdeck-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'hoopdeck-read-write' IDENTIFIED BY 'def456!!';


GRANT SELECT, SHOW VIEW ON hoopdeck.* 
      TO 'hoopdeck-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON hoopdeck.* 
      TO 'hoopdeck-read-write';
      
FLUSH PRIVILEGES;