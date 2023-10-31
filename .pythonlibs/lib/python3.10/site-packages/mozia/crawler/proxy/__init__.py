from .farfetch import crawl_farfetch_product
from .intramirror import crawl_intramirror_product
from .resolver import FarfetchResolver
from mozia.crawler.repository import dao


def crawl_product(catalog):
    params = {
        "source_id": catalog["source_id"],
        "source_type": catalog["source_type"]
    }
    product = dao.catalog.get_product_cache(params)
    if product:
        print("use product from cache:", product)
        return product, True

    if 1 == catalog["source_type"]:
        product = crawl_farfetch_product(catalog)
    elif 3 == catalog["source_type"]:
        product = crawl_intramirror_product(catalog)

    if product:
        dao.catalog.save_product_cache(catalog, product)

    return product, False
