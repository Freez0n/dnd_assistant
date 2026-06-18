import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Tuple

class DatabaseManager:
    _instance = None

    def __new__(cls, host='localhost', user='root', password='', database='dnd'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.host = host
            cls._instance.user = user
            cls._instance.password = password
            cls._instance.database_name = database
            cls._instance._conn = None
            cls._instance._initialized = False
        return cls._instance

    def _get_connection(self):
        if self._conn is None or not self._conn.is_connected():
            try:
                conn_no_db = mysql.connector.connect(host=self.host, user=self.user, password=self.password, charset='utf8mb4')
                cursor = conn_no_db.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
                conn_no_db.commit(); cursor.close(); conn_no_db.close()
                
                self._conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database_name, charset='utf8mb4')
                print(f"✅ Подключено к базе данных: {self.database_name}")
            except Error as e:
                print(f"❌ Ошибка подключения к MySQL: {e}"); raise e
        return self._conn

    def close(self):
        if self._conn and self._conn.is_connected(): self._conn.close(); self._conn = None

    def _initialize_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        print("⚙️ Инициализация структуры БД...")
        
        tables_sql = [
            """CREATE TABLE IF NOT EXISTS `users` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `username` VARCHAR(50) NOT NULL UNIQUE,
                `password_hash` VARCHAR(255) NOT NULL,
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `experiencelevelmap` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Level` INT NOT NULL, `MinExperience` INT NOT NULL, `ProficiencyBonus` TINYINT NOT NULL,
                PRIMARY KEY (`id`),
                CONSTRAINT `fk_ExpMap_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `character` (
                `idCharacter` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Name` VARCHAR(45) NOT NULL, `Race` VARCHAR(45), `Class` VARCHAR(45),
                `Experience` INT NOT NULL DEFAULT 0, `Level` TINYINT NOT NULL DEFAULT 1,
                `ProficiencyBonus` TINYINT NOT NULL DEFAULT 2, `Notes` TEXT,
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_Character_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `attribute` (
                `idCharacter` INT NOT NULL, `Strength` TINYINT DEFAULT 10, `Dexterity` TINYINT DEFAULT 10, 
                `Constitution` TINYINT DEFAULT 10, `Intelligence` TINYINT DEFAULT 10, `Wisdom` TINYINT DEFAULT 10, `Charisma` TINYINT DEFAULT 10, 
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_Attribute_Character` FOREIGN KEY (`idCharacter`) REFERENCES `character` (`idCharacter`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `characterstats` (
                `idCharacter` INT NOT NULL, `MaxHP` SMALLINT DEFAULT 10, `CurrentHP` SMALLINT DEFAULT 10, 
                `ArmorClass` TINYINT DEFAULT 10, `Initiative` TINYINT DEFAULT 0, `Speed` SMALLINT DEFAULT 30, 
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_Stats_Character` FOREIGN KEY (`idCharacter`) REFERENCES `character` (`idCharacter`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `savingthrows` (
                `idCharacter` INT NOT NULL, `Strength` TINYINT DEFAULT 0, `Dexterity` TINYINT DEFAULT 0, 
                `Constitution` TINYINT DEFAULT 0, `Intelligence` TINYINT DEFAULT 0, `Wisdom` TINYINT DEFAULT 0, `Charisma` TINYINT DEFAULT 0, 
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_Save_Character` FOREIGN KEY (`idCharacter`) REFERENCES `character` (`idCharacter`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `savingthrowsproficiency` (
                `idCharacter` INT NOT NULL, `Strength` TINYINT DEFAULT 0, `Dexterity` TINYINT DEFAULT 0, 
                `Constitution` TINYINT DEFAULT 0, `Intelligence` TINYINT DEFAULT 0, `Wisdom` TINYINT DEFAULT 0, `Charisma` TINYINT DEFAULT 0, 
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_SaveProf_Character` FOREIGN KEY (`idCharacter`) REFERENCES `character` (`idCharacter`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `skill` (
                `idCharacter` INT NOT NULL, `Acrobatics` TINYINT DEFAULT 0, `AnimalHandling` TINYINT DEFAULT 0, 
                `Athletics` TINYINT DEFAULT 0, `Deception` TINYINT DEFAULT 0, `History` TINYINT DEFAULT 0, 
                `Insight` TINYINT DEFAULT 0, `Intimidation` TINYINT DEFAULT 0, `Investigation` TINYINT DEFAULT 0, 
                `Medicine` TINYINT DEFAULT 0, `Nature` TINYINT DEFAULT 0, `Perception` TINYINT DEFAULT 0, 
                `Performance` TINYINT DEFAULT 0, `Persuasion` TINYINT DEFAULT 0, `Religion` TINYINT DEFAULT 0, 
                `SleightOfHand` TINYINT DEFAULT 0, `Stealth` TINYINT DEFAULT 0, `Survival` TINYINT DEFAULT 0, 
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_Skill_Character` FOREIGN KEY (`idCharacter`) REFERENCES `character` (`idCharacter`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `skillproficiency` (
                `idCharacter` INT NOT NULL, `Acrobatics` TINYINT DEFAULT 0, `AnimalHandling` TINYINT DEFAULT 0, 
                `Athletics` TINYINT DEFAULT 0, `Deception` TINYINT DEFAULT 0, `History` TINYINT DEFAULT 0, 
                `Insight` TINYINT DEFAULT 0, `Intimidation` TINYINT DEFAULT 0, `Investigation` TINYINT DEFAULT 0, 
                `Medicine` TINYINT DEFAULT 0, `Nature` TINYINT DEFAULT 0, `Perception` TINYINT DEFAULT 0, 
                `Performance` TINYINT DEFAULT 0, `Persuasion` TINYINT DEFAULT 0, `Religion` TINYINT DEFAULT 0, 
                `SleightOfHand` TINYINT DEFAULT 0, `Stealth` TINYINT DEFAULT 0, `Survival` TINYINT DEFAULT 0, 
                PRIMARY KEY (`idCharacter`),
                CONSTRAINT `fk_SkillProf_Character` FOREIGN KEY (`idCharacter`) REFERENCES `character` (`idCharacter`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `monster` (
                `idMonster` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Name` VARCHAR(45) NOT NULL, `AC` INT DEFAULT 10, `HP_Formula` VARCHAR(45), `HP_Avg` INT, `Speed` VARCHAR(45),
                `STR` INT DEFAULT 10, `DEX` INT DEFAULT 10, `CON` INT DEFAULT 10, `INT` INT DEFAULT 10, `WIS` INT DEFAULT 10, `CHA` INT DEFAULT 10,
                `CR` FLOAT DEFAULT 0, `Type` VARCHAR(45), `Source` VARCHAR(45),
                PRIMARY KEY (`idMonster`),
                CONSTRAINT `fk_Monster_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `item` (
                `idItem` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Name` VARCHAR(45) NOT NULL, `Type` VARCHAR(45), `Rarity` VARCHAR(45), `Description` TEXT, `idOwner` INT,  
                PRIMARY KEY (`idItem`),
                CONSTRAINT `fk_Item_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `note` (
                `idNote` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Title` VARCHAR(45) NOT NULL, `Body` TEXT, `Category` VARCHAR(45) DEFAULT 'Прочее', 
                `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `UpdatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
                PRIMARY KEY (`idNote`),
                CONSTRAINT `fk_Note_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `combatsession` (
                `idSession` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `IsActive` TINYINT DEFAULT 1, 
                PRIMARY KEY (`idSession`),
                CONSTRAINT `fk_CombatSession_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `combatparticipant` (
                `idParticipant` INT NOT NULL AUTO_INCREMENT,
                `idSession` INT, `Name` VARCHAR(45) NOT NULL, `Initiative` INT DEFAULT 0, `CurrentHP` INT DEFAULT 10, 
                `MaxHP` INT DEFAULT 10, `Status` VARCHAR(45) DEFAULT 'Нормальный', `IsPlayer` TINYINT DEFAULT 0, 
                PRIMARY KEY (`idParticipant`),
                CONSTRAINT `fk_Participant_Session` FOREIGN KEY (`idSession`) REFERENCES `combatsession`(`idSession`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `dicerollhistory` (
                `idRoll` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Formula` VARCHAR(45) NOT NULL, `Result` INT NOT NULL, `Details` TEXT, `Timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                PRIMARY KEY (`idRoll`),
                CONSTRAINT `fk_DiceHistory_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `saveddiceformula` (
                `idFormula` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `Name` VARCHAR(45) NOT NULL, `Formula` VARCHAR(45) NOT NULL, 
                PRIMARY KEY (`idFormula`),
                CONSTRAINT `fk_SavedDice_User` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            
            """CREATE TABLE IF NOT EXISTS `config` (
                `key` VARCHAR(45) NOT NULL, `value` TEXT, PRIMARY KEY (`key`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
        ]
        
        for sql in tables_sql:
            try: cursor.execute(sql)
            except Exception as e: print(f"❌ Ошибка создания таблицы: {e}"); raise e
            
        print("✅ База данных успешно инициализирована.")
        self._initialized = True

    def __init__(self, host='localhost', user='root', password='', database='dnd'):
        if self._initialized: return
        self._initialize_database()

    def execute(self, query: str, params: Tuple = ()) -> mysql.connector.cursor.MySQLCursorDict:
        conn = self._get_connection(); cursor = conn.cursor(dictionary=True); cursor.execute(query, params); return cursor
    
    def executemany(self, query: str, params_list: List[Tuple]) -> mysql.connector.cursor.MySQLCursorDict:
        conn = self._get_connection(); cursor = conn.cursor(dictionary=True); cursor.executemany(query, params_list); return cursor
    
    def commit(self): self._get_connection().commit()
    
    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict]: 
        return self.execute(query, params).fetchone()
    
    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict]: 
        return self.execute(query, params).fetchall()
    
    def last_insert_id(self) -> int:
        cursor = self.execute("SELECT LAST_INSERT_ID() AS id"); return int(cursor.fetchone()['id'])
    
    def get_config(self, key: str, default: str = "") -> str:
        row = self.fetchone("SELECT value FROM `config` WHERE `key` = %s", (key,)); return row['value'] if row else default
    
    def set_config(self, key: str, value: str):
        self.execute("INSERT INTO `config` (`key`, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s", (key, value, value)); self.commit()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        return self.fetchone("SELECT * FROM `users` WHERE username = %s", (username,))
    
    def create_user(self, username: str, pwd_hash: str) -> int:
        self.execute("INSERT INTO `users` (username, password_hash) VALUES (%s, %s)", (username, pwd_hash))
        self.commit(); return self.last_insert_id()
        
    def update_password(self, user_id: int, new_pwd_hash: str):
        self.execute("UPDATE `users` SET password_hash = %s WHERE id = %s", (new_pwd_hash, user_id)); self.commit()