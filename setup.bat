@echo off
python -m venv venv
call venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

echo Virtual environment setup complete. Run 'venv\Scripts\activate' to activate.
