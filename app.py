from flask import Flask, render_template, request
import pandas as pd
import yfinance as yf
from fredapi import Fred as Fed # Make sure you're importing correctly
from datetime import datetime, timedelta
#These next ones are for plotting:
import plotly.graph_objects as go
#To be able to render and output the plot correctly
import plotly.io as pio
import plotly.express as px
import plotly
import json


app = Flask(__name__)
#Takes in main if it is ran through this file, else if imported it takes in the name of the file

#_____________________________________

# Initialize a global default for discount rate in case obtaining the information fails
default__aaa_yield = 0.045 # 4.5%

try:
#My API key so i can access the FRED information
    fred = Fed(api_key='a99f8e0301913988401acd5680bd2c05') #ChatGPT generated use for key
    # API key as a string

# Get U.S. Discount Rate series from FRED
    interest_rate = fred.get_series('DAAA')#DAAA, FEDFUNDS
    
    #print("got this info", interest_rate)
    
    if not interest_rate.empty:
        
        latest_rate_date = interest_rate.last_valid_index()
        latest_rate_value = interest_rate[latest_rate_date]
        #print(latest_rate_value)
        
        if latest_rate_value > 1:
            latest_rate_value /= 100.0
        
    else:
        print("Warning: Could not retrieve FEDFUNDS series. Using fallback discount rate.")

except Exception:
    print(f"Error connecting to FRED or fetching data: {Exception}")
    print(f"Using fallback discount rate: {default__aaa_yield}")     

    
#Self made csv from list of stocks I obtained from CHat GPT
df = pd.read_csv("tickers.csv")


def volatility(ticker: str):
    try: 
        stock = yf.Ticker(ticker)
        time = stock.history(period = "1y")
        
        high = time['Close'].max()
        low = time['Close'].min()
        volatility_level = (high-low)/low
        
    except Exception:
        print("The stock selected does not have enough data to caluculate its volatility")
        
    return volatility_level

#_______________________________________

def get_stock_value(ticker: str, interest_rate2 = latest_rate_value):
    #Get the specific stock ticker data
    stock = yf.Ticker(ticker)
    #Get full name of company for better output
    company_name = stock.info.get("longName")

    try:
        #use datetime library to set the data to today to get latest data
        end_date = datetime.today()
        #start the time you are acquiring the information to 2 years ago:
        start_date = end_date - timedelta(days = 2*365)

        #Earnings-Per-Share:
        eps = stock.info.get("trailingEps")

        #Projected Future Price of Stock:
        current_price = stock.info.get("currentPrice")
        future_price = stock.info.get("targetMeanPrice")

        #Projected Growth-Rate:
        growth_rate = round(float(future_price/current_price -1),4) * 100

        print(f"Current AAA corporate bond yield: {(interest_rate2*100):.2f}%")

        #Dividends:
        dividends = stock.info.get("dividendYield")
        #print(dividends) .info.get("dividendYield")
        
        #Two different evaluations of the stock:
        intrinsic_value = ((eps*(7.5 + 1.5*growth_rate)*4.4)*(1+growth_rate/100))/(interest_rate2*100)
        #Simplified equation for the present value of a stock using one year's worth of data
        present_value = (future_price + dividends)/(1 + latest_rate_value)
        
        
        if intrinsic_value > current_price and present_value > current_price:
            return [f"The intrinsic value of {company_name} stock is: {intrinsic_value:.2f}" , f"The present value of {company_name} stock is: {present_value:.2f}" , "The stock may be undervalued, it is recommended to consider purchasing it!"]
            
        elif intrinsic_value < current_price and present_value < current_price:
            return [f"The intrinsic value of {company_name} stock is: {intrinsic_value:.2f}" , f"The present value of {company_name} stock is: {present_value:.2f}" , "The stock may be overvalued, it is recommended think twice before purchasing it!"]            
        else:
            return [f"The intrinsic value of {company_name} stock is: {intrinsic_value:.2f}" , f"The present value of {company_name} stock is: {present_value:.2f}" , "The stock is a solid consideration under one of the two evalutations, you may want to consider purchasing it"]
            
    except NameError:
        return ["There is not enough information on the selected stock", f"Stock Price: {current_price}"]
        
    except TypeError:
        return ["There is not enough information on the selected stock ", f"Stock Price: {current_price}"]
#_______________________________________

def get_news(ticker: str):
    stock = yf.Ticker(ticker)
    #Get news using the yf api from their news section on the website
    #Obtain the first ten news articles on a stock and organize as dictionary
    response = stock.get_news(count=10, tab='news')
    #Here we use that dictionary to extract the tile, summary, and link to the first and most important latest peace of news on the stock:
    return [f"{response[0]['content']['title']}" , f"{response[0]['content']['summary']}" ,f"{response[0]['content']['canonicalUrl']['url']}" ]
    
#_______________________________________

def get_graph(ticker: str):
    
    stock = yf.Ticker(ticker)
    company_name = stock.info.get("longName")
    #Force it to print out the graph    
    pio.renderers.default = 'iframe' #made by chat gpt

    end_date = datetime.today()
    #start the time you are acquiring the information to 2 years ago:
    start_date = end_date - timedelta(days = 2*365)

    current_price = stock.info.get("currentPrice")
    
    data_for_graph = yf.Ticker(ticker).history(period="2y").reset_index()
    
    if not data_for_graph.empty:
        #assign figure to the plotly.express graph with x axis called Date, and y axis Close Price
        fig = px.line(data_for_graph, x = 'Date', y = 'Close', title = f'{ticker} Stock Price')
        #Makes the trace of the line the color green because it is my favorite color
        fig.update_traces(line=dict(color='green'))

        fig.update_layout(
            xaxis_title = 'Date',
            yaxis_title = 'Stock Closing Price (USD)'
        )
        #prints out the figure/graph
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        return None
            


#_______________________________________
def get_recommended_stocks(risk_tolerance, sector_exclusions = None, price_range = "No limit", dividend_rate = "Low"):
    df = pd.read_csv("tickers.csv")
    list_of_stocks = []
    
    if risk_tolerance == "Low":
        list_of_stocks = [ticker for ticker in df['Ticker'] if volatility(ticker) <= 0.3]
    
    if risk_tolerance == "Medium":
        list_of_stocks = [ticker for ticker in df['Ticker'] if volatility(ticker) > 0.3 and volatility(ticker) <= 0.55] 
    
    if risk_tolerance == "High":
        list_of_stocks = [ticker for ticker in df['Ticker'] if volatility(ticker) >= 0.55]
    
    if sector_exclusions:
        if isinstance(sector_exclusions, str): #These two lines I had to reference chat gpt
            sector_exclusions = [sector_exclusions]
        
        list_of_stocks = [
            stock for stock in list_of_stocks
            if yf.Ticker(stock).info.get("sector") not in sector_exclusions
        ]
    if price_range == "0 - 100":
        list_of_stocks = [stock for stock in list_of_stocks if yf.Ticker(stock).info.get("currentPrice") < 100]
        
    elif price_range == "0 - 500":
        list_of_stocks = [stock for stock in list_of_stocks if yf.Ticker(stock).info.get("currentPrice") <= 500]
    
    elif price_range == "0 - 1000":
        list_of_stocks = [stock for stock in list_of_stocks if yf.Ticker(stock).info.get("currentPrice") < 1000]
    
    #Filtering stocks by dividend annual rate
    filtered_list = []
    if dividend_rate == "Low":
        for stock in list_of_stocks:
            try:
                dividend = yf.Ticker(stock).info.get("dividendRate")
                if dividend < 1:
                    filtered_list.append(stock)
                else:
                    filtered_list.append(stock)
            except:
                filtered_list.append(stock)
    elif dividend_rate == "Medium":
        for stock in list_of_stocks:
            try:
                dividend = yf.Ticker(stock).info.get("dividendRate")
                if dividend >= 1 and dividend < 2:
                    filtered_list.append(stock)
                else:
                    continue
            except:
                filtered_list = filtered_list
    elif dividend_rate == "High":
        for stock in list_of_stocks:
            try:
                dividend = yf.Ticker(stock).info.get("dividendRate")
                if dividend >= 2:
                    filtered_list.append(stock)
                else:
                    continue
            except:
                filtered_list = filtered_list

    return filtered_list

#_______________________________________

risk_levels = ["Low Risk (I love my money)", "Medium Risk (A little uncertainty can't hurt)", "High Risk (Go BIG or go BROKE)"]
price_range = ["$0 - $100", "$0 - $500", "No Limit"]
dividend_rate = ["Low (0% to 1%)", "Medium (1% to 2%)", "High (+2%)"]
sector_exclusions = [] #Whatever the user inputs

@app.route("/")
def page_1():
    return render_template("index.html")

@app.route("/stockapp", methods=["GET", "POST"])
def stock_lookup():
        return render_template("stockapp.html")

@app.route("/stock_recommendation")
def stock_recommend():
    return render_template("stockRec.html", risk_levels=risk_levels, price_range=price_range, dividend_rate=dividend_rate, sector_exclusions=sector_exclusions)


#_______________________________________

#I am currently working on this dont forget
@app.route("/result")
def stock_results():
    risk_tolerance = request.args.get("risk_tolerance")
    price_range = request.args.get("price_range")
    dividend_rate = request.args.get("dividend_rate")
    sector_exclusion = request.args.get("sector_exclusions")

    #I NEED TO MAKE THIS THING WORK!!!
    stock_output = get_recommended_stocks(risk_tolerance, sector_exclusion, price_range, dividend_rate)

    return render_template("result.html",risk_tolerance=risk_tolerance, price_range=price_range, dividend_rate=dividend_rate, sector_exclusion=sector_exclusion, stock_output=stock_output)
#_______________________________________ to do next

@app.route("/lookup_res")
def search_up_result():
    ticker = request.args.get("ticker")
    if ticker:
        news = get_news(ticker)
        value = get_stock_value(ticker)

        graphJSON = get_graph(ticker)
        if graphJSON is None:
            return "Invalid ticker or insufficient data.", 404

        return render_template("lookup_res.html", ticker=ticker, news=news, value=value, graphJSON=graphJSON)
    else:
        return "Invalid ticker or insufficient data.", 404


if __name__ == "__main__":
    app.run(debug=True)


    
    


