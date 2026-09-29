import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Data Files
BCS_ALL_STOCKS_FILE = os.path.join(DATA_DIR, "bcs_all_market_stocks.json")
BCS_DIVIDENDS_FILE = os.path.join(DATA_DIR, "bcs_dividends_cache.json")
BCS_RATIOS_FILE = os.path.join(DATA_DIR, "bcs_ratios_cache.json")
BCS_SCREENER_CACHE_FILE = os.path.join(DATA_DIR, "bcs_screener_cache.json")

import shutil

# Bolsa de Santiago URLs & Executables
BCS_BASE_URL = "https://www.bolsadesantiago.com"
BCS_MERCADO_URL = "https://www.bolsadesantiago.com/mercado/acciones"

def _find_browser_executable() -> str:
    """Find Microsoft Edge or Google Chrome executable dynamically across any Windows PC."""
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in possible_paths:
        if p and os.path.isfile(p):
            return p

    for name in ["msedge", "chrome", "google-chrome"]:
        w = shutil.which(name)
        if w:
            return w

    return r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

EDGE_EXECUTABLE = _find_browser_executable()

# Pre-loaded Baseline (User's Portfolio Stocks)
INITIAL_PORTFOLIO_SYMBOLS = [
    "AAISA",
    "ANDINA-A",
    "CENCOMALLS",
    "CHILE",
    "ENELGXCH",
    "HABITAT",
    "LIPIGAS",
    "PEHUENCHE",
    "QUINENCO",
    "SOQUICOM"
]

# Popular IPSA & Chilean Blue Chips for Quick Analysis
POPULAR_CHILEAN_STOCKS = [
    "SQM-B",
    "BCI",
    "BSANTANDER",
    "CCU",
    "CMPC",
    "COLBUN",
    "COPEC",
    "ECL",
    "EMBONOR-B",
    "ENELAM",
    "ENTEL",
    "FALABELLA",
    "ILC",
    "MALLPLAZA",
    "PARAUCO",
    "RIPLEY",
    "SALFACORP",
    "SECURITY",
    "SMU",
    "SONDA",
    "VAPORES"
]
