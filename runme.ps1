﻿E:
cd E:/workspace/python/"Market Management"
.\venv\Scripts\activate.ps1

$env:FLASK_APP=./runme.py
$env:FLASK_ENV="development"
$env:FLASK_DEBUG=1

python -m flask run --host=0.0.0.0