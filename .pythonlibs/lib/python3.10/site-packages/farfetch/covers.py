import network
import os
from repository import dao


def download_from_oss(url, product_id):
    if not url:
        return

    file_path = "data/cover/" + os.path.basename(url)

    if not os.path.isfile(path=file_path):
        print "download image:", url
        network.download_image(url, file_path)
    else:
        print "file exists:", url


def check_product_oss_cover(product_id):
    if not product_id:
        return


def start_download_covers():
    for item in dao.catalog.get_men_product_covers():
        url = item["oss_url"]
        download_from_oss(url, item["product_id"])


if __name__ == "__main__":
    start_download_covers()
