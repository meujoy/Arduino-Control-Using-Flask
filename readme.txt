To package the application

pip install pyinstaller
pyinstaller --onefile --add-data 'templates:templates' --add-data 'static:static' app.py --clean