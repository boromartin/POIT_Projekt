from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect    
import paho.mqtt.client as mqtt
import MySQLdb    
import json
from os import path
from csv import writer



import time
import random
import math

async_mode = None

app = Flask(__name__)

myhost = "localhost"
myuser = "root"
mypasswd = ""
mydb = "poit"

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 
client = mqtt.Client("Python")
db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb) 
listObj = []


print(myhost)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/env_monitoring_boro")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    socketio.emit('my_response',str(msg.payload)[2:-1],namespace='/test')
    cursor = db.cursor()
    DataJSON = json.loads(msg.payload)
    
    #save to MySQL

    cursor.execute("INSERT INTO Monitoring (Measurement) VALUES (%s)", [msg.payload.decode("utf-8")] )
    db.commit()
    
    f = open("/home/pi/CV7/flask2/DATA.txt", "a")
    f.write(msg.payload.decode("utf-8") + "\n")
    f.close()

def background_thread(args):
    #db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)    
	
    count = 0    
    print("here")

    client.connect("appletoe358.cloud.shiftr.io", 1883)
    client.username_pw_set("appletoe358", "bJDHbabT58HYjSqD")

    client.on_connect = on_connect
    client.on_message = on_message

    client.loop_forever()

    socketio.sleep(2)

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
    
@app.route('/graphSQL', methods=['GET', 'POST']) 
def graph():
    return render_template('graphSQL.html', async_mode=socketio.async_mode)
    
@app.route('/graphFile', methods=['GET', 'POST']) 
def graphFile():
    return render_template('graphFile.html', async_mode=socketio.async_mode)

  
@app.route('/dbdata/<string:num>', methods=['GET', 'POST'])
def dbdata(num):
  rv = []
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  cursor.execute("SELECT * FROM Monitoring")
  rv = cursor.fetchall()
  rvJSON = json.dumps(rv[-int(num):])

  return str(rvJSON) 

@app.route('/filedata/<string:num>', methods=['GET', 'POST'])
def filedata(num):
  rv = []
  f = open("/home/pi/CV7/flask2/DATA.txt", "r")
  rv = f.read()

  return str(rv) 

 

@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    
#    emit('my_response',
#        {'data': message['value'], 'count': session['receive_count']})
 
@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
#    emit('my_response',
#         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
#    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
    
    client.username_pw_set("appletoe358", "bJDHbabT58HYjSqD")


