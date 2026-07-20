from dotenv import load_dotenv
load_dotenv()
#
import os

SERVER = os.getenv("SERVER")
WAITING_PORT = os.getenv("WAITING_PORT")
NAME = os.getenv("NAME")