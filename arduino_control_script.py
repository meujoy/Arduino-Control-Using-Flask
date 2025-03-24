import requests
import time

url = "http://10.1.1.188:8000/"

#Sending commands with the same key will overwrite each other, make sure they have unqiue keys
commands = {
  "WDGoff": {
    "command1": "close relay00",
    "command2": "open relay00"
  },
  "WDGon": {
      "command1": "close relay00",
      "command2": "open relay00"
    }
}

def connect():
    response = requests.post(url=url+"connectToPort")
    print(response.status_code, response.json())

def execute(command):
    response = requests.post(url=url+"send",json={"command": command})
    print(response.status_code, response.json())

def reset_commands():
    response = requests.delete(url=url+"reset-commands")
    print(response.status_code, response.json())

def create_commands():
    response = requests.post(url=url+'submit',json=commands)
    print(response.status_code, response.json())

def get_commands():
    response = requests.get(url=url+'get-commands')
    print(response.status_code, response.json())

print("resetting Commands")
reset_commands()
print("Creating Commands")
create_commands()
print("Connecting")
connect()
print("Sending Commands")
execute('WDGoff')
time.sleep(2) # Important
execute('WDGon')
print("Getting Commands")
get_commands()


    
        
