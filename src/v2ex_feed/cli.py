# cli.py
import asyncio, typer
from main import main as run_bot

app = typer.Typer()


@app.command()
def start():
    asyncio.run(run_bot())


if __name__ == "__main__":
    app()
