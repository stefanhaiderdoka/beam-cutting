import streamlit as st
import pandas as pd
import functions as functions
from streamlit import caching
#from streamlit.scriptrunner import RerunException

@st.cache(allow_output_mutation=True)
def get_data():
    return []
    

def main():
    
    st.sidebar.image('doka_logo_web.jpg')

    st.sidebar.header(
        "Prototype"
    )
    
    st.sidebar.subheader(
        "Raw Beam Optimisation"
    )
    
    if st.sidebar.button('Restart'):
        
        caching.clear_cache()
        st.experimental_rerun()
        #raise RerunException

    if len(get_data()) < 4:

        st.subheader('Type in your Customer Demand')

        length = st.number_input("Beam Length (m)")
        demand = st.number_input("Demand in Pieces")

        if st.button("Add row"):

            get_data().append({"length": length, "open_qty": demand})
        
    else:
        
        st.subheader('For Test-purposes input lengths are limited to max. 4 different lengths')
        st.text('You can delete the current Customer Demand by clicking Restart in the Sidebar')
        
    cust_dem = pd.DataFrame(get_data())

    if cust_dem.empty == False:

        st.subheader('Customer Demand')
        cust_dem = pd.DataFrame(get_data())

        st.write(cust_dem)
        
        if st.button("Start Processing"):

            production_orders = pd.DataFrame()
            remaining_demand = pd.DataFrame()

            while cust_dem.empty == False:
                
                print(len(cust_dem.index))
                
                cust_dem = cust_dem.dropna().reset_index(drop=True)
                
                dem, prd = functions.create_prd_orders(cust_dem)

                production_orders = production_orders.append(prd)
                
                try:
                    remaining_demand = remaining_demand.append(dem.sort_values(by=['open_qty'], ascending=True).reset_index(drop = True).iloc[0])
                    
                    cust_dem = dem.sort_values(by=['open_qty'], ascending=True).reset_index(drop = True).drop(0)
                    
                except Exception as e:
                    cust_dem = dem
                    print('demand solved')
                    #print(len(dem.index))
                    remaining_demand = pd.DataFrame()
                    
            st.subheader('Production Orders')
            st.write(production_orders)
            
            st.subheader('Remaining Demand')
            
            if remaining_demand.empty == False:
                st.write(remaining_demand) 
                
            else:
                st.text('No remaining demand')


main()

