# -*- coding: UTF-8 -*-
import json
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, flash, redirect
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
import executor

app = Flask(__name__)
Bootstrap(app)

nav = Nav()

# registers the "top" menubar
nav.register_element('top', Navbar(
    View('MACROS', 'deploy')
))
nav.init_app(app)


@app.route('/deploy')
def deploy():
    return render_template('deploy.html')


@app.route('/weboff/deploy', methods=['POST'])
def deploy_weboff():
    source = json.loads(request.get_data() or "{}")
    if not source.get("source"):
        return "No source special"
    return executor.deploy_weboff(source["source"])


@app.route('/webffo/deploy', methods=['POST'])
def deploy_webffo():
    source = json.loads(request.get_data() or "{}")
    if not source.get("source"):
        return "No source special"
    return executor.deploy_webffo(source["source"])


@app.route('/webadm/deploy', methods=['POST'])
def deploy_webadm():
    source = json.loads(request.get_data() or "{}")
    if not source.get("source"):
        return "No source special"
    return executor.deploy_webadm(source["source"])


@app.route('/official/deploy', methods=['POST'])
def deploy_official():
    source = json.loads(request.get_data() or "{}")
    if not source.get("source"):
        return "No source special"
    return executor.deploy_official(source["source"])


@app.route('/finger/deploy', methods=['POST'])
def deploy_finger():
    source = json.loads(request.get_data() or "{}")
    if not source.get("source"):
        return "No source special"
    return executor.deploy_finger(source["source"])


@app.route('/webadm/restart', methods=['GET'])
def restart_webadm():
    return executor.restart_webadm()


@app.route('/weboff/restart', methods=['GET'])
def restart_weboff():
    return executor.restart_weboff()


@app.route('/webffo/restart', methods=['GET'])
def restart_webffo():
    return executor.restart_webffo()


@app.route('/webadm/logs', methods=['GET'])
def get_webadm_logs():
    return executor.get_tail_logs("/home/webadm/logs/webadm.log", 50)


@app.route('/weboff/logs', methods=['GET'])
def get_weboff_logs():
    return "No logs"


@app.route('/webffo/logs', methods=['GET'])
def get_webffo_logs():
    return executor.get_tail_logs("/home/webffo/logs/webffo.log", 50)


@app.route('/file/upload', methods=['POST'])
def uploadZip():
    fileZip = request.files['file']
    # 当前文件所在路径
    basepath = os.path.dirname(__file__)
    # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    save_path = os.path.join(basepath, 'static/zip', secure_filename(fileZip.filename))
    fileZip.save(save_path)
    return save_path


app.config['SECRET_KEY'] = 'off'
if __name__ == '__main__':
    nav.init_app(app)
    app.run(debug=False, port=8604, host="0.0.0.0")
