# build a Mac application bundle for Feldman using pyinstaller
python -m PyInstaller --clean --onefile --name "Correlator" --windowed --icon icons/correlator.icns correlator.py