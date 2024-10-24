from waitress import serve
from flask import Flask
from views import views,logging # importing the views variable of the views file to register the blueprint 
import sys
import os
import configparser

app = Flask(__name__) # Creating Flask app

# Registering the blueprint
app.register_blueprint(views,url_prefix = "/") # url_prefix means that routes will be accessed with the following format "/nameOfthepage"


if __name__ == "__main__":
    try:
        # Read configurations from config file
        config = configparser.ConfigParser()
        config.read('config.ini')

        ip_address = config.get('IP_Address','ip')
        port = int(config.get('Port','port'))

        logging.info("===============Starting Arduino Control VM v1.0.0===================")
        logging.debug("listening on ip address : %s and port %d" % (ip_address,port))

        if getattr(sys,'frozen',False):
            # If frozen, update the template and static folder paths of the existing app instance
            os.environ['FLASK_ENV'] = 'production'
            app.template_folder = os.path.join(sys._MEIPASS, 'templates')
            app.static_folder = os.path.join(sys._MEIPASS, 'static')
            serve(app, host=ip_address, port=port)
        else:
            os.environ['FLASK_ENV'] = 'development'
            app.run(host=ip_address, port=port, debug=True)

    except OSError as e:
        logging.error("OS error occurred while starting Flask: %s", e)
    except Exception as e:
        logging.error("Error occured (%s)" %e)
