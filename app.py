from flask import Flask, render_template, url_for, request
from flask_bootstrap import Bootstrap


app = Flask(__name__)
Bootstrap(app)


from __future__ import print_function
from ctypes import c_void_p, cast, POINTER
from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings
from time import sleep
from threading import Event
from sys import argv
import redis

redis_host = "localhost"
redis_port = 6379
redis_password = ""
r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

states = []

class State:
    def __init__(self, device):
        self.device = device
        self.callback = cbindings.FnVoid_VoidP_DataP(self.data_handler)
        self.processor = None
        self.samples = 0

    def data_handler(self, ctx, data):
        values = parse_value(data, n_elem = 2)
        ll = str(values[0].x) + "," + str(values[0].y) + "," + str(values[0].z) + "," + str(values[1].x)+","+ str(values[1].y)+","+ str(values[1].z)
        #print(data.contents.epoch)
        r.publish("redisChat", str(ll))
        # r.rpush("iotahead",ll)
        print(" %.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f" % (data.contents.epoch, values[0].x, values[0].y, values[0].z, values[1].x, values[1].y, values[1].z))
        self.samples+=1

    def setup(self):
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        e = Event()

        def processor_created(context, pointer):
            self.processor = pointer
            e.set()
        fn_wrapper = cbindings.FnVoid_VoidP_VoidP(processor_created)
        
        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(self.device.board)

        signals = (c_void_p * 1)()
        signals[0] = gyro
        libmetawear.mbl_mw_dataprocessor_fuser_create(acc, signals, 1, None, fn_wrapper)
        e.wait()

        libmetawear.mbl_mw_datasignal_subscribe(self.processor, None, self.callback)

    def start(self):
    
        libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(self.device.board)
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)

        libmetawear.mbl_mw_gyro_bmi160_start(self.device.board)
        libmetawear.mbl_mw_acc_start(self.device.board)
        
for i in range(len(argv) - 1):
    d = MetaWear(argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

for s in states:
    print("Configuring %s" % (s.device.address))
    s.setup()

for s in states:
    s.start()

while():
    sleep(30.0)

print("Resetting devices")
events = []
for s in states:
    e = Event()
    events.append(e)

    s.device.on_disconnect = lambda s: e.set()
    libmetawear.mbl_mw_debug_reset(s.device.board)

for e in events:
    e.wait()


print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data', methods=['POST'])
def get_data():
    if request.method == 'POST':
        
    return render_template('engine.html',prediction=prediction)

# run the app.
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)