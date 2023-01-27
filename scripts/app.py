from flask import Flask, jsonify, request, abort
app = Flask(__name__)
import scripts

@app.route("/checkin", methods=['POST'])
def index():
    try:
        reqs = request.get_json(force=True)
        res = scripts.checkin(reqs["content"])
        return jsonify(res)
    except Exception as ept:
        return abort(403, f'{ept}')

@app.route("/ip", methods=['GET'])
def getip():
    return jsonify({"ip": scripts.get_host_ip()})

app.run(host='0.0.0.0', port=7777)

