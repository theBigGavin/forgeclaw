"""日志配置."""

import os
import sys
from pathlib import Path

import structlog

# 日志目录
LOG_DIR = Path(os.getenv("FORGECLAW_LOG_DIR", "./logs"))
LOG_DIR.mkdir(exist_ok=True)


def configure_logging():
    """配置结构化日志."""
    # 获取日志级别
    log_level = os.getenv("FORGECLAW_LOG_LEVEL", "INFO").upper()
    
    # 配置标准库日志
    import logging
    
    # 文件处理器 - 记录所有日志
    file_handler = logging.FileHandler(
        LOG_DIR / "forgeclaw.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 错误文件处理器 - 只记录错误
    error_handler = logging.FileHandler(
        LOG_DIR / "forgeclaw.error.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 根日志配置
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, error_handler, console_handler],
        force=True,
    )
    
    # 配置 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 记录启动信息
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        log_dir=str(LOG_DIR),
        log_level=log_level,
        log_files=[
            str(LOG_DIR / "forgeclaw.log"),
            str(LOG_DIR / "forgeclaw.error.log"),
        ]
    )


def get_task_logger(task_id: str):
    """获取带任务ID的日志记录器."""
    return structlog.get_logger().bind(task_id=task_id)
