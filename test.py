import pathlib

pth = pathlib.Path().iterdir()
for e in pth:
    if not e.is_dir():
        print(e)