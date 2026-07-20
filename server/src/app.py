import os
import threading
from dotenv import load_dotenv
from flask import Flask
from routes import main_bp
from socket_server import socket_server_loop

load_dotenv()

FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

def create_app():
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    return app

if __name__ == "__main__":
    socket_thread = threading.Thread(target=socket_server_loop, daemon=True)
    socket_thread.start()
    
    app = create_app()
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )