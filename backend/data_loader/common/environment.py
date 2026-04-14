
import os
import logging
from dotenv import load_dotenv
import os
from dotenv import load_dotenv



class EnvironmentConfig:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 🔥 build absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_path = os.path.join(base_dir, "data_loader", "common", ".env")

        load_dotenv(env_path)

        # load variables
        self.DB_SERVER = os.getenv("DB_SERVER")
        self.DB_DATABASE = os.getenv("DB_DATABASE")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")

        # validate
        missing = []
        if not self.DB_SERVER:
            missing.append("DB_SERVER")
        if not self.DB_DATABASE:
            missing.append("Db_DATABASE")
        if not self.DB_USER:
            missing.append("DB_USER")
        if not self.DB_PASSWORD:
            missing.append("DB_PASSWORD")

        if missing:
            raise EnvironmentError(f"Missing env variables: {', '.join(missing)}")

        self.logger.info("Environment variables loaded successfully")
if __name__ == "__main__":
    config = EnvironmentConfig()
    