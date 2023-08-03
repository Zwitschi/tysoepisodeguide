from app import app

if __name__ == '__main__':
    from waitress import serve
    serve(app, listen='*:5000')