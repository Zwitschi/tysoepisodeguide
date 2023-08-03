import os
from app import app

if __name__ == '__main__':
    activate_this = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate_this.py')
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

    from waitress import serve
    serve(app, listen='*:5000')