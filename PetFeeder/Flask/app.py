from flask import Flask, Response, render_template, redirect, request #, send_file
from helpers import cam_connect, generate_frames, calc_delay, flash, send_feed_command   #, listen_audio
# , green_light
import time
import random
import requests
app = Flask (__name__)

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


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(settings["feed_delay"], settings["pet_id"], settings["accuracy"], settings["auto_feed"], settings["portion"]), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/settings", methods=["GET", "POST"])
def handle_settings():
    if request.method == "POST":
        # Update settings
        settings["seconds"] = request.form.get("seconds")
        settings["minutes"] = request.form.get("minutes")
        settings["hours"] = request.form.get("hours")
        settings["feed_delay"] = calc_delay(settings["seconds"], settings["minutes"], settings["hours"])

        # Handle pet detection selection
        petSelection = request.form.get("petSelection")
        if petSelection == 'detectCats':
           settings["pet_id"] = 15
        elif petSelection == 'detectBirds':
           settings["pet_id"] = 14
        else:
           settings["pet_id"] = 16

        # Handle detection accuracy selection
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

        # Handle autofeed on/off
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
        # green_light('on')  # Bật đèn xanh
        send_feed_command(settings["portion"])
        # green_light('off')  # Tắt đèn xanh sau khi kết thúc cho ăn
        return redirect("/stream")
    return "Invalid request"


@app.route('/flash_on', methods=['POST'])
def flash_on():
    print('Den duoc bat')
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


# @app.route('/audio_feed')
# def audio_feed():
#     def generate_audio():
#         url = "http://192.168.196.128:8081/audio_feed"
#         with requests.get(url, stream=True) as response:
#             for chunk in response.iter_content(chunk_size=128): # Giảm chunk size để giảm độ trễ
#                 if chunk:
#                     yield chunk
#     return Response(generate_audio(), mimetype="audio/wav")



app.run(host= "0.0.0.0", port= 8001, debug= False)