# API free historical prices is non-adjusted
# the numbers below allow for 2 free queries per day
# App variable setup:
N1 = 11 # number of ETF components ranked by weight that should be charted - arbitrary but subject to API subscription limits 
N2 = 5 # number of stock symbols allowed per statistical query - 5 symbols maximum allowed in the free subscription
N3 = 3 # API maximum number of studies per query = 3
N4 = "compact" # API historical price data defaults setup = "compact" (100 names). "full" returns 20 years history
N5 = 25 # API free-query limits = 25 per day

HOLIDAYS = {
    "2025-01-01",  # New Year's Day
    "2025-07-04",  # Independence Day
    "2025-12-25",  # Christmas Day
}

TIME_SERIES_QUERIES = ["TIME_SERIES_DAILY", 
                       "TIME_SERIES_WEEKLY", 
                       "TIME_SERIES_MONTHLY"]

TIME_SERIES_PARAMS = {
    "function": None,
    "symbol": None,
    "outputsize": "full",
    "datatype": None,
    "apikey": None
}

STATS_QUERY_PARAMS = {
    "function": "ANALYTICS_FIXED_WINDOW",
    "SYMBOLS": None,
    "RANGE": None,
    "OHLC": None,
    "INTERVAL": None,
    "CALCULATIONS": None,
    "apikey": None,
}

CALCULATIONS_OPTIONS = [
    "MIN", 
    "MAX", 
    "MEAN", 
    "MEDIAN", 
    "CUMULATIVE_RETURN", 
    "VARIANCE", 
    "VARIANCE(annualized=True)",
    "STDDEV",
    "MAX_DRAWDOWN",
    "HISTOGRAM",
    "AUTOCORRELATION",
    "COVARIANCE",
    "CORRELATION",
    "CORRELATION(method=KENDALL)",
    "CORRELATION(method=SPEARMAN)",
]

ETF_QUERY_PARAMS = {
    "function": "ETF_PROFILE",
    "symbol": None,
    "apikey": None,
}

LISTED_SECURITIES_PARAMS = {
    "function": "LISTING_STATUS",
    "date": None,
    "state": "active",
    "apikey": None
}