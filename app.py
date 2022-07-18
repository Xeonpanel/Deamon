import flask, os, sqlite3, docker, sys, flask_sock, json, flask_cors, logging, time, signal

def sqlquery(sql, *parameter):
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    data = cursor.execute(sql, (parameter)).fetchall()
    conn.commit()
    return data

os.chdir("/etc/deamon")

logging.basicConfig(filename="logs/log.txt", level=logging.DEBUG)
client = docker.from_env()
app = flask.Flask(__name__)
sock = flask_sock.Sock(app)
cors = flask_cors.CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/api/servers/<uuid>/stop", methods=["POST"])
def stop_server(uuid):
    data = sqlquery("SELECT * FROM containers WHERE uuid = ? and user_token = ?", uuid, flask.request.json["user_token"])
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

@app.route("/api/servers/<uuid>/files/upload", methods=["POST"])
def upload_file(uuid):
    if len(sqlquery("SELECT * FROM containers WHERE uuid = ? and user_token = ?", uuid, flask.request.form["user_token"])):
        file = flask.request.files["file"]
        if file.filename == "":
            return "something went wrong"
        if file:
            file.save("{}/{}/{}".format(app.config["UPLOAD_FOLDER"], uuid, file.filename))
            return "file uploaded"
    else:
        flask.abort(401)

@app.route("/api/servers/<uuid>/files", methods=["GET"])
def server_files(uuid):
    if len(sqlquery("SELECT * FROM containers WHERE uuid = ? and user_token = ?", uuid, flask.request.form["user_token"])):
        directory = []
        for file in os.listdir("/etc/deamon/data/{}/".format(uuid)):
            if os.path.isdir("/etc/deamon/data/{}/{}".format(uuid, file)):
                directory.append({"name": file, "type": "dir"})
            else:
                directory.append({"name": file, "type": "file"})
        return flask.jsonify(directory)
    else:
        flask.abort(401)

@app.route("/api/servers/<uuid>/start", methods=["POST"])
def start_server(uuid):
    if len(sqlquery("SELECT * FROM containers WHERE uuid = ? and user_token = ?", uuid, flask.request.json["user_token"])):
        try:
            container = client.containers.get(uuid)
            if container.status == "exited":
                container.stop()
                container.remove(force=True)
                mount = docker.types.Mount(
                    target="/home/container",
                    source="/etc/deamon/data/{}".format(uuid),
                    type="bind"
                )
                container = client.containers.run(
                    image=flask.request.json["image"],
                    command=["sh", "-c", flask.request.json["startup_command"]],
                    mounts=[mount],
                    name=uuid,
                    detach=True,
                    working_dir="/home/container",
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
                source="/etc/deamon/data/{}".format(uuid),
                type="bind"
            )
            container = client.containers.run(
                image=flask.request.json["image"],
                command=["sh", "-c", flask.request.json["startup_command"]],
                mounts=[mount],
                name=uuid,
                detach=True,
                working_dir="/home/container",
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
    if flask.request.form["system_token"] == app.config["SYSTEM_TOKEN"]:
        os.mkdir("/etc/deamon/data/{}".format(uuid))
        sqlquery("INSERT INTO containers (uuid, user_token, port, memory) VALUES (?, ?)", uuid, flask.request.form.get("user_token"), flask.request.form.get("port"). flask.request.form.get("memory"))
        return "server created"
    else:
        flask.abort(401)

@app.route("/")
def main():
    response = flask.jsonify({"succes": "node online"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@sock.route("/logs")
def logs(ws):
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
                    ws.send("\nServer marked as offline..\n")
            except Exception:
                ws.send("Server marked as offline..\n")

@sock.route("/memory")
def stats(ws):
    while True:
        data = json.loads(ws.receive())
        if data.get("uuid"):
            try:
                if client.containers.get(data.get("uuid")).status == "running":
                    container = client.containers.get(data.get("uuid"))
                    for line in container.stats(decode=True, stream=True):
                        ws.send(line["memory_stats"]["usage"])
            except Exception:
                pass

@sock.route("/disk")
def disk(ws):
    while True:
        data = json.loads(ws.receive())
        if data.get("uuid"):
            while True:
                container_size = 0
                for path, dirs, files in os.walk("/etc/deamon/data/{}".format(data.get("uuid"))):
                    for f in files:
                        fp = os.path.join(path, f)
                        container_size += os.path.getsize(fp)
                ws.send(container_size)
                time.sleep(4)

@sock.route("/status")
def status(ws):
    while True:
        data = json.loads(ws.receive())
        if data.get("uuid"):
            while True:
                time.sleep(0.5)
                try:
                    if client.containers.get(data.get("uuid")).status == "exited":
                        ws.send("offline")
                    if client.containers.get(data.get("uuid")).status == "running":
                        ws.send("online")
                except Exception:
                    ws.send("offline")

try:
    if sys.argv[1] == "--token":
        conn = sqlite3.connect("database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.executescript(open("schema.sql").read())
        conn.commit()
        if not os.path.exists("/etc/deamon/data"):
            os.mkdir("/etc/deamon/data")
        print("\n-> Node configured succesfully")
        print("-> Enter: service deamon start, to start deamon\n")
        cursor.execute("INSERT INTO settings (system_token) VALUES (?)", (sys.argv[2],))
        conn.commit()
        os._exit(1)
except:
    if os.path.isfile("database.db"):
        app.config["SYSTEM_TOKEN"] = sqlquery("SELECT * FROM settings")[0][0]
        app.config["SECRET_KEY"] = os.urandom(30).hex()
        app.config["UPLOAD_FOLDER"] = "/etc/deamon/data"
        app.run(debug=False, host="0.0.0.0", port=8080)
    else:
        print("\n-> Node not configured")
        os._exit(1)