import yfinance as yf
from fredapi import Fred as Fed # Make sure you're importing correctly

# Replace 'your_api_key_here' with the actual API key, surrounded by quotes
fred = Fed(api_key='a99f8e0301913988401acd5680bd2c05')  # API key as a string

# Get U.S. Discount Rate series from FRED
interest_rate = fred.get_series('FEDFUNDS')

# Get the most recent (latest) value
latest_date = interest_rate.last_valid_index()  # Correct method to get the latest valid index
latest_rate = interest_rate[latest_date]

# Print the latest discount rate and date
print(f"Latest Discount Rate (as of {latest_date.date()}): {latest_rate}%")

def get_present_value(ticker: str, discount_rate = latest_rate):
    stock = yf.Ticker(ticker)
    breakdown = stock.info
    try:
        current_price = breakdown['regularMarketPrice']
        future_price = breakdown['targetMeanPrice']
        dividend = breakdown.get('dividendRate', 0.0)

        present_value = (dividend + future_price)/discount_rate


    except KeyError:
        print("THere is not enough information on the selected stock")
        print(f"Stock Price: {current_price}")
        print("Consider purchasing with a grain of salt (do more research!!!)")

#def projected_growth()
    
    


