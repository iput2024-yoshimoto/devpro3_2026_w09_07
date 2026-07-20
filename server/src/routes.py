import datetime
import os
from dotenv import load_dotenv
from flask import Blueprint, render_template, request
from server.src.csv_handler import read_all_rows, save_sensor_row, get_latest_row

load_dotenv()

TEMPLATE_NAME = os.getenv('TEMPLATE_NAME', 'HTML_iteration_g7.html')

main_bp = Blueprint('main', __name__)

@main_bp.route("/", methods=["GET"])
def index():
    data_list = read_all_rows()
    return render_template(TEMPLATE_NAME, input_from_python=data_list)

@main_bp.route("/submit", methods=["POST"])
def submit():
    try:
        print(f"[Debug] request.formの中身: {request.form}")
        
        tp = request.form.get('temperature', '-')
        hm = request.form.get('humidity', '-')
        co2 = request.form.get('co2', '-')
        nm = request.form.get('student_id', '-')
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [ts, tp, hm, co2, nm]
        save_sensor_row(row)
        print(f"[HTTP Submit] Successfully saved to CSV: {row}")

        return "Success", 200
    except Exception as e:
        print(f"[HTTP Submit Error] {e}")
        return "Internal Server Error", 500

@main_bp.route("/latest", methods=["GET"])
def latest():
    latest_row = get_latest_row()
    if latest_row and len(latest_row) >= 5:
        csv_response = ",".join(latest_row[:5])
        return csv_response, 200, {'Content-Type': 'text/plain'}
        
    return "No data available", 404