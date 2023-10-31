import os
from ftp_client import get_ftp_client


def save_file_to_ftp(remote_path, local_path):
    ftp_client = get_ftp_client()

    buffer_size = 1024
    fp = open(local_path, 'rb')
    ftp_client.storbinary('STOR ' + remote_path, fp, buffer_size)
    ftp_client.set_debuglevel(0)
    fp.close()


if __name__ == "__main__":
    cover_dir = "G:/spider/ready/cover"
    for local_file in os.listdir(cover_dir):
        remote_path = "cover" + "/" + os.path.basename(local_file)
        local_path = cover_dir + "/" + local_file
        print "put ftp file:", remote_path, local_path
        save_file_to_ftp(remote_path, local_path)
