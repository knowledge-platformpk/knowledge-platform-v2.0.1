import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt

def get_Precp_image_roi(json_data, from_date, to_date):
    roi = ee.FeatureCollection(json_data)

    # Convert dates to ee.Date objects
    start_date = ee.Date(from_date)
    end_date = ee.Date(to_date)

    def scale_index(img):
        return img.multiply(1).copyProperties(img,['system:time_start','date','system:time_end'])
    # Filter the ERA temperature collection by date
    Precp_collection = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start_date, end_date).select('precipitation').map(scale_index)

    # Calculate the mean temperature image
    mean_Precp_image = Precp_collection.mean().clip(roi)

    minMax = mean_Precp_image.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=roi,
        scale=30,
        bestEffort=True
    )

    area = roi.geometry(0.01).area().divide(1e6)

    try:
        # Access min and max values from the minMax dictionary
        min_image = minMax.get('precipitation_min')
        max_image = minMax.get('precipitation_max')

        st.session_state['min'] = min_image.getInfo()
        st.session_state['max'] = max_image.getInfo()
        st.session_state['area'] = area.getInfo()
    except:
        st.session_state['min'] = 0
        st.session_state['max'] = 10
        st.session_state['area'] = area.getInfo()

    return mean_Precp_image
def create_Precp_timeseries_roi(json_data, from_date, to_date):
    roi = ee.FeatureCollection(json_data)

    # Convert dates to ee.Date objects
    start_date = ee.Date(from_date)
    end_date = ee.Date(to_date)
    def scale_index(img):
        return img.multiply(1).copyProperties(img,['system:time_start','date','system:time_end'])
    # Filter the ERA temperature collection by date
    Precp_collection = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(roi).filterDate(start_date, end_date).select('precipitation').map(scale_index)

    # Create a list of dates and mean temperature values
    timeseries = Precp_collection.map(lambda image: ee.Feature(None, {
        'date': image.date().format(),
        'precipitation': image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=5566  # Adjust scale according to your data resolution
        ).get('precipitation')
    }))

    # Convert to a Pandas DataFrame
    timeseries_list = timeseries.reduceColumns(ee.Reducer.toList(2), ['date', 'precipitation']).values().get(0).getInfo()
    df = pd.DataFrame(timeseries_list, columns=['date', 'precipitation'])
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%b %Y')
    st.session_state['Precp_chart_data'] = df

    # Create a time-series plot
    fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
    df.plot(x='date', y='precipitation', ax=ax, legend=True, title='Precipitation Time Series')
    plt.xlabel('Date', fontsize=6)
    plt.ylabel('Precipitation mm/day')
    plt.grid(True)
    plt.tight_layout()

    return fig
