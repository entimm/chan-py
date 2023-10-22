from enum import Enum, auto

class DataSrc(Enum):
    BAOSTOCK = auto()
    CCXT = auto()
    Y_FINANCE = auto()
    LOCAL = auto()
    GENERATE = auto()

FETCHER_CLASSES = {
    DataSrc.BAOSTOCK: "BaostockFetcher",
    DataSrc.CCXT: "CcxtFetcher",
    DataSrc.Y_FINANCE: "YFinanceFetcher",
    DataSrc.LOCAL: "LocalFetcher",
    DataSrc.GENERATE: "GenerateFetcher",
}

def get_stock_api(src):
    if src in FETCHER_CLASSES:
        fetcher_class_name = FETCHER_CLASSES[src]
        fetcher_module = __import__(f"data_fetch.fetchers.{src.name.lower()}_fetcher", fromlist=[fetcher_class_name])
        return getattr(fetcher_module, fetcher_class_name)

    if src.startswith("custom:"):
        package_info = src.split(":")[1]
        package_name, cls_name = package_info.split(".")
        module = __import__(f"data_api.apis.{package_name}", fromlist=[cls_name])
        return getattr(module, cls_name)

    raise Exception("src type not found")

def fetch_data(src, process):
    stockapi_cls = get_stock_api(src)
    try:
        stockapi_cls.do_init()
        return process(stockapi_cls)
    except Exception:
        raise
    finally:
        stockapi_cls.do_close()