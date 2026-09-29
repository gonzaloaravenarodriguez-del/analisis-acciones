import os
import json
import asyncio
import subprocess
import time
import urllib.request
import websockets
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import (
    BCS_ALL_STOCKS_FILE,
    BCS_DIVIDENDS_FILE,
    BCS_RATIOS_FILE,
    BCS_MERCADO_URL,
    EDGE_EXECUTABLE,
    INITIAL_PORTFOLIO_SYMBOLS
)

def load_all_market_stocks() -> List[Dict[str, Any]]:
    """Load cached list of all market stocks and live quotes from Bolsa de Santiago."""
    if os.path.exists(BCS_ALL_STOCKS_FILE):
        try:
            with open(BCS_ALL_STOCKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[BCSClient] Error loading market stocks: {e}")
    return []

def load_cached_dividends() -> Dict[str, List[Dict[str, Any]]]:
    """Load cached dividend records."""
    if os.path.exists(BCS_DIVIDENDS_FILE):
        try:
            with open(BCS_DIVIDENDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[BCSClient] Error loading dividends cache: {e}")
    return {}

def save_dividends_cache(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save dividends cache."""
    try:
        with open(BCS_DIVIDENDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[BCSClient] Error saving dividends cache: {e}")

def load_cached_ratios() -> Dict[str, List[Dict[str, Any]]]:
    """Load cached financial ratios."""
    if os.path.exists(BCS_RATIOS_FILE):
        try:
            with open(BCS_RATIOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[BCSClient] Error loading ratios cache: {e}")
    return {}

def save_ratios_cache(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save financial ratios cache."""
    try:
        with open(BCS_RATIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[BCSClient] Error saving ratios cache: {e}")

async def _cdp_call(ws, method: str, params: Optional[Dict] = None, msg_id: int = 1):
    req = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(req))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data

async def _fetch_bcs_live_async(tasks_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute live headless Edge session to query official Bolsa de Santiago endpoints.
    tasks_config can request:
      - 'refresh_all_stocks': bool
      - 'symbols_for_ratios': list of strings
      - 'symbols_for_dividends': list of strings
    """
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp(prefix="bcs_analisis_")
    cmd = [
        EDGE_EXECUTABLE,
        "--headless=new",
        "--disable-gpu",
        "--disable-blink-features=AutomationControlled",
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
        f"--user-data-dir={temp_dir}",
        "--remote-debugging-port=9222",
        "about:blank"
    ]
    if not os.path.exists(EDGE_EXECUTABLE):
        print(f"[BCSClient] Error: Navegador no encontrado en '{EDGE_EXECUTABLE}'.")
        return {"error": f"Navegador no encontrado en {EDGE_EXECUTABLE}"}

    proc = subprocess.Popen(cmd)
    await asyncio.sleep(2)

    results = {}
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5) as resp:
            targets = json.loads(resp.read().decode('utf-8'))
        ws_url = targets[0]["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url) as ws:
            await _cdp_call(ws, "Page.enable", msg_id=1)
            await _cdp_call(ws, "Runtime.enable", msg_id=2)
            await _cdp_call(ws, "Page.navigate", {"url": BCS_MERCADO_URL}, msg_id=3)

            # Wait for Angular initialization
            for i in range(15):
                await asyncio.sleep(1)
                chk = await _cdp_call(ws, "Runtime.evaluate", {
                    "expression": "document.querySelector('[ng-app]') && window.angular && window.angular.element(document.querySelector('[ng-app]')).injector() ? true : false",
                    "returnByValue": True
                }, msg_id=100 + i)
                if chk.get("result", {}).get("result", {}).get("value") is True:
                    break

            config_json = json.dumps(tasks_config)
            exec_script = f"""
            (async function() {{
                var inj = window.angular.element(document.querySelector('[ng-app]')).injector();
                var csrfService = inj.get('csrfService');
                var cfg = {config_json};
                var out = {{}};

                // 1. Fetch All Market Stock Quotes if requested
                if (cfg.refresh_all_stocks) {{
                    try {{
                        var csrf = await csrfService.getApi();
                        var r = await fetch('/api/RV_ResumenMercado/getAccionesPrecios', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json;charset=UTF-8', 'X-CSRF-Token': csrf }},
                            body: '{{}}'
                        }});
                        var data = await r.json();
                        out.all_stocks = data.listaResult || [];
                    }} catch(e) {{
                        out.all_stocks_error = e.toString();
                    }}
                }}

                // 2. Fetch Financial Ratios for specific symbols
                if (cfg.symbols_for_ratios && cfg.symbols_for_ratios.length > 0) {{
                    out.ratios = {{}};
                    var today = new Date().toISOString().slice(0, 10);
                    for (var s of cfg.symbols_for_ratios) {{
                        try {{
                            var csrf = await csrfService.getApi();
                            var r = await fetch('/api/RV_Instrumentos/getRazonesFinancieras', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json;charset=UTF-8', 'X-CSRF-Token': csrf }},
                                body: JSON.stringify({{
                                    nemo: s,
                                    fecbal: today,
                                    tipobal: 'I',
                                    ajusteipc: 0,
                                    fecajuste: ''
                                }})
                            }});
                            var data = await r.json();
                            out.ratios[s] = data.listaResult || [];
                        }} catch(e) {{
                            out.ratios[s] = [];
                        }}
                    }}
                }}

                // 3. Fetch Dividends for specific symbols
                if (cfg.symbols_for_dividends && cfg.symbols_for_dividends.length > 0) {{
                    out.dividends = {{}};
                    for (var s of cfg.symbols_for_dividends) {{
                        try {{
                            var csrf = await csrfService.getApi();
                            var r = await fetch('/api/RV_ResumenMercado/getDividendos', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json;charset=UTF-8', 'X-CSRF-Token': csrf }},
                                body: JSON.stringify({{
                                    fec_pagoini: '2022-01-01',
                                    fec_pagofin: '2026-12-31',
                                    nemo: s
                                }})
                            }});
                            var data = await r.json();
                            out.dividends[s] = data.listaResult || [];
                        }} catch(e) {{
                            out.dividends[s] = [];
                        }}
                    }}
                }}

                return out;
            }})()
            """
            eval_res = await _cdp_call(ws, "Runtime.evaluate", {
                "expression": exec_script,
                "awaitPromise": True,
                "returnByValue": True
            }, msg_id=500)

            results = eval_res.get("result", {}).get("result", {}).get("value", {})
    except Exception as e:
        print(f"[BCSClient] Live fetch failed: {e}")
    finally:
        proc.terminate()
        await asyncio.sleep(1)
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Save any fetched all_stocks
    if "all_stocks" in results and results["all_stocks"]:
        try:
            with open(BCS_ALL_STOCKS_FILE, "w", encoding="utf-8") as f:
                json.dump(results["all_stocks"], f, indent=2)
        except Exception:
            pass

    # Merge any fetched dividends into dividends cache
    if "dividends" in results and results["dividends"]:
        cached_divs = load_cached_dividends()
        cached_divs.update(results["dividends"])
        save_dividends_cache(cached_divs)

    # Merge any fetched ratios into ratios cache
    if "ratios" in results and results["ratios"]:
        cached_ratios = load_cached_ratios()
        cached_ratios.update(results["ratios"])
        save_ratios_cache(cached_ratios)

    return results

def sync_all_stocks_live() -> List[Dict[str, Any]]:
    """Synchronously refresh quotes for all 1,000+ stocks from Bolsa de Santiago."""
    res = asyncio.run(_fetch_bcs_live_async({"refresh_all_stocks": True}))
    return res.get("all_stocks", load_all_market_stocks())

def fetch_live_stock_analysis(symbols: List[str]) -> Dict[str, Any]:
    """Fetch live quotes, financial ratios, and dividends for a list of symbols from Bolsa de Santiago."""
    tasks = {
        "refresh_all_stocks": True,
        "symbols_for_ratios": symbols,
        "symbols_for_dividends": symbols
    }
    return asyncio.run(_fetch_bcs_live_async(tasks))

def _extract_val(v1: Any, v2: Any) -> Optional[float]:
    """Extract primary value (v1), falling back to comparative/annual period (v2) if v1 is 0 or None."""
    try:
        if v1 is not None and float(v1) != 0:
            return float(v1)
        if v2 is not None and float(v2) != 0:
            return float(v2)
        if v1 is not None:
            return float(v1)
    except (ValueError, TypeError):
        pass
    return None

def parse_financial_ratios(raw_ratios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse raw list of ratios into a clean structured dictionary."""
    parsed = {
        "periodo": None,
        "eps_12m": None,
        "eps_6m": None,
        "book_value": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "roe": None,
        "net_margin": None,
        "gross_margin": None,
        "current_ratio": None,
        "quick_ratio": None,
        "debt_equity": None,
        "shares_outstanding": None,
        "closing_price": None
    }

    for item in raw_ratios:
        desc = item.get("DESCRIPCION", "")
        v1 = item.get("VALOR01")
        v2 = item.get("VALOR02")
        val = _extract_val(v1, v2)

        if desc == "PERIODO":
            parsed["periodo"] = f"{v1}/{v2}"
        elif "Util. x Accion en 12 Meses" in desc:
            parsed["eps_12m"] = val
        elif "Util. x Accion en 06 Meses" in desc:
            parsed["eps_6m"] = val
        elif "Valor Libro" in desc:
            parsed["book_value"] = val
        elif "Relacion Precio / Utilidad" in desc:
            parsed["pe_ratio"] = val if val is not None and val > 0 else None
        elif "Relacion Bolsa / Libro" in desc:
            parsed["pb_ratio"] = val if val is not None and val > 0 else None
        elif "Utilidad Neta / Cap. y Res." in desc:
            parsed["roe"] = val * 100 if val is not None and val != 0 else None
        elif "Utilidad Neta / Ventas" in desc:
            parsed["net_margin"] = val * 100 if val is not None and val != 0 else None
        elif "Margen Directo / Ventas" in desc:
            parsed["gross_margin"] = val * 100 if val is not None and val != 0 else None
        elif "Razon Circulante" in desc:
            parsed["current_ratio"] = val if val is not None and val > 0 else None
        elif "Razon Acida" in desc:
            parsed["quick_ratio"] = val if val is not None and val > 0 else None
        elif "Pasivo Exigible / Patrimonio" in desc:
            parsed["debt_equity"] = val
        elif "Acciones en Circulacion" in desc:
            parsed["shares_outstanding"] = val

    # ROE fallback calculation if not directly provided in interim ratios
    eps = parsed.get("eps_12m")
    bv = parsed.get("book_value")
    if (parsed.get("roe") is None or parsed.get("roe") == 0) and eps and eps > 0 and bv and bv > 0:
        parsed["roe"] = round((eps / bv) * 100, 2)

    return parsed
