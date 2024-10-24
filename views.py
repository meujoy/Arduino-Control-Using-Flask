'''
We do this in order to sperate the routes from the starting file of the app
'''
from flask import Blueprint, render_template, request, jsonify, redirect,url_for
import serial
import glob
import pyudev
import time
import json
import logging
import os

logging.basicConfig(level=logging.DEBUG,
    filename= "logs.log",
    filemode= "a",
    format= "{asctime} - {levelname} - {funcName} - {lineno} - {message}",
    style="{",
)

# variable = Blueprint(name of the file)
views = Blueprint(__name__,"views") # intializing Blueprint

serial_connection = None
commands_dict = {}

@views.route("/")
def home():
    if (command_file_exist()):
        global serial_connection
        get_commands()
        serial_connection = None
        if serial_connection is None or not serial_connection.is_open:
            port = get_port()
            if port:
                serial_connection = connectToPort(port)
                return render_template("home.html",message= "Connected successfully",commands = commands_dict)
            else:
                logging.info("No Valid Ports")
                return render_template("home.html",message= "No Valid ports")
    else:
        return redirect(url_for('views.setup'))

@views.route('/submit', methods=['POST'])
def fetch_data():
    data = request.get_json()
    if data:
        print(f"Received data:{data}")
        print(type(data))
        json_object = json.dumps(data,indent=4)
        with open('commands.json','w') as file:
            file.write(json_object)
            
        return jsonify({
            'message': 'Data received successfully',
            'redirect_url': url_for('views.home')
        }), 200
    else:
        return jsonify({
            'message': 'Failed to receive data',
            'error': True
        }), 400

    
@views.route('/setup')
def setup():
    if (command_file_exist() == False):
        return render_template("setup.html")
    else:
        return redirect(url_for('views.home'))
def get_port():

    ports = glob.glob('/dev/ttyAC[A-Za-z]*')
    if not ports:
        logging.info("No Serial ports found")
        return None
    for port in ports:
        context = pyudev.Context()
        device = pyudev.Device.from_device_file(context,port)
        if device.get('ID_VENDOR_ID') == "2341" or "arduino" in device.get('ID_VENDOR'):
            logging.info("Port %s found" % port)
            return port
        else:
            logging.info("No Arduino ports found")
            return None
'''
get_port() return the arduino serial port name /dev/ttyACM0
'''
def connectToPort(port):
    serial_init = None
    timer = 10
    counter = 0
    while(True):
        try:
            serial_init = serial.Serial(port,9600,timeout=5)
            logging.info("Connected Successfully to %s" %serial_init.port)
            time.sleep(1)
            return serial_init
        except Exception as e:
            if counter < 10:
                logging.error("Connection to port (%s) failed with exception: %s Retrying in %d seconds" %(port,e,timer))
                time.sleep(timer)
                timer += 10
                counter += 1
            else:
                logging.error("Cannot Connect to serial port after %d tries" %counter)
                return None

@views.route('/send',methods = ['POST'])
def send():
    key = request.json.get('command')
    if serial_connection and serial_connection.is_open:
        try:
            for command in commands_dict[key]:
                serial_connection.write(commands_dict[key][command].encode('utf-8'))
                #time.sleep(1)
                response = read()
                logging.debug("Arduino respone: (%s)" %response)
            logging.debug("Key %s sent successfully" %key)
            return jsonify({"message": "%s command executed successfully" %key}), 200
        except Exception as e:
            return jsonify({"message": "Error: No commands sent. Error message %s." %e}), 401
    else:
        return jsonify({"message": "Error: No commands sent. Serial connection is not open."}), 401

def read():
    while True:
        data = serial_connection.readline().decode().strip()
        if data:
            return data

def get_commands():
    global commands_dict
    if not commands_dict:
        with open("commands.json","r") as f:
            commands_dict = json.load(f)

def command_file_exist():
    file_path = 'commands.json'
    if os.path.exists(file_path):
        return True
    else:
        return False
    
@views.route('/reset-commands',methods = ['DELETE'])  
def delete_command_file():
    global commands_dict
    file_path = 'commands.json'  # Change this to your file path

    try:
        if os.path.exists(file_path):
            os.remove(file_path)  # Delete the file
            commands_dict = {}
            return jsonify({
            'message': 'File deleted successfully.',
            'redirect_url': url_for('views.setup')
            }), 200
        else:
            return jsonify({'message': 'File not found.', 'status': 'error'}), 404
    except Exception as e:
        return jsonify({'message': f'Error deleting file: {str(e)}', 'status': 'error'}), 500
