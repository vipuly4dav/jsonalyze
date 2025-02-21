import streamlit as st
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Title
st.title("JSON Counter")

# Uploading the file
st.header("Upload JSON File")
st.file_uploader("", key="json_input")
json_input = st.session_state.get("json_input", None)

st.divider()

# Preprocessing
if json_input:
    json_file = json.load(json_input)

# Clubbed properties
    c = pd.json_normalize(json_file,sep=',').T \
        .reset_index(names="property")
    
# Split the properties into different columns
    d = c['property'].str.split(',',expand=True).rename(columns=lambda x: "Level " + str(x+1))
    d['Value'] = c[0]

    no_of_cols = len(d.columns)
    
# Start of analysis section
    st.header("Analysis")

# Global options
    col1, col2, col3 = st.columns(3)
    with col3:
            st.toggle("Remove empty columns",value=True,key="remove_empty_cols")
        
    
# Display the filters common to all tabs
    st.multiselect("Show columns",d.columns,d.columns,key="keep_columns")
        
    st.multiselect("Filter on :",d.columns,key="filter_columns")

    col1, col2 = st.columns([0.05,0.95])
    for column in st.session_state.get("filter_columns",[]):
        with col2:
            st.multiselect(f"{column} filter",d[column].unique(),key=f"{column} filter")

    def do_reset_filters():
        if set(st.session_state['keep_columns']) != set(d.columns):
            st.session_state['keep_columns'] = d.columns

        st.session_state['filter_columns'] = []

    st.button("Reset",key="reset_keep_columns",on_click=do_reset_filters)

# Process the filters 
    table_view = d 

    remove_empty_cols = st.session_state.get('remove_empty_cols',True)
    if remove_empty_cols:
        table_view = table_view.dropna(axis=1,how='all')

    for column in table_view.columns:
        if column not in st.session_state.get("keep_columns",[]):
            table_view = table_view.drop(column,axis=1)
        else:
            filter_value = st.session_state.get(f"{column} filter",[])
            if filter_value:
                table_view = table_view[table_view[column].isin(filter_value)]

# Display tabs
    tab_raw, tab_plot = st.tabs(["Raw","Plot"])

# Content in Raw tab
    with tab_raw:
        st.dataframe(table_view,use_container_width=True)

# Content in Plot tab
    # Level of detail selection
    with tab_plot:
        st.selectbox("Level of detail",st.session_state['keep_columns'],key="lod")

    # Top N elements selection
        st.number_input('Select top N elements to display',
                        min_value=1,
                        value=10,
                        key='topn')

    # Process data in plot view
    plot_view = table_view.copy()
    for column in plot_view.columns:
        if "Level" in column:
            i = int(column.split(" ")[1]) - 1
            
            if f"Level {i}" in plot_view.columns:
                plot_view[column].fillna("",inplace=True)
                plot_view[column] = plot_view[f"Level {i}"] + "." + plot_view[column] # change something here 
                
    lod = st.session_state.get("lod",None)
    with tab_plot:
        if lod:
            plot_data = plot_view.groupby(lod,dropna=False).size().reset_index(name="Count")
            st.bar_chart(plot_data,y="Count",x=lod,horizontal=True)

    # Display table
    # show_freq = st.session_state.get('show_freq',False)
    # if show_freq:
    #     st.dataframe(table_view.value_counts(dropna=False),use_container_width=True)
    # else:
    #     st.dataframe(table_view,use_container_width=True)

