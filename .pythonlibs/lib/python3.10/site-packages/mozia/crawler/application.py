# -*- coding: UTF-8 -*-
import json
from proxy import crawl_product
from flask import request
from flask import Flask
from flask import make_response
from flask_cors import CORS
from modules.tools.translate import translator
from modules.repository import repositories
from modules.scheduler import task_scheduler
from mozia.crawler.downloader import \
    get_today_covers, \
    get_daily_covers, \
    get_cover_dirs, \
    save_product_images, \
    add_ftp_cover_task

app = Flask(__name__)
CORS(app)

SUCCESS = {
    "status": 0,
    "message": "success"
}


@app.route('/proxy/product', methods=["POST", "GET"])
def get_product():
    catalog = {
        "source_type": 1,
        "catalog_id": 7909,
        "language_id": 1,
        "source_id": "12598893",
        "url": "/cn/shopping/women/mm6-maison-margiela-pleated-side-dress-item-12598893.aspx?storeid=9306&from=listing",
        "thumbnail": "https://cdn-images.farfetch-contents.com/12/58/75/59/12587559_12078291_255.jpg",
        "product_name": "leopard trim cropped trousers",
        "catalog_context": "{\"imageUrl\": \"https://cdn-images.farfetch-contents.com/12/58/75/59/12587559_12078291_255.jpg\", \"unit_sale_price\": 5617.1645, \"color\": \"\", \"CurrencyCode\": \"CNY\", \"name\": \"leopard trim cropped trousers\", \"skuCode\": \"12587559\", \"url\": \"/cn/shopping/women/dolce-gabbana-leopard-trim-cropped-trousers-item-12587559.aspx?storeid=9306&from=listing\", \"currencyCode\": \"CNY\", \"storeId\": 9306, \"sku_code\": \"12587559\", \"unit_price\": 5617.1645, \"currency\": \"CNY\", \"designerName\": \"Dolce & Gabbana\", \"image_url\": \"https://cdn-images.farfetch-contents.com/12/58/75/59/12587559_12078291_255.jpg\", \"stock\": 8, \"unitSalePrice\": 5617.1645, \"unitPrice\": 5617.1645, \"id\": \"12587559\", \"hasStock\": true, \"manufacturer\": \"Dolce & Gabbana\"}",
        "catalog_status": 0
    }

    if request.method == 'POST':
        product, _ = crawl_product(request.get_json())
        if not product:
            product = {}
        response = make_response(json.dumps(product))
    else:
        response = make_response(json.dumps(crawl_product(catalog)))

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'

    return response


@app.route('/translate', methods=["POST", "GET"])
def translate():
    if request.method == 'POST':
        string = translator.en_to_zh(request.get_json()["text"])
    else:
        string = translator.en_to_zh(
            "Jet Set Travel saffiano leather tote bag<br>Model in saffiano print calf leather<br />Central zip closure<br />2 flat handles with buckle<br />2 internal compartments and a central partition with zip<br />1 inside pocket with zip<br />3 inside flat pockets<br />1 pocket for mobilephone<br />1 removable logoed charm<br />Gold-tone hardware<br />Fabric lining with allover logo<br />Length: 38 cm<br />Height: 28 cm<br />Depth: 15 cm<br>Posizione del logo: Metallic logo on front<br>100%, Leather<br>Confezione: Acetate<br>Colore: black<br>Product Model: Jet Set Travel")
    response = make_response(string)
    print(string)
    return response


@app.route('/favicon.ico')
def favicon():
    return []


@app.route('/covers')
@app.route('/covers/<date_string>')
def covers(date_string=None):
    if not date_string:
        today_covers = get_today_covers()
    else:
        today_covers = get_daily_covers(date_string)

    data = {
        "covers": today_covers,
        "length": len(today_covers),
        "status": 0,
        "message": "success"
    }
    return make_response(json.dumps(data))


@app.route('/cover/dirs')
def covers_dir():
    dirs = get_cover_dirs()
    data = {
        "covers": dirs,
        "length": len(dirs),
        "status": 0,
        "message": "success"
    }
    return make_response(json.dumps(data))


@app.route('/cover/createFtpTask', methods=["POST", "GET"])
def ftp_cover():
    if request.method == 'POST':
        ftp_cover_task = request.get_json()
    else:
        ftp_cover_task = {
            "product_id": 0,
            "cover_url": "https://images-media.oss-cn-shanghai.aliyuncs.com/s01/0050/00000045/cover.jpg"
        }
    add_ftp_cover_task(ftp_cover_task)
    response = make_response(json.dumps(SUCCESS))
    return response


@app.route('/product/saveImages')
def set_product_images():
    data = request.get_json()
    save_product_images(data["product_id"], data["image_urls"])
    return make_response(json.dumps(data))


app.config['SECRET_KEY'] = 'off'
if __name__ == '__main__':
    repositories.connect()
    task_scheduler.connect()
    app.run(debug=False, port=9604, host="0.0.0.0")
