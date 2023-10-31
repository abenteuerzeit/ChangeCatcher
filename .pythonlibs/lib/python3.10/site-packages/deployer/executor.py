import commands
import shutil
import os


def copy_file_to_dir(file_path, target_dir):
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)
    shutil.copy(file_path, target_dir)


def deploy_weboff(source):
    print source
    target_dir = "/home/admin/transfer/weboff/"
    copy_file_to_dir(source, target_dir)
    (status, output) = commands.getstatusoutput('/home/web/weboff/deploy.sh')
    return str(output)


def deploy_official(source):
    print source
    target_dir = "/home/admin/transfer/official/"
    copy_file_to_dir(source, target_dir)
    (status, output) = commands.getstatusoutput('/home/web/official-site/deploy.sh')
    return str(output)


def deploy_finger(source):
    print source
    target_dir = "/home/admin/transfer/finger/"
    copy_file_to_dir(source, target_dir)
    (status, output) = commands.getstatusoutput('/home/web/finger/deploy.sh')
    return str(output)


def deploy_webffo(source):
    print source
    copy_file_to_dir(source, "/home/admin/transfer/webffo/")
    (status, output) = commands.getstatusoutput('/home/webffo/scripts/deploy.sh')
    return str(output)


def deploy_webadm(source):
    print source
    copy_file_to_dir(source, "/home/admin/transfer/webadm/")
    (status, output) = commands.getstatusoutput('/home/webadm/scripts/deploy.sh')
    return str(output)


def restart_webadm():
    (status, output) = commands.getstatusoutput('su - webadm -c "/home/webadm/scripts/startup.sh stop"')
    return str(output)


def restart_webffo():
    (status, output) = commands.getstatusoutput('su - webffo -c "/home/webffo/scripts/startup.sh stop"')
    return str(output)


def get_tail_logs(log_path, lines):
    (status, output) = commands.getstatusoutput('tail -n%s %s' % (lines, log_path))
    return str(output)


def restart_weboff():
    return "success"
