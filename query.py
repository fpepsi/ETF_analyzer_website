import os
import csv
import pandas as pd
import requests
import constants as c
import json
import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
from dotenv import load_dotenv
from typing import Union, Dict
#%%
load_dotenv()
matplotlib.use('Agg')  # Use a non-interactive backend
# API access settings and parameters
alphavantage_key = os.environ.get("ALPHAVANTAGE_API_KEY")
alphavantage_url = "https://www.alphavantage.co/query"


class query_alphavantage():
    def __init__(self, time):
        self.EST_time = time   # time is required to manage files per query days
        # variables obtained from get_AlphaV_securities()
        self.app_variable_list = []  # list to hold the "N" constants which are API search parameters
        self.active_securities = None # list of all active securities
        self.names_list = []  # ETF-filtered list from the active securities list
        # variables selected by user for analysis
        self.ETF_symbol = str # ETF symbol picked by user from website dropdown list for analysis
        self.ts_periodicity = str # user selects if data is daily, weekly or mothly
        self.calculations = [] # list of studies selected by user
        # variables obtained from get_ETF_dataset()
        self.ETF_name = str  # ETF name from active_securities list corresponding to ETF_symbol
        self.ETF_data = {}  # ETF descriptive data
        self.sectors = []  # ETF sectors data used for pie chart
        self.weights = [] # ETF weights data used for pie chart
        self.sorted_data = []  # list of all ETF components sorted by weight
        self.fetch_list = [] # sublist from sorted_data containing (up to) the top N1 securities symbols
        # variables obtained from get_components_prices()
        self.top_n_components_df = {} # dictionary where keys are components' symbols and values are time series
        self.first_date = None # first date from time series
        self.last_date = None # last day from time series
        self.periodicity = str # time series daily / weekly / monthly
        # variables obtained from get_statistical_data()
        self.studies_data = {}  # statistics data from alphavantage
        # variables obtained from generate_charts()
        self.ETF_candle = str # ETF candle chart address
        self.pie_chart = str # pie chart address
        self.normalized_chart = str # address of historic normalized prices
        self.candle_charts = [] # list of candle charts addresses
        self.study_metrics = [] # list of univariate metrics
        self.study_histograms = []  # histograms charts
        self.study_matrices = [] # list of multivariate tables
        

    def clean_up_directory(self):
        '''This function deletes all files in the "static" directory that do not contain the current date
        OR creates the "static" directory if it doesn't exist'''
        files_path = os.path.join(os.getcwd(), "static")

        if os.path.exists(files_path):
            for file in os.listdir(files_path):
                file_path = os.path.join(files_path, file)
                if self.EST_time not in file:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file}")
                    except Exception as e:
                        print(f"Error deleting {file}: {e}")

        else:
            print(f"Directory '{files_path}' does not exist. Creating {files_path} directory")
            os.mkdir(files_path)


    def check_file_exists(self, file_name):
        '''this function checks if file_name already exists to avoid unnecessary API calls on multiple searches'''
        if os.path.exists(file_name):  # File exists
            try:
                if file_name.endswith('csv'):
                    data = pd.read_csv(file_name, header=0)
                elif file_name.endswith('json'):
                    with open(file_name, "r") as file:
                        data = json.load(file)
                print(f"File found: {file_name}. Loaded data successfully.")
                return data  # Return file data if successfully loaded
            except Exception as e:
                print(f"Error reading CSV file: {e}")
                return None  # Return None if reading fails
        else:
            print(f"File not found: {file_name}. Making API request...")
            return None  # Explicitly return None when the file is missing
        

    def save_to_file(self, data, file_name):
        ''' this function save the data obtained from the API to files so they can be retained and processed '''
        os.makedirs("static", exist_ok=True)  # Ensure the directory exists
        if file_name.endswith('csv'):
            # Save to CSV file 
            data.to_csv(file_name, index=False)  # Save the DataFrame to a new CSV file
        elif file_name.endswith('json'):
            with open(file_name, "w") as file:
                json.dump(data, file, indent=4)


    def query_API(self, datatype: str, params: Dict) -> Union[Dict, pd.DataFrame]:
        ''' this function receives Alphavantage query parameters as well as the datatype returned by the API and
        retrurns the data in whichever response format is obtained, according to API documentation'''
        try:
            if datatype == "json":
                response = requests.get(alphavantage_url, params=params, timeout=10)  # Set timeout for safety
                response.status_code 
                response.raise_for_status()  # Raises an error for HTTP 4xx or 5xx
                try:
                    data = response.json()  # Ensure response is valid JSON
                except ValueError:  # Catches invalid JSON errors
                    print("Error: Response is not a valid JSON format.")
                    data = {}  # Default to an empty dictionary
            elif datatype == "csv":
                response = requests.get(alphavantage_url, params=params, timeout=10)  # Set timeout for safety
                response.status_code 
                response.raise_for_status()  # Raises an error for HTTP 4xx or 5xx
                decoded_content = response.content.decode('utf-8')
                csv_obj = csv.reader(decoded_content.splitlines(), delimiter=',')
                header = next(csv_obj)  # Extract the header row
                rows = [row for row in csv_obj]  # Extract the remaining rows
                data = pd.DataFrame(rows, columns=header) # Create a Pandas DataFrame
                data = data[data['name'].notna()] # cleanup lines missing a name
        except requests.exceptions.RequestException as err:
            print(f"Request failed: {err}")
            data = {}
        return data


    def plot_multiple_stocks(self, stock_data_dict, symbol, time):
        """ Plots multiple stock price movements in a single chart using normalized values. """
        if len(stock_data_dict) == 0:
            file_name = "static/not_available.jpg"
        else:
            file_name = f'static/{symbol}_ETF_Components_{time}.png'
            plt.figure(figsize=(12, 6))

            for symbol, df in stock_data_dict.items():
                df.index = pd.to_datetime(df.index).date
                df = df.sort_index(ascending=True)
                # Normalize prices: First price = 1, all others relative
                df["normalized"] = df["close"] / df["close"].iloc[0]
                plt.plot(df.index, df["normalized"], label=symbol)

            plt.xlabel("Date")
            plt.ylabel("Normalized Prices")
            plt.title("Normalized ETF Components Price Movements")
            plt.legend()
            plt.grid()
            plt.savefig(file_name)
            plt.close()
        return file_name


    def get_AlphaV_securities(self):
        ''' search active securities database '''
        # prepare directory and variables to be rendered
        self.clean_up_directory()
        self.app_variable_list = [c.N1, c.N2, c.N3, c.N4, c.N5]
        self.names_list = []

        file_name = f"static/active_securities_{self.EST_time}.csv"
        self.active_securities = self.check_file_exists(file_name)
        if self.active_securities is None:
            params = c.LISTED_SECURITIES_PARAMS
            params['date'] = self.EST_time
            params['apikey'] = alphavantage_key
            self.active_securities = self.query_API('csv', params)
            self.save_to_file(self.active_securities, file_name) 
        # data processing - creates a list with all ETF components, plus the ETF itself
        ETF_df = self.active_securities[self.active_securities["assetType"].str.contains("ETF", na=False, case=False)]
        self.names_list = ETF_df["symbol"].tolist()


    def get_ETF_dataset(self):
        ''' fetch ETF dataset '''
        self.ETF_name = self.active_securities[self.active_securities["symbol"] == self.ETF_symbol]["name"].iloc[0]
        file_name = f"static/ETF_{self.ETF_symbol}_{self.EST_time}.json"
        data = self.check_file_exists(file_name)  # check if there is an updated file in place
        if data is None:
            params = c.ETF_QUERY_PARAMS
            params['symbol'] = self.ETF_symbol
            params['apikey'] = alphavantage_key
            data = self.query_API('json', params)
            self.save_to_file(data, file_name)  
        # data processing - Extract sectors and weights information for pie chart
        self.ETF_data = {
            "name": self.ETF_name,
            "net_assets": data["net_assets"],
            "net_expense_ratio": data["net_expense_ratio"],
            "portfolio_turnover": data["portfolio_turnover"],
            "dividend_yield": data["dividend_yield"],
            "inception_date": data["inception_date"],
            "leveraged": data["leveraged"],
        }
        self.sectors = [item["sector"] for item in data["sectors"]]
        self.weights = [float(item["weight"]) for item in data["sectors"]]
        # prepares data for next query by sorting ETF components in decreasing weight order
        data["holdings"].sort(key=lambda x: float(x["weight"]), reverse=True)
        self.sorted_data  = data["holdings"]
        self.fetch_list = [holding['symbol'] for holding in self.sorted_data][:c.N1]
        self.fetch_list.insert(0, self.ETF_symbol)  # adds the ETF to the list as it is needed for performance comparison

    def get_components_prices(self):
        ''' fetch historical data for ETF and top n components ''' 
        n = c.N1
        time_series = {}
        params = c.TIME_SERIES_PARAMS
        params["function"] = self.ts_periodicity
        params["outputsize"] = c.N4 
        params["datatype"] = "json"
        params["apikey"] = alphavantage_key

        for item in self.fetch_list:
            params["symbol"] = item
            file_name = f'static/{item}_{params["function"]}_{self.EST_time}.json'
            data = self.check_file_exists(file_name)  
            if data is None:
                data = self.query_API('json', params)
                self.save_to_file(data, file_name) 

            # Time Series Key may be Daily, Weekly or Monthly. This function selects the relevant periodicity based on 
            # previous query data and use it to populate dictionary with all time series
            time_series_key = [key for key in data.keys() if "Time Series" in key][0] 
            if time_series_key:
                time_series[item] = data[time_series_key]

        # data processing
        # transform the response data into a dictionary with keys=symbols and value=time-series in dataframe format
        # Iterate over each stock symbol
        for symbol, data in time_series.items():
            df = pd.DataFrame.from_dict(data, orient="index")
            df.rename(columns=lambda x: x.split(".")[1].strip(), inplace=True) 
            df.index = pd.to_datetime(df.index).date
            df.index.name = "date"
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric, errors='coerce')
            self.top_n_components_df[symbol] = df

        # obtain first and last series dates to perform next query; dates' order must be reversed. Assumes all series have equal dates 
        self.first_date = df.index[-1].strftime("%Y-%m-%d")
        self.last_date = df.index[0].strftime("%Y-%m-%d")
        # retains the periodicity used in this query so it is used consistently on next query
        self.periodicity = params["function"][12:]


    def get_statistical_data(self):
        '''get statistical data of the top ETF components'''
        # set API parameters for historical prices
        n2 = c.N2
        file_name = f'static/{self.ETF_symbol}_stats_{self.EST_time}.json'
        data = self.check_file_exists(file_name)  # check if there is an updated file in place
        if data is None:
            symbols_list = self.fetch_list[:n2] 
            symbol_query_param = ','.join(symbols_list)
            calculation_param = self.calculations # free query allows 3 studies only
            range_param = [self.first_date, self.last_date]
            params = c.STATS_QUERY_PARAMS
            params["function"] = "ANALYTICS_FIXED_WINDOW"
            params["SYMBOLS"] = symbol_query_param
            params["RANGE"] = range_param
            params["OHLC"] = "close"
            params["INTERVAL"] = self.periodicity
            params["CALCULATIONS"] = calculation_param
            params["apikey"] = alphavantage_key

            data = self.query_API('json', params)
            self.save_to_file(data, file_name)  

        # data processing
        lowercase_calculations = [calculation.lower() for calculation in self.calculations]
        lowercase_data = {key.lower(): value for (key, value) in data["payload"]["RETURNS_CALCULATIONS"].items()}

        for study in lowercase_calculations:
            if study in lowercase_data.keys():
                self.studies_data[study] = lowercase_data[study]
            else:
                self.studies_data[study] = None


    def generate_charts(self):
        '''generate descriptive statistical charts and tables'''
        # 1 - clean up lists
        self.study_histograms = []
        self.study_metrics = []
        self.study_matrices = []

        # 2 - ETF sector pie chart
        if len(self.weights) == 0:
            file_name = "static/not_available.jpg"
        else:
            file_name = f'static/{self.ETF_symbol}_sector_weights_{self.EST_time}.png'
            plt.pie(self.weights, labels=self.sectors)
            plt.title(f'{self.ETF_symbol} sector distribution')
            plt.savefig(file_name)
            plt.close()
            self.pie_chart = file_name

        # 3 - performance chart normalizing prices for direct comparison
        self.normalized_chart = self.plot_multiple_stocks(self.top_n_components_df, self.ETF_symbol, self.EST_time)

        # 4 - ETF and its top individual components candle charts
        for symbol, df in self.top_n_components_df.items():
            file_name = f'static/{symbol}_{self.periodicity}_candlestick_{self.EST_time}.png'
            df.index = pd.to_datetime(df.index)
            mpf.plot(df, type='candle', title=f'Candlestick Chart for {symbol}', ylabel='Price', style='yahoo', datetime_format='%Y-%m-%d', savefig=file_name)
            if symbol == self.ETF_symbol:
                self.ETF_candle = file_name
            else:
                self.candle_charts.append(file_name)

        # 5 - ETF and main components statistical analysis
        for study, data in self.studies_data.items():
            # Create histograms for each stock index
            if study == "histogram":
                for (symbol, hist_data) in data.items():
                    fig, ax = plt.subplots(figsize=(6, 4))
                    # Plot histogram
                    ax.bar(hist_data["bin_edges"][:-1], hist_data["bin_count"], width=0.05, edgecolor='black', alpha=0.7)
                    ax.set_title(f"Histogram of {symbol} Returns")
                    ax.set_xlabel("Returns")
                    ax.set_ylabel("Frequency")
                    file_name = f'static/{symbol}_{self.periodicity}_histogram.png'
                    fig.savefig(file_name)
                    plt.tight_layout()
                    self.study_histograms.append(file_name)
            elif study in ["min", "max", "mean", "median", "cumulative_return", "variance", "variance(annualized=true)", "stddev", "max_drawdown", "autocorrelation"]:
                df = pd.DataFrame.from_dict(data, orient='index', columns=[study])
                df[study] = pd.to_numeric(df[study], errors='coerce')
                df[study] = df[study].apply(lambda x: f"{x:.4%}")
                tuple = (study, df)
                self.study_metrics.append(tuple)
            elif study in ["covariance", "covariance(annualized=true)", "correlation", "correlation(method=kendall)", "correlation(method=spearman)"]:
                symbols = data["index"]
                for key in data.keys():
                    if key in study:
                        df = pd.DataFrame(data[key], index=symbols, columns=symbols)
                tuple = (study, df)
                df.fillna(0.0000, inplace=True)
                self.study_matrices.append(tuple)







    
    