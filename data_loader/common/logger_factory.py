import logging
from logging.handlers import RotatingFileHandler
import os


class LoggerFactory:
    """
    LoggerFactory sets up rotating file logging and provides
    logger adapters with contextual information.
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 10  # Keep 10 backup log files

    @staticmethod
    def setup_logging(
        log_filename: str = "databricks_adapter.log",
        stream=None,
        clean_before_run: bool = True
    ):
        """
        Set up the root logger with rotating file handler.
        Optionally logs to a provided stream (like sys.stderr).
        """

        # Ensure directory exists
        log_dir = os.path.dirname(log_filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Clean existing log file
        if clean_before_run and os.path.exists(log_filename):
            try:
                with open(log_filename, 'w'):
                    pass
            except Exception as e:
                print(f"Warning: Failed to clear log file {log_filename}: {e}")

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=LoggerFactory.MAX_FILE_SIZE,
            backupCount=LoggerFactory.BACKUP_COUNT
        )

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove old handlers (avoid duplicate logs)
        if root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

        # Add file handler
        root_logger.addHandler(file_handler)

        # Optional console logging
        if stream:
            stream_handler = logging.StreamHandler(stream)
            stream_handler.setFormatter(formatter)
            root_logger.addHandler(stream_handler)

        root_logger.info("Logging initialized successfully.")

    @staticmethod
    def get_logger(class_name: str, context: str = None) -> logging.LoggerAdapter:
        """
        Return a logger adapter with optional contextual info.
        """

        logger = logging.getLogger(class_name)

        extra = {
            'context': context if context else "N/A"
        }

        return logging.LoggerAdapter(logger, extra)