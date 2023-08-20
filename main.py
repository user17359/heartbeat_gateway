import typer

app = typer.Typer()


@app.command()
def startup():
    print(f'Hi')


@app.command()
def display_info():
    print(f'Hi')


if __name__ == '__main__':
    app()
