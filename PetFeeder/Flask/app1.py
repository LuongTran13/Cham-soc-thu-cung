from flask import Flask, Response, render_template, redirect, request
from helpers import cam_connect, generate_frames, calc_delay, flash, send_feed_command
import asyncio
import websockets
from websockets.exceptions import ConnectionClosed
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialise variables
settings = {
    "timer_running": False,
    "feed_delay": 30,
    "pet_id": 16,
    "auto_feed": False,
    "seconds": 30,
    "minutes": 0,
    "hours": 0,
    "accuracy": 0.65,
    "portion": 'SMALL'
}

# Connect to camera and motor
cam_connect()

# WebSocket setup
WS_PORT = 8888
HTTP_PORT = 8001
connected_clients = []

async def handle_websocket(websocket, path):
    logger.info(f"New WebSocket connection from {websocket.remote_address}, path: {path}")
    connected_clients.append(websocket)
    try:
        async for data in websocket:
            logger.info(f"Received {len(data)} bytes from {websocket.remote_address}")
            active_clients = []
            for client in connected_clients:
                try:
                    if client.state == websockets.protocol.State.OPEN and client != websocket:
                        await client.send(data)
                        logger.info(f"Sent {len(data)} bytes to {client.remote_address}")
                        active_clients.append(client)
                    else:
                        active_clients.append(client)
                except ConnectionClosed:
                    logger.info(f"Client {client.remote_address} disconnected")
                    continue
                except Exception as e:
                    logger.error(f"Error sending to {client.remote_address}: {str(e)}")
                    continue
            connected_clients[:] = active_clients
    except ConnectionClosed:
        logger.info(f"WebSocket {websocket.remote_address} closed")
    except Exception as e:
        logger.error(f"WebSocket error from {websocket.remote_address}: {str(e)}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
            logger.info(f"Removed client {websocket.remote_address}, {len(connected_clients)} clients remain")

async def start_websocket_server():
    await websockets.serve(handle_websocket, "0.0.0.0", WS_PORT)
    logger.info(f"WebSocket server is listening at ws://0.0.0.0:{WS_PORT}")

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(settings["feed_delay"], settings["pet_id"], settings["accuracy"], settings["auto_feed"], settings["portion"]), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/settings", methods=["GET", "POST"])
def handle_settings():
    if request.method == "POST":
        settings["seconds"] = request.form.get("seconds")
        settings["minutes"] = request.form.get("minutes")
        settings["hours"] = request.form.get("hours")
        settings["feed_delay"] = calc_delay(settings["seconds"], settings["minutes"], settings["hours"])

        petSelection = request.form.get("petSelection")
        if petSelection == 'detectCats':
            settings["pet_id"] = 15
        elif petSelection == 'detectBirds':
            settings["pet_id"] = 14
        else:
            settings["pet_id"] = 16

        accuracyInput = request.form.get("accuracy")
        if accuracyInput == 'lowAccuracy':
            settings["accuracy"] = 0.5
        elif accuracyInput == 'highAccuracy':
            settings["accuracy"] = 0.8
        else:
            settings["accuracy"] = 0.65

        portionInput = request.form.get("portion")
        if portionInput == 'largePortion':
            settings["portion"] = 'LARGE'
        elif portionInput == 'medPortion':
            settings["portion"] = 'MED'
        else:
            settings["portion"] = 'SMALL'

        auto_feed = request.form.get("auto_feed")
        if auto_feed == 'on':
            settings["auto_feed"] = True
        else:
            settings["auto_feed"] = False

        return redirect("/")
    else:
        return render_template('settings.html', settings=settings)

@app.route("/stream", methods=["GET", "POST"])
def stream():
    return render_template('stream.html')

@app.route('/feed', methods=['POST'])
def feed():
    if request.method == 'POST' and request.form['feed'] == 'button_click':
        send_feed_command(settings["portion"])
        return redirect("/stream")
    return "Invalid request"

@app.route('/flash_on', methods=['POST'])
def flash_on():
    if request.method == 'POST' and request.form['flash_on'] == 'button_click':
        flash('on')
        return redirect("/stream")  
    return "Invalid request"

@app.route('/flash_off', methods=['POST'])
def flash_off():
    if request.method == 'POST' and request.form['flash_off'] == 'button_click':
        flash('off')
        return redirect("/stream")
    return "Invalid request"

def run_flask_with_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server())
    app.run(host="0.0.0.0", port=HTTP_PORT, debug=False)

if __name__ == '__main__':
    run_flask_with_websocket()