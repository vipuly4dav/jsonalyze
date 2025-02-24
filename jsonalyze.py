import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Title
st.title("jsonalyzer")

# Uploading the file
st.header("Upload JSON File")

st.file_uploader("", key="json_input")
json_input = st.session_state.get("json_input", None)
json_file = None
if json_input is None:
    st.pills('or load a dummy file..',options=[i for i in range(1,5)],key='chosen_example')
    if 'chosen_example' in st.session_state.keys() and st.session_state['chosen_example'] is not None:
        example_file_name = 'example' + str(st.session_state['chosen_example']) + ".json"
        with open(example_file_name,'r') as json_input:
            json_file = json.load(json_input)
else:
    json_file = json.load(json_input)

st.divider()

# Preprocessing
if json_file is not None:

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
    col1, col2, col3 = st.columns([0.4,0.45,0.15])
    with col1:
        st.toggle("Remove empty columns",value=True,key="remove_empty_cols")
    
    def do_reset_filters():
        if 'keep_columns' in st.session_state.keys():
            del st.session_state['keep_columns']
            st.session_state['keep_columns'] = d.columns.to_list()
        if 'filter_columns' in st.session_state.keys():
            del st.session_state['filter_columns']
            st.session_state['filter_columns'] = []
    
    # Reset button
    with col3:
        st.button("Reset",key="reset_keep_columns",on_click=do_reset_filters)        
    
# Display the filters common to all tabs
    st.multiselect("Show columns",options=d.columns,default=d.columns,key="keep_columns")
        
    st.multiselect("Filter on :",st.session_state['keep_columns'],key="filter_columns")

    col1, col2 = st.columns([0.2,0.8])
    for column in st.session_state.get("filter_columns",[]):
        with col1:
            st.selectbox("",options=["exclude","include"],key=f"{column}_filter_type")
        with col2:
            st.multiselect(f"{column} filter",d[column].unique(),key=f"{column}_filter_value")

# Process the filters 

    def process_filter(p_view):
        for column in p_view.columns:
            if column not in st.session_state.get("keep_columns",[]):
                p_view = p_view.drop(column,axis=1)
            else:
                filter_columns = st.session_state.get("filter_columns")
                filter_type = st.session_state.get(f"{column}_filter_type")
                filter_value = st.session_state.get(f"{column}_filter_value",[])
                if column in filter_columns:
                    if filter_type == "exclude":
                        p_view = p_view[~p_view[column].isin(filter_value)]
                    else:
                        p_view = p_view[p_view[column].isin(filter_value)]

        remove_empty_cols = st.session_state.get('remove_empty_cols',True)
        if remove_empty_cols:
            p_view = p_view.dropna(axis=1,how='all')

        return p_view

    table_view = process_filter(d)

# Display tabs
    tab_raw, tab_agg = st.tabs(["Raw","Aggregate"])

# Content in Raw tab
    with tab_raw:
        st.data_editor(table_view,use_container_width=True,key="table_view_edits")

# Content in Aggregate tab
    with tab_agg:
        # Show plot
        st.toggle('Show plot',value=False,key='show_plot')

        # Level of detail selection
        st.selectbox("Level of detail",st.session_state['keep_columns'],key="lod")

        # No of elements to display
        col1, col2 = st.columns([0.3,0.7])
        with col1:
            st.selectbox("",options=['Descending','Ascending'],key='sorting_order')
        if st.session_state['show_plot'] is True:
            with col2:
                st.select_slider("Choose number of elements to show",options=range(5,21,5),key='topn')
        
        if st.session_state['sorting_order'] == 'Ascending':
            is_ascending = True
        else:
            is_ascending = False

        # Add new column fields
        # with st.form(key='new_col_form'):
        #     col1, col2 = st.columns(2,vertical_alignment='center')  
        #     with col1:
        #         st.text_input('',key=f"new_col")
            
        #     st.form_submit_button("Add new column")    

        # Preprocessing table levels to add preceding qualifier
        _view = table_view.copy()

        def combine_rows(x):
            if x[1] is not None:
                return x[0] + "." + x[1]
            else:
                return x[0]

        for column in _view.columns:
            if "Level" in column:
                prev_level = int(column.split(" ")[1]) - 1
                while (prev_level > 0):
                    if f"Level {prev_level}" in _view.columns:
                        _view[column] = _view[[f"Level {prev_level}",column]].apply(combine_rows,axis=1)
                        break
                    else:
                        prev_level -= 1

        agg_view = _view.groupby(st.session_state["lod"]).size().rename('Count').sort_values(ascending=is_ascending)

        # if not st.session_state['new_col'] != '':
        #     st.write('something is done')
        #     agg_view = pd.concat([agg_view,pd.Series(name=st.session_state['new_col'])],axis=1)
        #     st.data_editor(agg_view, use_container_width=True,key="agg_view_edits")
        # else:
        #     st.data_editor(agg_view, use_container_width=True, key="agg_view_edits")

        if st.session_state['show_plot'] is True:
            plot_view = agg_view[:st.session_state['topn']]
            sns.set_theme(style='white',palette='pastel')
            fig, ax = plt.subplots()
            sns.barplot(y=plot_view.index,x=plot_view.values,ax=ax)
            sns.despine()
            st.pyplot(fig=fig)
        else:
            st.data_editor(agg_view,use_container_width=True, key="agg_view_edits")


