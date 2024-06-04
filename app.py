from flask import Flask, json, abort, Response, request
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import threading

app = Flask(__name__)
app.config["timestamp"] = ''
scheduleThreads = {}
nodeHostname = 'wil-gma1-node'

@app.post('/on')
def on():
    print("INFO: Client requested ON state...")
    try:
        r = requests.post('http://' + nodeHostname + '/on')
    except Exception as e:
        print("ERROR: %s..." % e)
        abort(400)
    return Response(
        r.text,
        status=r.status_code,
    )

@app.post('/off')
def off():
    print("INFO: Client requested OFF state...")
    try:
        r = requests.post('http://' + nodeHostname + '/off')
    except Exception as e:
        print("ERROR: %s..." % e)
        abort(400)
    return Response(
        r.text,
        status=r.status_code,
    )

@app.get('/state')
def state():
    try:
        r = requests.get('http://' + nodeHostname + '/state')
    except Exception as e:
        print("ERROR: %s..." % e)
        abort(400)
    return Response(
        r.text,
        status=r.status_code,
    )

@app.post('/cancel')
def cancel():
    message = ""
    if request.args is None or len(request.args) <= 0:
        abort(400)
    else:
        try:
            print("INFO: Requested cancellation of schedule %s " % request.args["timestamp"])
            app.config["timestamp"] = datetime.fromisoformat(request.args["timestamp"]).isoformat()
            try:
                timer = scheduleThreads.pop(app.config["timestamp"])
                timer.cancel()
                message = "Schedule found and cancelled."
            except KeyError as ke:
                message = "Schedule was NOT found!"
            print("INFO: %s" % message)
        except Exception as e:
            print("ERROR: %s..." % e)
            abort(400)
    return Response(
        message,
        status=200,
    )

@app.post('/schedule')
def schedule():
    if request.args is None or len(request.args) <= 0:
        abort(400)
    else:
        try:
            print("INFO: Requested schedule is %s " % request.args["timestamp"])
            future = datetime.fromisoformat(request.args["timestamp"])
            now = datetime.now(ZoneInfo(key='US/Eastern'))
            difference = future - now
            if difference.total_seconds() <= 0:
                raise Exception("Difference is %i seconds which means schedule requested is in the past!" % difference.total_seconds())
            print("INFO: Seconds in the future = %i..." % difference.total_seconds())
            app.config["timestamp"] = datetime.fromisoformat(request.args["timestamp"]).isoformat()
            timer = threading.Timer(difference.total_seconds(), on)
            timer.setName(app.config["timestamp"])
            scheduleThreads[app.config["timestamp"]] = timer
            timer.start()
        except Exception as e:
            print("ERROR: %s..." % e)
            abort(400)
    return Response(
        "Behaviors scheduled for %s." % app.config["timestamp"],
        status=200,
    )

@app.post('/reboot')
def reboot():
    if request.args is None or len(request.args) <= 0:
        abort(400)
    else:
        target = None
        try:
            target = request.args["target"]
            print("INFO: Client requested reboot of target '%s'..." % target)
            if target == "server":
                print("INFO: I would reboot the server...")
                return "Rebooting target '%s'." % target
            elif target == "nodes":
                try:
                    r = requests.post('http://' + nodeHostname + '/reboot')
                except Exception as e:
                    print("ERROR: %s..." % e)
                    abort(400)
                return Response(
                    r.text,
                    status=r.status_code,
                )
            else:
                raise Exception("Client requested invalid target")
        except Exception as e:
            print("ERROR: %s..." % e)
            abort(400)
    