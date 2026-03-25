"""统一日志配置."""

import logging
import os
import sys
from pathlib import Path

import structlog

# 日志目录
LOG_DIR = Path(os.getenv("FORGECLAW_LOG_DIR", "./logs"))
LOG_DIR.mkdir(exist_ok=True)


def configure_logging():
    """配置统一结构化日志."""
    log_level = os.getenv("FORGECLAW_LOG_LEVEL", "INFO").upper()
    is_tty = sys.stdout.isatty()

    # 共享处理器链
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # 控制台渲染器
    if is_tty:
        console_renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        console_renderer = structlog.processors.JSONRenderer()

    # 文件渲染器 - 始终 JSON
    file_renderer = structlog.processors.JSONRenderer()

    # 使用 ProcessorFormatter 桥接 structlog 和标准库日志
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=console_renderer,
        foreign_pre_chain=shared_processors,
    )

    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=file_renderer,
        foreign_pre_chain=shared_processors,
    )

    # 文件处理器
    file_handler = logging.FileHandler(
        LOG_DIR / "forgeclaw.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # 错误文件处理器
    error_handler = logging.FileHandler(
        LOG_DIR / "forgeclaw.error.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)

    # 根日志配置
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, error_handler, console_handler],
        force=True,
    )

    # 配置特定模块的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # 配置 Uvicorn 日志处理器，使其也使用 structlog 格式
    # 覆盖 Uvicorn 默认的日志配置
    for uvicorn_logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers = []  # 清除默认处理器
        uvicorn_logger.propagate = False  # 防止重复日志
        uvicorn_logger.addHandler(console_handler)
        uvicorn_logger.addHandler(file_handler)
        uvicorn_logger.addHandler(error_handler)

    # 配置 structlog
    structlog.configure(
        processors=shared_processors + [
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
        ],
        third_party_levels={
            "uvicorn.access": "WARNING",
            "httpx": "WARNING",
        }
    )


def get_task_logger(task_id: str):
    """获取带任务ID的日志记录器."""
    return structlog.get_logger().bind(task_id=task_id)
