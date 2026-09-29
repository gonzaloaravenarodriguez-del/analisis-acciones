import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import bcs_client
from config import INITIAL_PORTFOLIO_SYMBOLS

# Chilean Stock Metadata: Sector, Archetype, Inflation Indexation, and Article 107 LIR Status
STOCK_METADATA = {
    "ENELGXCH": {"nombre": "Enel Generación Chile", "sector": "Servicios Básicos / Electricidad", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🛡️ UF / USD (Anti-inflación)", "presencia_107": True},
    "LIPIGAS": {"nombre": "Empresas Lipigas", "sector": "Gas / Combustibles", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🇨🇱 CLP (Demanda Inelástica)", "presencia_107": True},
    "PEHUENCHE": {"nombre": "Empresa Eléctrica Pehuenche", "sector": "Servicios Básicos / Electricidad", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🛡️ UF / USD", "presencia_107": True},
    "HABITAT": {"nombre": "AFP Habitat", "sector": "Servicios Financieros / Pensiones", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🇨🇱 CLP (Comisión Legal)", "presencia_107": True},
    "CHILE": {"nombre": "Banco de Chile", "sector": "Banca / Financiero", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 UF / CLP (Cartera Reajustable)", "presencia_107": True},
    "CENCOMALLS": {"nombre": "Cencosud Shopping", "sector": "Bienes Raíces / Centros Comerciales", "arquetipo": "🚀 Dividend Growth", "indexacion": "🛡️ 100% UF (Contratos Indexados)", "presencia_107": True},
    "ANDINA-A": {"nombre": "Embotelladora Andina A", "sector": "Consumo Masivo / Bebidas", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 CLP (Consumo Defensivo)", "presencia_107": True},
    "QUINENCO": {"nombre": "Quiñenco S.A.", "sector": "Holding / Conglomerado", "arquetipo": "📦 Holding con Descuento", "indexacion": "🇨🇱 Mixto (Grupo Luksic)", "presencia_107": True},
    "AAISA": {"nombre": "Administradora Americana", "sector": "Holding / Financiero", "arquetipo": "📦 Holding con Descuento", "indexacion": "🇨🇱 CLP", "presencia_107": False},
    "SOQUICOM": {"nombre": "Soquimich Comercial", "sector": "Comercial / Fertilizantes", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🇨🇱 CLP / USD", "presencia_107": True},
    "SQM-B": {"nombre": "Sociedad Química y Minera B", "sector": "Minería / Litio y Fertilizantes", "arquetipo": "⏳ Cíclica / Commodity", "indexacion": "💵 100% USD", "presencia_107": True},
    "VAPORES": {"nombre": "CSAV (Vapores)", "sector": "Transporte Marítimo", "arquetipo": "⏳ Cíclica / Commodity", "indexacion": "💵 100% USD (Hapag-Lloyd)", "presencia_107": True},
    "CAP": {"nombre": "CAP S.A.", "sector": "Minería / Hierro y Acero", "arquetipo": "⏳ Cíclica / Commodity", "indexacion": "💵 100% USD", "presencia_107": True},
    "BCI": {"nombre": "Banco BCI", "sector": "Banca / Financiero", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 UF / CLP / USD", "presencia_107": True},
    "BSANTANDER": {"nombre": "Banco Santander Chile", "sector": "Banca / Financiero", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 UF / CLP", "presencia_107": True},
    "COLBUN": {"nombre": "Colbún S.A.", "sector": "Servicios Básicos / Electricidad", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🛡️ UF / USD", "presencia_107": True},
    "COPEC": {"nombre": "Empresas Copec", "sector": "Forestal / Combustibles", "arquetipo": "⏳ Cíclica / Commodity", "indexacion": "💵 USD / CLP", "presencia_107": True},
    "CMPC": {"nombre": "Empresas CMPC", "sector": "Forestal / Celulosa y Papel", "arquetipo": "⏳ Cíclica / Commodity", "indexacion": "💵 USD / CLP", "presencia_107": True},
    "CCU": {"nombre": "Compañía Cervecerías Unidas", "sector": "Consumo Masivo / Bebidas", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 CLP", "presencia_107": True},
    "MALLPLAZA": {"nombre": "Plaza S.A.", "sector": "Bienes Raíces / Centros Comerciales", "arquetipo": "🚀 Dividend Growth", "indexacion": "🛡️ 100% UF", "presencia_107": True},
    "PARAUCO": {"nombre": "Parque Arauco", "sector": "Bienes Raíces / Centros Comerciales", "arquetipo": "🚀 Dividend Growth", "indexacion": "🛡️ 100% UF", "presencia_107": True},
    "ENTEL": {"nombre": "Entel Chile", "sector": "Telecomunicaciones", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🇨🇱 CLP / USD", "presencia_107": True},
    "ECL": {"nombre": "Engie Energía Chile", "sector": "Servicios Básicos / Electricidad", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🛡️ UF / USD", "presencia_107": True},
    "EMBONOR-B": {"nombre": "Coca-Cola Embonor B", "sector": "Consumo Masivo / Bebidas", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 CLP", "presencia_107": True},
    "FALABELLA": {"nombre": "Falabella S.A.", "sector": "Retail / Comercio", "arquetipo": "🚀 Dividend Growth", "indexacion": "🇨🇱 CLP", "presencia_107": True},
    "SMU": {"nombre": "SMU S.A. (Unimarc)", "sector": "Retail / Supermercados", "arquetipo": "🐄 Vaca Lechera", "indexacion": "🇨🇱 CLP", "presencia_107": True},
}

def calculate_ttm_dividend(dividend_events: List[Dict[str, Any]], ref_date: Optional[datetime] = None) -> float:
    """Calculate Trailing Twelve Months (TTM) dividend per share from Bolsa de Santiago events."""
    if not dividend_events:
        return 0.0

    ref = ref_date or datetime.now()
    one_year_ago = (ref - timedelta(days=365)).strftime("%Y-%m-%d")

    ttm_sum = 0.0
    for ev in dividend_events:
        pago = str(ev.get("fec_pago", ""))[:10]
        if pago >= one_year_ago:
            val = float(ev.get("val_acc", 0.0) or 0.0)
            ttm_sum += val

    # Fallback to most recent calendar year with dividends if none in past 365 days
    if ttm_sum == 0.0:
        years = {}
        for ev in dividend_events:
            pago = str(ev.get("fec_pago", ""))[:4]
            if pago.isdigit():
                y = int(pago)
                years[y] = years.get(y, 0.0) + float(ev.get("val_acc", 0.0) or 0.0)
        if years:
            latest_year = max(years.keys())
            ttm_sum = years[latest_year]

    return round(ttm_sum, 4)

def calculate_yearly_dividends(dividend_events: List[Dict[str, Any]]) -> Dict[int, float]:
    """Calculate yearly dividends per share."""
    yearly = {}
    for ev in dividend_events:
        pago = str(ev.get("fec_pago", ""))[:4]
        if pago.isdigit():
            y = int(pago)
            val = float(ev.get("val_acc", 0.0) or 0.0)
            yearly[y] = round(yearly.get(y, 0.0) + val, 4)
    return dict(sorted(yearly.items()))

def calculate_chilean_tax_credit(div_ttm: float) -> Dict[str, float]:
    """
    Calculate Chilean First Category Tax Credit (27%) under the Semi-Integrated System (Art. 14 A LIR).
    Shareholder gets an imputable tax credit of 65% of corporate tax paid.
    """
    if div_ttm <= 0:
        return {"credito_bruto": 0.0, "credito_imputable": 0.0, "dividendo_incrementado": 0.0}

    # Gross-up factor: 1 / (1 - 0.27) = 1.369863
    div_incrementado = div_ttm / (1 - 0.27)
    credito_bruto = div_incrementado * 0.27
    credito_imputable = credito_bruto * 0.65  # 65% imputable after 35% restitution

    return {
        "credito_bruto": round(credito_bruto, 3),
        "credito_imputable": round(credito_imputable, 3),
        "dividendo_incrementado": round(div_incrementado, 3)
    }

def detect_dividend_trap_flags(
    div_yield: float,
    payout_ratio: Optional[float],
    roe: Optional[float],
    pe_ratio: Optional[float]
) -> List[str]:
    """Detect institutional red flags for potential dividend traps."""
    flags = []
    if payout_ratio is not None and payout_ratio > 100.0:
        flags.append(f"⚠️ Payout Insostenible ({payout_ratio:.1f}%): Paga más de lo que gana.")
    if roe is not None and roe < 4.0:
        flags.append(f"⚠️ ROE Deprimido ({roe:.1f}%): Rentabilidad sobre patrimonio muy baja.")
    if div_yield > 12.0 and payout_ratio is not None and payout_ratio > 95.0:
        flags.append("🔴 Trampa de Alto Yield: Rendimiento artificial por ciclo o caída de precio.")
    if pe_ratio is not None and pe_ratio > 40.0:
        flags.append(f"⚠️ Múltiplo P/U Desconectado ({pe_ratio:.1f}x): Excesivamente cara.")
    return flags

def calculate_expert_checklist(
    div_yield: float,
    payout_ratio: Optional[float],
    roe: Optional[float],
    pe_ratio: Optional[float],
    indexacion: str,
    benchmark_rf: float = 4.0
) -> Dict[str, Any]:
    """
    Evaluate the 5 Golden Rules of Institutional Dividend Investing in Chile:
    1. Yield Spread vs Renta Fija (Tasa DAP seleccionable por usuario + 1.5%)
    2. Payout Saludable (< 75%)
    3. Rentabilidad ROE (> 10%)
    4. Valuación Razonable (P/U < 15x)
    5. Escudo Inflacionario (UF o Monopolio Natural)
    """
    min_target = benchmark_rf + 1.5
    r1 = div_yield >= min_target
    r2 = payout_ratio is not None and (0 < payout_ratio <= 75.0)
    r3 = roe is not None and roe >= 10.0
    r4 = pe_ratio is not None and (0 < pe_ratio <= 15.0)
    r5 = "UF" in indexacion or "Inelástica" in indexacion or "Monopolio" in indexacion

    rules = [
        {"regla": f"Supera al Depósito a Plazo ({benchmark_rf:.1f}%) por al menos +1.5%", "cumple": r1, "detalle": f"Yield: {div_yield:.2f}% (Meta: >= {min_target:.1f}%)"},
        {"regla": "Payout Sostenible (<= 75% de utilidades netas)", "cumple": r2, "detalle": f"Payout: {payout_ratio:.1f}%" if payout_ratio else "Sin dato"},
        {"regla": "Negocio Rentable de Calidad (ROE >= 10%)", "cumple": r3, "detalle": f"ROE: {roe:.1f}%" if roe else "Sin dato"},
        {"regla": "Valuación Atractiva o Razonable (P/U <= 15x)", "cumple": r4, "detalle": f"P/U: {pe_ratio:.1f}x" if pe_ratio else "Sin dato"},
        {"regla": "Foso Defensivo / Protección Inflacionaria (UF o Monopolio)", "cumple": r5, "detalle": indexacion}
    ]

    passed_count = sum(1 for r in rules if r["cumple"])
    confidence_pct = (passed_count / 5.0) * 100.0

    return {
        "rules": rules,
        "passed_count": passed_count,
        "confidence_pct": round(confidence_pct),
        "status": "Alta Convicción" if passed_count >= 4 else "Moderada" if passed_count >= 2 else "Baja Convicción"
    }

def calculate_dividend_score_and_signal(
    div_yield: float,
    payout_ratio: Optional[float],
    roe: Optional[float],
    pe_ratio: Optional[float],
    pb_ratio: Optional[float],
    cagr_3y: Optional[float],
    arquetipo: str = ""
) -> Dict[str, Any]:
    """Score a stock from 0 to 100 based on dividend investment criteria."""
    score = 0
    rationales = []

    # 1. Yield Score (0 - 25)
    if div_yield >= 7.5:
        score += 25
        rationales.append("Alto Dividend Yield (> 7.5%)")
    elif div_yield >= 5.0:
        score += 20
        rationales.append("Dividend Yield Atractivo (5% - 7.5%)")
    elif div_yield >= 3.0:
        score += 14
        rationales.append("Dividend Yield Moderado (3% - 5%)")
    elif div_yield > 0:
        score += 8
        rationales.append("Dividend Yield Bajo (< 3%)")
    else:
        score += 0
        rationales.append("Sin Dividendos Recientes")

    # 2. Payout Safety (0 - 25)
    if payout_ratio is not None and payout_ratio > 0:
        if 30 <= payout_ratio <= 70:
            score += 25
            rationales.append("Payout Óptimo (30% - 70%)")
        elif 70 < payout_ratio <= 85:
            score += 18
            rationales.append("Payout Aceptable (70% - 85%)")
        elif 85 < payout_ratio <= 100:
            score += 12
            rationales.append("Payout Alto (85% - 100%)")
        elif payout_ratio > 100:
            score += 5
            rationales.append("⚠️ Payout Peligroso (> 100%: paga más de lo que gana)")
        elif payout_ratio < 30:
            score += 18
            rationales.append("Payout Conservador (< 30%)")
    else:
        score += 14

    # 3. Profitability / ROE (0 - 25)
    if roe is not None:
        if roe >= 15.0:
            score += 25
            rationales.append("Alta Rentabilidad ROE (> 15%)")
        elif roe >= 10.0:
            score += 19
            rationales.append("Buen ROE (10% - 15%)")
        elif roe >= 5.0:
            score += 12
            rationales.append("ROE Moderado (5% - 10%)")
        elif roe > 0:
            score += 5
            rationales.append("Bajo ROE (< 5%)")
        else:
            score += 0
            rationales.append("⚠️ ROE Negativo (Pérdidas)")
    else:
        score += 12

    # 4. Valuation / Multiples (0 - 25)
    val_points = 0
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio < 12.0:
            val_points += 15
            rationales.append("Valuación Atractiva P/U (< 12x)")
        elif pe_ratio <= 18.0:
            val_points += 10
            rationales.append("Valuación Razonable P/U (12x - 18x)")
        else:
            val_points += 4
            rationales.append("P/U Elevado (> 18x)")
    else:
        val_points += 8

    if pb_ratio is not None and pb_ratio > 0:
        if pb_ratio <= 1.5:
            val_points += 10
            rationales.append("Cotiza cerca o bajo Valor Libro (P/VL <= 1.5x)")
        elif pb_ratio <= 3.0:
            val_points += 6
        else:
            val_points += 2
    else:
        val_points += 5

    score += min(25, val_points)

    # Growth bonus
    if cagr_3y is not None and cagr_3y > 5.0:
        score = min(100, score + 5)
        rationales.append("Historial de Dividendos Crecientes")

    # Signal Classification
    if score >= 72:
        signal = "COMPRA / DIVIDENDO FUERTE"
        badge = "🟢"
        color = "#00d084"
    elif score >= 52:
        signal = "MANTENER / ESTABLE"
        badge = "🟡"
        color = "#ffa726"
    else:
        signal = "PRECAUCIÓN / BAJO RENDIMIENTO"
        badge = "🔴"
        color = "#ff4d4f"

    return {
        "score": round(score),
        "signal": signal,
        "badge": badge,
        "color": color,
        "rationales": rationales
    }

def build_screener_table(symbols: Optional[List[str]] = None, benchmark_rf: float = 4.0) -> pd.DataFrame:
    """Build unified screener DataFrame for selected symbols with expert metrics."""
    all_stocks = bcs_client.load_all_market_stocks()
    stock_dict = {s.get("NEMO"): s for s in all_stocks if s.get("NEMO")}
    
    dividends_cache = bcs_client.load_cached_dividends()
    ratios_cache = bcs_client.load_cached_ratios()

    target_symbols = symbols or INITIAL_PORTFOLIO_SYMBOLS

    rows = []
    for sym in target_symbols:
        quote = stock_dict.get(sym, {})
        price = float(quote.get("PRECIO_CIERRE", 0.0) or 0.0)
        var_pct = float(quote.get("VARIACION", 0.0) or 0.0)
        monto = float(quote.get("MONTO", 0.0) or 0.0)
        bid = float(quote.get("PRECIO_COMPRA", 0.0) or 0.0)
        ask = float(quote.get("PRECIO_VENTA", 0.0) or 0.0)
        isin = quote.get("ISIN", "-")

        # Metadata
        meta = STOCK_METADATA.get(sym, {
            "nombre": sym,
            "sector": "Renta Variable",
            "arquetipo": "🐄 Vaca Lechera" if price > 0 else "Renta Variable",
            "indexacion": "🇨🇱 CLP",
            "presencia_107": True
        })

        # Dividends
        div_events = dividends_cache.get(sym, [])
        div_ttm = calculate_ttm_dividend(div_events)
        div_yield_pct = (div_ttm / price * 100) if price > 0 else 0.0
        
        yearly_divs = calculate_yearly_dividends(div_events)
        div_2026 = yearly_divs.get(2026, 0.0)
        div_2025 = yearly_divs.get(2025, 0.0)
        div_2024 = yearly_divs.get(2024, 0.0)

        # 3-year CAGR
        d22 = yearly_divs.get(2022, 0.0)
        d25 = yearly_divs.get(2025, 0.0)
        cagr_3y = round(((d25 / d22) ** (1 / 3) - 1) * 100, 1) if d22 > 0 and d25 > 0 else None

        # Financial Ratios
        raw_ratios = ratios_cache.get(sym, [])
        ratios = bcs_client.parse_financial_ratios(raw_ratios)

        eps = ratios.get("eps_12m")
        book_val = ratios.get("book_value")
        roe = ratios.get("roe")
        net_margin = ratios.get("net_margin") if ratios.get("net_margin") is not None else ratios.get("gross_margin")
        debt_eq = ratios.get("debt_equity")

        if (roe is None or roe == 0) and eps and eps > 0 and book_val and book_val > 0:
            roe = round((eps / book_val) * 100, 2)

        pe_ratio = ratios.get("pe_ratio")
        if (pe_ratio is None or pe_ratio == 0) and price > 0 and eps and eps > 0:
            pe_ratio = round(price / eps, 2)

        pb_ratio = ratios.get("pb_ratio")
        if (pb_ratio is None or pb_ratio == 0) and price > 0 and book_val and book_val > 0:
            pb_ratio = round(price / book_val, 2)

        payout_ratio = round((div_ttm / eps * 100), 1) if eps and eps > 0 else None

        # Tax Credit Calculation (Chilean Semi-Integrated System)
        tax_info = calculate_chilean_tax_credit(div_ttm)
        credito_imp = tax_info["credito_imputable"]
        div_gross_with_tax = div_ttm + credito_imp
        yield_con_credito = (div_gross_with_tax / price * 100) if price > 0 else 0.0

        # Dividend Trap Flags
        trap_flags = detect_dividend_trap_flags(div_yield_pct, payout_ratio, roe, pe_ratio)

        # Expert Checklist
        checklist = calculate_expert_checklist(
            div_yield=div_yield_pct,
            payout_ratio=payout_ratio,
            roe=roe,
            pe_ratio=pe_ratio,
            indexacion=meta["indexacion"],
            benchmark_rf=benchmark_rf
        )

        # Scoring
        score_eval = calculate_dividend_score_and_signal(
            div_yield=div_yield_pct,
            payout_ratio=payout_ratio,
            roe=roe,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            cagr_3y=cagr_3y,
            arquetipo=meta["arquetipo"]
        )

        rows.append({
            "NEMO": sym,
            "Nombre": meta["nombre"],
            "Sector": meta["sector"],
            "Arquetipo": meta["arquetipo"],
            "Indexacion": meta["indexacion"],
            "Presencia_107": "✅ Sí (10% Impuesto)" if meta["presencia_107"] else "⚠️ No (Tasa General)",
            "Precio_CLP": price,
            "Variacion_Pct": var_pct,
            "Div_TTM_CLP": div_ttm,
            "Dividend_Yield_Pct": round(div_yield_pct, 2),
            "Credito_Tributario_CLP": credito_imp,
            "Yield_Con_Credito_Pct": round(yield_con_credito, 2),
            "Score_Dividendo": score_eval["score"],
            "Senal": f"{score_eval['badge']} {score_eval['signal']}",
            "PE_Ratio": round(pe_ratio, 2) if pe_ratio else None,
            "PB_Ratio": round(pb_ratio, 2) if pb_ratio else None,
            "ROE_Pct": round(roe, 1) if roe else None,
            "Payout_Ratio_Pct": payout_ratio,
            "EPS_12M_CLP": eps,
            "Valor_Libro_CLP": book_val,
            "Margen_Neto_Pct": round(net_margin, 1) if net_margin else None,
            "Deuda_Patrimonio": round(debt_eq, 2) if debt_eq else None,
            "Monto_Transado_CLP": monto,
            "Bid_CLP": bid,
            "Ask_CLP": ask,
            "Div_2026_CLP": div_2026,
            "Div_2025_CLP": div_2025,
            "Div_2024_CLP": div_2024,
            "CAGR_3Y_Pct": cagr_3y,
            "Ultimo_Pago": str(div_events[0].get("fec_pago", "-"))[:10] if div_events else "-",
            "Total_Eventos_BCS": len(div_events),
            "ISIN": isin,
            "Trap_Flags": trap_flags,
            "Checklist": checklist,
            "Rationales": score_eval["rationales"]
        })

    return pd.DataFrame(rows)

def get_detailed_stock_report(symbol: str, benchmark_rf: float = 4.0) -> Dict[str, Any]:
    """Compile comprehensive single-stock dossier directly from official Bolsa data."""
    df_single = build_screener_table([symbol], benchmark_rf=benchmark_rf)
    row = df_single.iloc[0].to_dict() if not df_single.empty else {}
    
    divs_cache = bcs_client.load_cached_dividends()
    events = divs_cache.get(symbol, [])
    
    ratios_cache = bcs_client.load_cached_ratios()
    raw_ratios = ratios_cache.get(symbol, [])
    parsed_ratios = bcs_client.parse_financial_ratios(raw_ratios)

    yearly = calculate_yearly_dividends(events)

    return {
        "summary": row,
        "events": events,
        "yearly_dividends": yearly,
        "parsed_ratios": parsed_ratios,
        "raw_ratios": raw_ratios
    }
