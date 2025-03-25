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
import re

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
        user_agent = request.headers.get("User-Agent", "").lower()
        is_browser = any(x in user_agent for x in ["mozilla", "chrome", "edg", "safari"])
        if not is_browser:
            logging.info("User creating command through /submit API directly")
            
            logging.info("Validating Commands")
            if not validate_commands(data):
                logging.error("Commands validation failed")
                return jsonify({'message': 'Commands validation failed. Please check the commands format', 'status': 'failure'}), 400
            logging.info("Validation Successfull")

        logging.info(f"Commands created by the user: {data}")
        json_object = json.dumps(data,indent=4)
        with open('commands.json','w') as file:
            try:
                logging.info("Writing Commands to file")
                file.write(json_object)
            except Exception as e:
                return jsonify({
            'message': 'Failed to receive data, Can not write commands to file',
            'error': True
        }), 500
        
        get_commands() # Writing commands to the global commands_dict variable

        if is_browser:        
            return jsonify({
                    'message': 'Data received successfully',
                    'redirect_url': url_for('views.home')
                }), 200
        else:
            return jsonify({
                    'message': 'Data received successfully','status':'success'
                }), 200

    else:
        return jsonify({
            'message': 'Failed to receive data, Empty data structure',
            'status': 'failure'
        }), 400
    
@views.route('/setup')
def setup():
    if (command_file_exist() == False):
        return render_template("setup.html")
    else:
        return redirect(url_for('views.home'))

@views.route('/reset-commands',methods = ['DELETE'])  
def delete_command_file():
    global commands_dict
    file_path = 'commands.json'

    user_agent = request.headers.get("User-Agent", "").lower() #Checking if the request from a script or the webpage
    if "mozilla" in user_agent or "chrome" in user_agent or 'edg' in user_agent:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)  
                commands_dict = {}
                logging.info("Command File deleted successfully")
                return jsonify({
                'message': 'File deleted successfully.',
                'redirect_url': url_for('views.setup')
                }), 200
            else:
                logging.error(f'{file_path} Not Found')
                return jsonify({'message': 'File does not exist', 'status': 'failure'}), 404
        except Exception as e:
            logging.error("Cannot delete Command File %s"%e)
            return jsonify({'message': 'Error deleting file', 'status': 'failure','Error message': f'{e}'}), 500

    try:
        if os.path.exists(file_path):
            os.remove(file_path)  
            commands_dict = {}
            logging.info("Command File deleted successfully through the API directly")
            return jsonify({'message': 'File deleted successfully.','status': 'success'}), 200
        else:
            return jsonify({'message': 'File does not exist.', 'status': 'failure'}), 404
    except Exception as e:
        logging.error("Cannot delete Command File %s"%e)
        return jsonify({'message': 'Error deleting file', 'status': 'failure','Error message': f'{e}'}), 500
    
@views.route('/connectToPort',methods = ['POST'])
def connect_to_port_api():
    global serial_connection 
    port = get_port()
    if port:
        try:
            serial_connection = serial.Serial(port,9600,timeout=5)
            logging.info("Connected Successfully to %s through API" %serial_connection.port)
            time.sleep(3)
            return jsonify({'message': 'Arduino Connected Successfully', 'status':'success'}), 200
        except Exception as e:
            return jsonify({'message': 'Error Connecting to Arduino.','status':'failure' ,'Error message': f'{e}'}), 500
    else:
        return jsonify({'message': 'No Arduino ports found.', 'status': 'failure'}), 404
    
@views.route('/send',methods = ['POST'])
def send():
    key = request.json.get('command') # Gets which command was sent from the GUI for example: WatchdogOff
    if serial_connection and serial_connection.is_open:
        try:
            logging.info("Sending Commands to Arduino")
            for command in commands_dict[key]: # Loop with the key in the commands_dict which are command1, command2, etc....
                logging.debug("Sending Command: (%s)" %command)
                serial_connection.write(commands_dict[key][command].encode('utf-8')) # Gets the value of each key <command1> : value <close relay00> and sends it to the Arduino
                time.sleep(1)
                response = read() #Response from Arduino
                logging.debug("Arduino respone: (%s)" %response)
            logging.debug("Key %s sent successfully" %key)
            return jsonify({"message": "%s command executed successfully" %key,'status': 'success'}), 200
        except Exception as e:
            return jsonify({
                "message": "No commands sent, Did you setup your commands?",
                'status': 'failure',"Error message": str(e)
                }), 500
    else:
        return jsonify({"message": "Error: No commands sent. Serial connection is not open."}), 404

@views.route('/get-commands',methods = ['GET'])
def get_commands():
    file = 'commands.json'
    if command_file_exist():
        try:
            with open(file,'r') as f:
                data = json.load(f)
            return jsonify({"message":'Data retrieved successfully',"commands": data ,'status': 'success'}),200
        except Exception as e:
            return jsonify({'message': 'Data can not be retrieved.','status': 'failure', 'Error message': f'{e}'}), 500
    return jsonify({'message': 'File not Found.', 'status': 'failure'}), 404

@views.route('/close-serial', methods=['POST'])
def close_connection():
    global serial_connection
    try:
        if serial_connection and serial_connection.is_open:  # Check if connection exists and is open
            serial_connection.close()  # Close the connection
            return jsonify({"message": "Serial connection closed successfully",'status': 'success'}), 200
        else:
            return jsonify({"message": "No open serial connection found",'status': 'failure'}), 400
    except Exception as e:
        return jsonify({"message": "Failed to close serial connection", "Error message": str(e),'status': 'failure'}), 500

def get_port()-> str:
    '''
    get_port() return the arduino serial port name /dev/ttyACM0
    '''
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

def connectToPort(port: str)-> object:
    serial_init = None
    timer = 10
    counter = 0
    while(True):
        try:
            serial_init = serial.Serial(port,9600,timeout=5)
            logging.info("Connected Successfully to %s through GUI" %serial_init.port)
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

def validate_commands(data: dict) -> bool:
    pattern = r"^(close|open) relay(0[0-9]|1[0-2])$"
    if data:
        for value in data.values():
            for command in value.values():
                if not re.match(pattern,command):
                    return False
    return True

def read()-> str:
    while True:
        data = serial_connection.readline().decode().strip()
        if data:
            return data

def get_commands()-> None:
    global commands_dict
    if not commands_dict:
        with open("commands.json","r") as f:
            commands_dict = json.load(f)

def command_file_exist()-> bool:
    file_path = 'commands.json'
    if os.path.exists(file_path):
        return True
    else:
        return False
