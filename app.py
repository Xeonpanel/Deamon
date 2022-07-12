import flask, os, sqlite3, docker, sys, flask_sock, json, flask_cors, waitress

def sqlquery(sql, *parameter):
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    data = cursor.execute(sql, (parameter))
    conn.commit()
    return data

os.chdir("/var/www/deamon")

client = docker.from_env()
app = flask.Flask(__name__)
sock = flask_sock.Sock(app)
cors = flask_cors.CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/api/servers/<uuid>/stop", methods=["POST"])
def stop_server(uuid):
    data = sqlquery("SELECT * FROM containers WHERE uuid = ? and owner_api = ?", uuid, flask.request.json["api_key"]).fetchall()
    if len(data):
        try:
            container = client.containers.get(uuid)
            container.stop()
            container.remove(force=True)
            response = flask.jsonify({"succes": "server stopped"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
        except:
            response = flask.jsonify({"error": "server already running"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
    else:
        flask.abort(401)

@app.route("/api/servers/<uuid>/start", methods=["POST"])
def start_server(uuid):
    data = sqlquery("SELECT * FROM containers WHERE uuid = ? and owner_api = ?", uuid, flask.request.json["api_key"]).fetchall()
    if len(data):
        try:
            container = client.containers.get(uuid)
            if container.status == "exited":
                container.stop()
                container.remove(force=True)
                mount = docker.types.Mount(
                    target="/home/container",
                    source="/var/www/deamon/data/{}".format(uuid),
                    type="bind"
                )
                container = client.containers.run(
                    image=flask.request.json["image"],
                    command=flask.request.json["startup_command"],
                    mounts=[mount],
                    name=uuid,
                    detach=True,
                    stdout=True,
                    stderr=True
                )
                response = flask.jsonify({"succes": "server started"})
                response.headers["Access-Control-Allow-Origin"] = "*"
                return response
            else:
                response = flask.jsonify({"error": "server already running"})
                response.headers["Access-Control-Allow-Origin"] = "*"
                return response
        except:
            mount = docker.types.Mount(
                target="/home/container",
                source="/var/www/deamon/data/{}".format(uuid),
                type="bind"
            )
            container = client.containers.run(
                image=flask.request.json["image"],
                command=flask.request.json["startup_command"],
                mounts=[mount],
                name=uuid,
                detach=True,
                stdout=True,
                stderr=True
            )
            response = flask.jsonify({"succes": "server started"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
    else:
        flask.abort(401)

@app.route("/api/servers/<uuid>/create", methods=["POST"])
def create_server(uuid):
    if flask.request.form["api_key"] == app.config["API_KEY"]:
        os.mkdir("/var/www/deamon/data/{}".format(uuid))
        sqlquery("INSERT INTO containers (uuid, owner_api) VALUES (?, ?)", uuid, flask.request.form["owner_api"])
        return "server created"
    else:
        flask.abort(401)

@app.route("/")
def main():
    response = flask.jsonify({"succes": "node online"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@sock.route('/ws')
def echo(ws):
    while True:
        data = json.loads(ws.receive())
        if data.get("uuid"):
            try:
                if client.containers.get(data.get("uuid")).status == "exited":
                    container = client.containers.get(data.get("uuid"))
                    ws.send("Server marked as offline..\n")
                if client.containers.get(data.get("uuid")).status == "running":
                    container = client.containers.get(data.get("uuid"))
                    for line in container.attach(stdout=True, stream=True, logs=True):
                        ws.send(line.decode())
            except Exception:
                ws.send("Server marked as offline..\n")

try:
    if sys.argv[1] == "--token":
        if not os.path.isfile("database.db"):
            import models
            sqlquery("INSERT INTO settings (api_key) VALUES (?)", sys.argv[2])
except:
    pass

app.config["API_KEY"] = sqlquery("SELECT * FROM settings").fetchall()[0][0]
app.config["SECRET_KEY"] = os.urandom(30).hex()
if os.path.isfile("database.db"):
    waitress.serve(app, host="0.0.0.0", port=8080)
else:
    print("\n-> Node not configured")
    print("-> Go to you panel and click manage node to view deploy token\n")
    exit()