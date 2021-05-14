import pandas as pd
import numpy as np
import datetime
from sodapy import Socrata
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from urllib.request import urlopen
import json
import os
#sns.set(color_codes=True)

#!/usr/bin/env python

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
client = Socrata("data.cityofnewyork.us", None)

# Example authenticated client (needed for non-public datasets):
client = Socrata("data.cityofnewyork.us",
                 "Hi16i3SK4y2UNiONqpKz4IROh",
                 username="mtcarlos98@gmail.com",
                 password="Azeroth98",
                 timeout=12000)

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("gkne-dk5s", limit=8000000)

# Convert to pandas DataFrame
df = pd.DataFrame.from_records(results)

## Data types processing
df["tpep_pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], format="%Y-%m-%dT%H:%M:%S.%f")
df["tpep_dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], format="%Y-%m-%dT%H:%M:%S.%f")
df["hour"] = df["tpep_dropoff_datetime"].dt.hour

df["passenger_count"] = df["passenger_count"].astype("int32")
df["trip_distance"] = df["trip_distance"].astype("float32")
df["total_amount"] = df["total_amount"].astype("float32")

# Drop data that does not belong to the correct year
df["tpep_pickup_datetime"] = df["tpep_pickup_datetime"].apply(lambda x: x.replace(year=2014))
df["tpep_dropoff_datetime"] = df["tpep_dropoff_datetime"].apply(lambda x: x.replace(year=2014))

## Drop possible negative prices values
df = df[df["total_amount"]>0]
df.loc[:,"mileprice_ratio"] = df["trip_distance"]/df["total_amount"]

## Drop impossible mileprice_ratio values
df = df.drop( df[df["mileprice_ratio"]>0.4].index  )

## Manhattan visualization
df["pickup_latitude"] = df["pickup_latitude"].astype("float")
#df["dropoff_latitude"] = df["dropoff_latitude"].astype("float")
df["pickup_longitude"] = df["pickup_longitude"].astype("float")
#df["dropoff_longitude"] = df["dropoff_longitude"].astype("float")

## By rounding the coordinates we can stack points via groupby and create a continous color heatmap
df["pickup_latitude_round"] = df["pickup_latitude"].round(4)
#df["dropoff_latitude_round"] = df["dropoff_latitude"].round(4)
df["pickup_longitude_round"] = df["pickup_longitude"].round(4)
#df["dropoff_longitude_round"] = df["dropoff_longitude"].round(4)

# With pickups/dropoffs
df_vis = df.groupby(["pickup_latitude_round", "pickup_longitude_round"], as_index=False).count()[["pickup_latitude_round", "pickup_longitude_round", "vendor_id"]]
df_vis.columns = ["pickup_latitude", "pickup_longitude", "counts"]
# Drop coordinate outliers
df_vis = df_vis[(df_vis["pickup_latitude"]<45) & (df_vis["pickup_latitude"]>40.5)]
df_vis = df_vis[(df_vis["pickup_longitude"]<-73.25) & (df_vis["pickup_longitude"]>-80)]

## plots generation
if not os.path.exists("images_taxi_pickups"):
    os.mkdir("images_taxi_pickups")

print("Generating general plot\n")
fig = go.Figure(data=go.Scatter(
    x=df_vis["pickup_longitude"],
    y=df_vis["pickup_latitude"],
    mode='markers',
    marker=dict(size=0.5,
                color=np.log(df_vis["counts"]),
                colorscale="Blues")
))

fig.update_layout({'plot_bgcolor':'black', 'xaxis': {
    'showgrid': False,
    'zeroline': False,
    'visible': False,
    'range':[-74.076,-73.7413]
},
'yaxis': {
    'showgrid': False,
    'zeroline': False,
    'visible': False,
    'range': [40.6041, 40.8959]
}})
fig.update_layout(height=1500, width=1500, yaxis_title="Daily pickups")
#fig.show()

fig.write_image("images_taxi_pickups/all.png")


