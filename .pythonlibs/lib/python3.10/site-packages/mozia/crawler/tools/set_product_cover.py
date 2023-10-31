import os
from mozia.crawler.repository import dao
from modules.repository import repositories


def find_files(dir):
    return ["%s/%s" % (dir, local_file) for local_file in os.listdir(dir)]
    # print("put ftp file:", local_file)
    # save_file_to_ftp(remote_path, local_path)


def find_covers():
    covers = []
    cover_dir = "F:/home/scan"
    for subdir in os.listdir(cover_dir):
        covers += find_files("%s/%s" % (cover_dir, subdir))

    return covers


def create_formatted_covers():
    for cover in find_covers():
        print(cover)


if __name__ == "__main__":
    # find_covers()
    repositories.connect(host='10.26.235.6', port=3306)
    create_formatted_covers()
