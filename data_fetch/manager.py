from enum import Enum, auto

class DATA_SRC(Enum):
    BAO_STOCK = auto()
    CCXT = auto()
    Y_FINANCE = auto()
    LOCAL = auto()
    GENERATE = auto()

FETCHER_CLASSES = {
    DATA_SRC.BAO_STOCK: "BaoStockFetcher",
    DATA_SRC.CCXT: "CcxtFetcher",
    DATA_SRC.Y_FINANCE: "YFinanceFetcher",
    DATA_SRC.LOCAL: "LocalFetcher",
    DATA_SRC.GENERATE: "GenerateFetcher",
}

def GetStockAPI(src):
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
