# 🏛️ Analizador & Screener de Acciones Chilenas (Bolsa de Santiago)

Herramienta institucional e interactiva de **screener y análisis fundamental** enfocada en dividendos para el mercado accionario chileno. **El 100% de la información proviene directamente de la página oficial de la Bolsa de Comercio de Santiago (`bolsadesantiago.com`)**.

---

## 💎 Características Principales

1. **Datos 100% Oficiales de la Bolsa de Santiago:**
   - **Cotizaciones en Tiempo Real:** Precios de cierre oficial, puntas de compra (Bid), puntas de venta (Ask), variación porcentual diaria y montos transados.
   - **Razones Financieras Oficiales:** Relación Precio / Utilidad (P/U), Relación Bolsa / Valor Libro (P/VL), Rentabilidad sobre Patrimonio (ROE), Margen Neto, Razón Circulante y Nivel de Endeudamiento.
   - **Eventos de Dividendos Oficiales:** Fechas de corte (`fec_lim`), fechas de pago (`fec_pago`), montos exactos por acción en pesos chilenos (`val_acc`) y tipología (provisorio, definitivo, adicional).

2. **Pre-cargado con tus 10 Acciones de Portafolio:**
   - Al abrir la aplicación, ya dispones del diagnóstico completo de tus 10 acciones base: `AAISA`, `ANDINA-A`, `CENCOMALLS`, `CHILE`, `ENELGXCH`, `HABITAT`, `LIPIGAS`, `PEHUENCHE`, `QUINENCO` y `SOQUICOM`.

3. **Buscador & Analizador Universal:**
   - Permite agregar y analizar **cualquiera de las más de 1.000 acciones e instrumentos listados en la Bolsa de Santiago** (ej. `SQM-B`, `BCI`, `BSANTANDER`, `CCU`, `CMPC`, `COLBUN`, `COPEC`, `ENTEL`, `FALABELLA`, `VAPORES`, etc.).
   - Botón **"⚡ Analizar en Vivo"** para descargar al instante los datos oficiales de cualquier instrumento que no esté en la base local.

4. **Screener Multicriterio para Inversores en Dividendos:**
   - Filtros por **Dividend Yield Mínimo (%)**.
   - Filtros por **Valuación Máxima P/U**.
   - Filtros por **Rentabilidad Mínima ROE (%)**.
   - Filtros por **Señal de Inversión** (🟢 Compra / 🟡 Mantener / 🔴 Precaución).

5. **Sistema de Scoring Algorítmico (0 a 100 pts):**
   - **Rendimiento del Yield:** Atractivo del dividendo actual (> 7.5% otorga puntaje máximo).
   - **Seguridad del Payout:** Cobertura de las utilidades (payout saludable entre 30% y 70%).
   - **Rentabilidad Empresarial (ROE):** Capacidad de la empresa para generar retornos sobre su patrimonio.
   - **Valuación y Descuento:** Múltiplos P/U y P/VL favorables para evitar comprar sobrevalorado.

6. **Comparador Head-to-Head & Simulador de Inversión:**
   - Comparación lado a lado de 2 o más empresas para decidir entre competidores directos (ej. bancos, eléctricas, embotelladoras).
   - Simulador que calcula las acciones que comprarías con \$X capital, proyecta los dividendos anuales y mensuales esperados, y compara contra la tasa de interés de renta fija libre de riesgo.

---

## 📂 Estructura de Archivos

```
Analisis Acciones/
│
├── app.py                      # Interfaz interactiva en Streamlit (puerto 8502)
├── bcs_client.py               # Conector oficial con la API de Bolsa de Santiago
├── screener_engine.py          # Motor de métricas, scoring de dividendos y señales
├── config.py                   # Configuración y listado de acciones
├── run_analisis.bat            # Lanzador rápido en 1 clic (Windows)
├── README.md                   # Documentación detallada
└── data/
    ├── bcs_all_market_stocks.json    # Base de datos de 1.052 acciones de la Bolsa
    ├── bcs_ratios_cache.json         # Razones financieras oficiales (P/U, ROE, etc.)
    └── bcs_dividends_cache.json      # Historial oficial de dividendos pagados
```

---

## 🚀 Cómo Ejecutar la Aplicación en Cualquier PC

### Requisitos Previos:
- Tener instalado **Python 3.10 o superior** (al instalar en Windows, marcar la casilla **"Add Python to PATH"**).
- Navegador web moderno (Microsoft Edge o Google Chrome).

### Ejecución en 1 Clic (Recomendado):
Haz doble clic sobre el archivo **`run_analisis.bat`**.
> **Nota:** El archivo `.bat` detectará automáticamente Python e instalará todas las dependencias necesarias (`streamlit`, `pandas`, `plotly`, etc.) si no las tienes, y abrirá la aplicación en tu navegador.

### Ejecución Manual desde Terminal:
```powershell
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

La aplicación se abrirá en tu navegador web en:
👉 **`http://localhost:8502`**
*(Configurada en el puerto 8502 para convivir simultáneamente con otras apps de Streamlit).*
