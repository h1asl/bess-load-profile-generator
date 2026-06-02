import numpy as np
import pandas as pd
import scipy.io
import dask.dataframe as dd
import datetime
import os

from Track_SOC import Track_SOC

def Generate_FCR_Profile(Country, Region, Year= 2024, Sim_StartDay_index=1 , Sim_EndDay_index=2,FCR_Cap=1 ,power_cap=1,init_SOC=50, target_SOC=50, upper_SOC_limit = 100, lower_SOC_limit = 0):

    if Sim_StartDay_index > Sim_EndDay_index:
        Sim_EndDay_index = Sim_StartDay_index

 #-----------------------------------------------------------------------------------------------------------------------------------------------

    from paths import grid_frequency_path

    Freq_path = grid_frequency_path(Country, Region, Year)
    if Country == "US":
        mat_key = f"f_{Region}_{Year}"
    else:
        mat_key = f"f_{Country}_{Year}"
    Frequancy_Profile = scipy.io.loadmat(Freq_path)
    Frequancy_Profile = pd.DataFrame(Frequancy_Profile[mat_key])
    
 #-----------------------------------------------------------------------------------------------------------------------------------------------

    if len(Frequancy_Profile) < (Sim_EndDay_index-Sim_StartDay_index+1)*24*3600:
        raise ValueError("Duration of Imported Grid Frequancy Data is less than requested Simulation Interval. Please Adjust Sim_StartDay_index and/or Sim_EndDay_index")

    start_time = pd.Timestamp(f'{Year}-01-01 00:00:00')
    Frequancy_Profile['Timestamp'] = start_time + pd.to_timedelta(Frequancy_Profile.index, unit='s')

    # Extract the day of the year
    Frequancy_Profile['DayOfYear'] = Frequancy_Profile['Timestamp'].dt.dayofyear 

    # Filter rows based on the day of the year
    Frequancy_Profile = Frequancy_Profile[(Frequancy_Profile['DayOfYear'] >= Sim_StartDay_index) & (Frequancy_Profile['DayOfYear'] <= Sim_EndDay_index)]
    Frequancy_Profile = Frequancy_Profile.drop(columns=['Timestamp', 'DayOfYear'])
    Frequancy_Profile = Frequancy_Profile.reset_index(drop=True)
    Frequancy_Profile = dd.from_pandas(Frequancy_Profile, npartitions=4) 

 #-----------------------------------------------------------------------------------------------------------------------------------------------
    
    if Country == "GER":
        Nominal_Frequancy = 50
        Deadband_Limit = 0.01
        FreqMax = 0.2
    elif Country == "GB":
        Nominal_Frequancy = 50
        Deadband_Limit = 0.015
        FreqMax = 0.5
    elif Country == "US":
        Nominal_Frequancy = 60
        Deadband_Limit = 0.017
        FreqMax = 0.5

    Freq_Deviation = Frequancy_Profile - Nominal_Frequancy
    #print(Freq_Deviation.head())

    #-----------------------------------------------------------------------------------------------------------------------------------------------

    # Define a function to apply the conditions to each row
    def compute_power(freq_deviation, deadband_limit, freq_max):
        if -deadband_limit <= freq_deviation <= deadband_limit:
            return 0
        elif deadband_limit < freq_deviation <= freq_max:
            return -1 * ( (freq_deviation - deadband_limit) / abs(freq_max - deadband_limit) )
        elif -freq_max <= freq_deviation < -deadband_limit:
            return -1 * ( (freq_deviation + deadband_limit) / abs(freq_max - deadband_limit) )
        elif freq_deviation > freq_max:
            return -1 
        elif freq_deviation < -freq_max:
            return 1 

    # Apply the function to each element in the 'Freq_Deviation' column
    B_Power = Freq_Deviation[0].map_partitions(lambda df: df.apply(compute_power, args=(Deadband_Limit, FreqMax)))

    # Trigger computation and bring it to memory as a pandas DataFrame if needed
    B_Power = B_Power.compute()
  
    #-----------------------------------------------------------------------------------------------------------------------------------------------

    Power_Profile = B_Power * power_cap
    Power_Profile_df = pd.DataFrame({'Power': Power_Profile})
    Power_Profile_df.index = range(0, len(Power_Profile))

    num_rows = len(Power_Profile_df)
    date = datetime.datetime(Year, 1, 1) + datetime.timedelta(days=Sim_StartDay_index-1)
    Power_Profile_df['Timestamp'] = pd.date_range(start=f'{Year}-{date.month}-{date.day} 00:00', periods=num_rows, freq='s')
    Power_Profile_df.set_index('Timestamp', inplace=True)

    #------------------------------------------------------------------------------------------------------------------------------------------------

    Power_Profile_df['Power'], SOC_new = Track_SOC(Power_Profile_df['Power'], init_SOC, FCR_Cap, target_SOC, upper_SOC_limit, lower_SOC_limit)

    return Power_Profile_df

    
