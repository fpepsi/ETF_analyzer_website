from flask import Flask, render_template, request, redirect, url_for, flash 
from query import query_alphavantage
import constants as c
from datetime import datetime, timedelta
import holidays
import pytz

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        analyzer.ETF_symbol = request.form.get("ETF_symbol")
        analyzer.ts_periodicity = request.form.get("params[function]")
        analyzer.calculations = request.form.getlist("params[CALCULATIONS]")
        
        # **Validation Check**
        if len(analyzer.calculations) > 3:
            flash("You must select between 1 and 3 studies in order to proceed with the analysis.", "danger")
            return redirect(url_for('index'))  

        analyzer.get_ETF_dataset()
        analyzer.get_components_prices()
        analyzer.get_statistical_data()
        analyzer.generate_charts()
        return render_template("index.html", app_variable_list=analyzer.app_variable_list,
                               ETF_symbol=analyzer.ETF_symbol, 
                               ETF_data=analyzer.ETF_data,
                               histograms_list=analyzer.study_histograms,
                               metrics_list=analyzer.study_metrics,
                               matrices_list=analyzer.study_matrices,
                               top_n_components_df=analyzer.top_n_components_df,
                               ETF_candle=analyzer.ETF_candle,
                               candle_charts=analyzer.candle_charts,
                               normalized_chart=analyzer.normalized_chart,
                               pie_chart=analyzer.pie_chart,
                               names_list=analyzer.names_list, 
                               )
    analyzer.get_AlphaV_securities()
    return render_template("index.html", app_variable_list=analyzer.app_variable_list, 
                           names_list=analyzer.names_list, 
                           time_series=c.TIME_SERIES_QUERIES, 
                           calculation_options=c.CALCULATIONS_OPTIONS)

# Get the current EST time
utc_now = datetime.now(pytz.utc)
est_timezone = pytz.timezone('US/Eastern')
est_today = utc_now.astimezone(est_timezone)

# determine if query day is a business day; if not, query last business day
query_day = est_today
bd = False
while not bd:
    if query_day.weekday() in (5,6) or query_day in holidays.country_holidays('US', years=query_day.year):
        previous_day = query_day - timedelta(1)
        query_day = previous_day
    else:
        bd = True
        query_day = query_day.strftime("%Y-%m-%d")
        
# creates query object
analyzer = query_alphavantage(query_day)
if __name__ == '__main__':
    app.run(debug=True)
    
