import mh_z19
import subprocess
import ast
#
def get_co2_data():
    try:
        mhz19b_out_bytes = subprocess.check_output(['sudo', '/home/pi/devpro3/venv313/bin/python', '-m', 'mh_z19'])
        result = ast.literal_eval(mhz19b_out_bytes.decode())

        print("mh_z19.read()の結果：", result)

        if result is not None:
            co2 = result["co2"]
            print(f"CO2: {co2} ppm")
            return int(co2)
        else:
            print("デバック：データとれず")

    except Exception as e:
        print("MH-Z19C Error:", e)

    return -1

if __name__ =="__main__":
    get_co2_data()