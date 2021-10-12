# import query dependencies
from enum import auto
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

#import flask dependencies
from flask import Flask,jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(engine,reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

# flask setup
app = Flask(__name__)

# List all available routes at 'home' page 
@app.route("/")
def index():
    return(
        f"Available routes:<br>"
        f"/api/v1.0/precipitation<br>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/&lt;start&gt;  <em>--->date format is yyyy-mm-dd</em><br>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;  <em>--->date format is yyyy-mm-dd</em><br>"
    )

# 'precipitation' page returns the json representation of precipitation values
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    precipitations = session.query(Measurement.date, Measurement.prcp).all()
    # Convert the query to a dictionary
    prcp_dict = {}
    for date, prcp in precipitations:
        prcp_dict[date] = prcp

    session.close()

    return jsonify(prcp_dict)


# 'stations' page returns a json list of the available stations
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    # Query all stations from Station class
    stations= session.query(Station.station).all()
    session.close()

    # Convert the query results into a list
    stations_list = list(np.ravel(stations))

    return jsonify(stations_list)


# 'tobs' page returns the dates and temperatures of the most active station for the last year of data
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    # Determine which station has the highest number of observations
    most_active_station = session.query(Measurement.station, func.count(Measurement.tobs)).group_by(Measurement.station).\
    order_by(func.count(Measurement.tobs).desc()).first()[0]

    # Determine the dates of last year
    # Query the date of the last data point
    last_point_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    # Convert last_point_date into a datetime object
    lp_date_obj = dt.datetime.strptime(last_point_date[0],'%Y-%m-%d')
    # Calculate the date 1 year ago from the last data point in the database
    one_year_ago = lp_date_obj - dt.timedelta(days=366)

    # Query last year data of the most active station
    last_year_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station==most_active_station).filter(Measurement.date>=one_year_ago).all()

    # Convert the query to a dictionary
    tobs_dict = {}
    for date, tobs in last_year_data:
        tobs_dict[date] = tobs

    session.close()

    return jsonify(tobs_dict)

# Return a list of the min, average and max temperature for the specified dates
# In case client provided a start date only
@app.route("/api/v1.0/<start>")
def range_start(start):
    session = Session(engine)
    start_date = dt.datetime.strptime(start,'%Y-%m-%d')
    temperatures = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date>=start_date).all()
    temperatures = list(np.ravel(temperatures))
    tmin = temperatures[0]
    tavg = round(temperatures[1],1)
    tmax = temperatures[2]
    session.close()

    return jsonify(tmin, tavg, tmax)

# In case client provided start/end dates
@app.route("/api/v1.0/<start>/<end>")
def range_start_end(start, end):
    session = Session(engine)
    start_date = dt.datetime.strptime(start,'%Y-%m-%d')
    end_date = dt.datetime.strptime(end,'%Y-%m-%d')
    temperatures = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter((Measurement.date>=start_date),(Measurement.date<=end_date)).all()
    temperatures = list(np.ravel(temperatures))
    tmin = temperatures[0]
    tavg = round(temperatures[1],1)
    tmax = temperatures[2]
    session.close()

    return jsonify(tmin, tavg, tmax)



if __name__ == "__main__":
    app.run(debug=True)