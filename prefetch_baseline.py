import bcs_client
from config import INITIAL_PORTFOLIO_SYMBOLS

print(f"Fetching financial ratios and quotes for baseline portfolio: {INITIAL_PORTFOLIO_SYMBOLS}")
data = bcs_client.fetch_live_stock_analysis(INITIAL_PORTFOLIO_SYMBOLS)
print("Finished!")
print("Ratios keys:", list(data.get("ratios", {}).keys()))
print("Dividends keys:", list(data.get("dividends", {}).keys()))
