"""命令行入口."""

import asyncio

import click
import uvicorn

from forgeclaw.api.main import create_app


@click.group()
def main():
    """ForgeClaw CLI."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8000, help="监听端口")
@click.option("--reload", is_flag=True, help="开发模式自动重载")
def server(host: str, port: int, reload: bool):
    """启动 API 服务器."""
    app = create_app()
    uvicorn.run(
        "forgeclaw.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@main.command()
def version():
    """显示版本."""
    from forgeclaw import __version__
    click.echo(f"ForgeClaw v{__version__}")


if __name__ == "__main__":
    main()
