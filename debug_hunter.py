from flask import Flask, request, render_template_string, send_file, redirect, session
import os, zipfile, re, subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "debug_hunter_secret"

UPLOAD_FOLDER = 'uploads'
MODIFIED_FOLDER = 'modified'
ZIP_FOLDER = 'zips'
BLOCKED_TERMS = ["rm", "reboot", "shutdown", "poweroff", "mkfs", "dd", ">", "|", "&"]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODIFIED_FOLDER, exist_ok=True)
os.makedirs(ZIP_FOLDER, exist_ok=True)

USERNAME = "kader11000"
PASSWORD = "hunter"

TOOLS = {
    "Nmap": "nmap -sV 127.0.0.1",
    "Nikto": "nikto -host http://127.0.0.1",
    "WHOIS": "whois example.com",
    "cURL": "curl http://example.com",
    "Traceroute": "traceroute 8.8.8.8",
    "Ping": "ping -c 4 8.8.8.8",
    "DNSRecon": "dnsrecon -d example.com",
    "WhatWeb": "whatweb http://example.com",
    "theHarvester": "theHarvester -d example.com -l 100 -b google",
    "Dirb": "dirb http://example.com",
    "WPScan": "wpscan --url http://example.com",
    "Hydra": "hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.1 ssh"
}

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>DEBUG Hunter</title>
    <style>
        body { background-color: #111; color: #0f0; font-family: monospace; padding: 20px; }
        input, select, textarea { width: 100%; margin: 5px 0; background-color: #222; color: #0f0; border: 1px solid #0f0; }
        .section { border: 1px solid #0f0; padding: 10px; margin-top: 20px; }
        .btn { background-color: #0f0; color: #000; padding: 10px; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h2>DEBUG Hunter by kader11000</h2>

    <form method="POST" enctype="multipart/form-data">
        <div class="section">
            <h3>Upload C or Objective-C Files</h3>
            <input type="file" name="files" multiple>
            <h4>Replace line with:</h4>
            <input type="text" name="replacement" placeholder="#define DEBUG 0">
            <button class="btn" type="submit">Scan & Replace</button>
        </div>

        <div class="section">
            <h3>External Tools</h3>
            <input type="text" name="custom_command" placeholder="Enter custom command">
            <button class="btn" name="run_cmd">Run</button>

            <h4>Predefined Tools:</h4>
            <select name="tool_command">
                {% for name, cmd in tools.items() %}
                    <option value="{{ cmd }}">{{ name }}</option>
                {% endfor %}
            </select>
            <button class="btn" name="run_tool">Run Tool</button>
        </div>
    </form>

    {% if results %}
    <div class="section">
        <h3>Scan Results:</h3>
        {% for filename, matches in results.items() %}
            <b>{{ filename }}</b><br>
            {% if matches %}
                <ul>
                {% for line in matches %}
                    <li>{{ line }}</li>
                {% endfor %}
                </ul>
            {% else %}
                No matches found.
            {% endif %}
        {% endfor %}
        <a href="/download-modified" class="btn">Download Modified Files</a>
    </div>
    {% endif %}

    {% if logs %}
    <div class="section">
        <h3>Logs:</h3>
        <pre>{% for log in logs %}> {{ log }}
{% endfor %}</pre>
    </div>
    {% endif %}

    {% if cmd_output %}
    <div class="section">
        <h3>Command Output:</h3>
        <pre>{{ cmd_output }}</pre>
    </div>
    {% endif %}
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect("/login")

    results, logs, cmd_output = {}, [], ""
    if request.method == "POST":
        if "run_cmd" in request.form or "run_tool" in request.form:
            command = request.form.get("custom_command") if "run_cmd" in request.form else request.form.get("tool_command")
            if any(term in command for term in BLOCKED_TERMS):
                cmd_output = "[ERROR] Command blocked for security reasons."
            else:
                try:
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=30, universal_newlines=True)
                    cmd_output = output
                except subprocess.CalledProcessError as e:
                    cmd_output = e.output
                except Exception as e:
                    cmd_output = str(e)
        else:
            uploaded_files = request.files.getlist("files")
            replacement_line = request.form.get("replacement")
            pattern = re.compile(r"#.*DEBUG$")
            for f in os.listdir(MODIFIED_FOLDER):
                os.remove(os.path.join(MODIFIED_FOLDER, f))
            for file in uploaded_files:
                filename = secure_filename(file.filename)
                if filename.endswith(('.c', '.m')):
                    path = os.path.join(UPLOAD_FOLDER, filename)
                    mod_path = os.path.join(MODIFIED_FOLDER, filename)
                    file.save(path)
                    logs.append(f"Uploaded file: {filename}")
                    matches, modified_lines = [], []
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if pattern.search(line):
                                matches.append(line.strip())
                                logs.append(f"Matched: {line.strip()}")
                                logs.append(f"Replaced with: {replacement_line}")
                                modified_lines.append(replacement_line + "\n")
                            else:
                                modified_lines.append(line)
                    with open(mod_path, "w", encoding="utf-8") as mf:
                        mf.writelines(modified_lines)
                    results[filename] = matches
            with zipfile.ZipFile(os.path.join(ZIP_FOLDER, "modified.zip"), "w") as zipf:
                for f in os.listdir(MODIFIED_FOLDER):
                    zipf.write(os.path.join(MODIFIED_FOLDER, f), f)

    return render_template_string(TEMPLATE, results=results, logs=logs, tools=TOOLS, cmd_output=cmd_output)

@app.route("/download-modified")
def download():
    return send_file(os.path.join(ZIP_FOLDER, "modified.zip"), as_attachment=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == USERNAME and request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        else:
            return "<h3>Invalid login credentials</h3>"
    return '''
    <form method="POST">
        <h3>Login to DEBUG Hunter</h3>
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
    '''

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
