from optimizer import optimizer
import numpy as np
import pandas as pd
import datetime
import os


def Generate_WSM_Profile(Country=None ,Region=None, Zone=None ,Year=2024 , Sim_StartDay_index=1 , Sim_EndDay_index=1 , BESS_cap=None , power_cap=1 , DA_Cap=None , DA_Cycles=1 , ID_Cap=None , ID_Cycles=1 , IDc_Cap=None , IDc_Cycles=1 , Solver_Path=None):
    
    if Country == "US" and Region == "ERCOT" and Zone is None:
        Zone = "HOUSTON"
    if Country == "US" and Region == "CAISO" and Zone is None:
        Zone = "VEA"

    #-------------------------------------------------------------------------------------------------

    if Solver_Path is None:
        raise ValueError("Solver Path isn't passed")
    
    #-------------------------------------------------------------------------------------------------
    
    if Sim_StartDay_index > Sim_EndDay_index:
        Sim_EndDay_index = Sim_StartDay_index

    #-------------------------------------------------------------------------------------------------
    
    if DA_Cap is not None and ID_Cap is None and IDc_Cap is None:
        ID_Cap = IDc_Cap = 0
    
    elif ID_Cap is not None and DA_Cap is None and IDc_Cap is None:
        DA_Cap = IDc_Cap = 0
    
    elif IDc_Cap is not None and DA_Cap is None and ID_Cap is None:
        DA_Cap = ID_Cap = 0
    
    elif DA_Cap is not None and ID_Cap is not None and IDc_Cap is None:
        IDc_Cap = 0
    
    elif DA_Cap is None and ID_Cap is None and IDc_Cap is None:
        DA_Cap = ID_Cap = IDc_Cap = 1

    # Define the whole BESS Capacity 
    
    if BESS_cap is None:
        BESS_cap = max(DA_Cap,ID_Cap,IDc_Cap)
    elif BESS_cap < max(DA_Cap,ID_Cap,IDc_Cap):
        raise ValueError("BESS_cap can't be smaller than the maximum between (DA_Cap,ID_Cap,IDc_Cap)")

    from paths import market_prices_path

    prices_path = market_prices_path(Country, Region)

    
    QuartersInDay = 96

    if DA_Cap > 0:
        DayAhead = pd.read_excel(prices_path, sheet_name='Dayahead')

        if DayAhead.empty == True:
            raise ValueError ("The Excel sheet 'Dayahead' is empty.")
        
        if Country =="US":
            if f'LZ_{Zone} Dayahead-{Year}' not in DayAhead.columns:
                raise ValueError (f'LZ_{Zone} Dayahead-{Year} Does not exist in Dayahead Sheet')
            Daa = np.array(DayAhead[f'LZ_{Zone} Dayahead-{Year}'])
        else:
            if f'Dayahead-{Year}' not in DayAhead.columns:
                raise ValueError (f'Dayahead-{Year} Does not exist in Dayahead Sheet')
            Daa = np.array(DayAhead[f'Dayahead-{Year}'])
        size_DA = len(Daa)
        
        
    if ID_Cap > 0:
        if Country == "US":
            Intraday = pd.read_excel(prices_path, sheet_name='Realtime')

            if Intraday.empty == True:
                raise ValueError ("The Excel sheet 'Realtime' is empty.")
            if f'LZ_{Zone} Realtime-{Year}' not in Intraday.columns:
                raise ValueError (f'LZ_{Zone} Realtime-{Year} Does not exist in Realtime Sheet')
            Ida = np.array(Intraday[f'LZ_{Zone} Realtime-{Year}'])
            size_ID = len(Ida)
        else:
            Intraday = pd.read_excel(prices_path, sheet_name='Intraday')

            if Intraday.empty == True:
                raise ValueError ("The Excel sheet 'Intraday' is empty.")
            if f'Intraday-{Year}' not in Intraday.columns:
                raise ValueError (f'Intraday-{Year} Does not exist in Intraday Sheet')
            Ida = np.array(Intraday[f'Intraday-{Year}'])
            size_ID = len(Ida)
        
    
    if Country == "US":
        IDc_Cap = 0

    if IDc_Cap > 0:
        Intraday_Cont = pd.read_excel(prices_path, sheet_name='Intraday Cont')

        if Intraday_Cont.empty == True:
            raise ValueError ("The Excel sheet 'Intraday Cont' is empty.")
        if f'Intraday Cont-{Year}' not in Intraday_Cont.columns:
            raise ValueError (f'Intraday Cont-{Year} Does not exist in Intraday Cont Sheet')
        Idc = np.array(Intraday_Cont[f'Intraday Cont-{Year}'])
        size_IDc = len(Idc)

    #-------------------------------------------------------------------------------------------------
        
    #Check if Dayahead, Intraday & Intraday Cont. Data are equal in size

    if DA_Cap > 0 and ID_Cap > 0 and IDc_Cap == 0:
        if size_DA*4 != size_ID:
            raise ValueError("Number of Days of Dayahead data and Intrayday data must match")

    if DA_Cap > 0 and ID_Cap > 0 and IDc_Cap > 0:
        if size_DA*4 != size_ID or size_DA*4 != size_IDc :
            raise ValueError("Number of Days of Dayahead data, Intrayday data and Intraday Cont. data must match")

     #-------------------------------------------------------------------------------------------------

    if ID_Cap == 0 and IDc_Cap == 0:
        daa_price_vector = Daa.tolist()
        daa_price_vector = [item for item in daa_price_vector for _ in range(4)]
        ida_price_vector = [0] * size_DA * 4
        idc_price_vector = [0] * size_DA * 4

    elif DA_Cap == 0 and IDc_Cap == 0:
        daa_price_vector = [0] * size_ID
        ida_price_vector = Ida.tolist()
        idc_price_vector = [0] * size_ID

    elif DA_Cap == 0 and ID_Cap == 0:
        daa_price_vector = [0] * size_IDc
        ida_price_vector = [0] * size_IDc
        idc_price_vector = Idc.tolist()
    
    elif IDc_Cap == 0 :
        daa_price_vector = Daa.tolist()
        daa_price_vector = [item for item in daa_price_vector for _ in range(4)]
        ida_price_vector = Ida.tolist()
        idc_price_vector = [0] * size_ID
    
    elif DA_Cap is not None and ID_Cap is not None and IDc_Cap is not None:
        daa_price_vector = Daa.tolist()
        daa_price_vector = [item for item in daa_price_vector for _ in range(4)]
        ida_price_vector = Ida.tolist()
        idc_price_vector = Idc.tolist()

    elif DA_Cap is None and ID_Cap is None and IDc_Cap is None:
        daa_price_vector = Daa.tolist()
        daa_price_vector = [item for item in daa_price_vector for _ in range(4)]
        ida_price_vector = Ida.tolist()
        idc_price_vector = Idc.tolist()


    #-------------------------------------------------------------------------------------------------
    # Form Prices DataFrame

    Prices_df = pd.DataFrame({
        'Dayahead': np.asarray(daa_price_vector) if DA_Cap > 0 else None,
        'Intraday': Ida if ID_Cap > 0 else None,
        'Intraday_Cont': Idc if IDc_Cap > 0 else None
        }).dropna()
    
    num_rows = len(Prices_df)
    Prices_df['Timestamp'] = pd.date_range(start=f'{Year}-01-01 00:00', periods=num_rows, freq='15min')
    Prices_df.set_index('Timestamp', inplace=True)
    

    #-------------------------------------------------------------------------------------------------
    
    #Running Squential Optimization for selected Markets

    optimize_wholesale = optimizer(solverpath_exe = Solver_Path)

    step1_soc_daa_total = [] 
    step1_cha_daa_total = [] 
    step1_dis_daa_total = [] 
    step1_profit_daa_total = 0 

    step2_soc_ida_total = []
    step2_cha_ida_total = []
    step2_dis_ida_total = []
    step2_cha_daida_total = []
    step2_dis_daida_total = []
    step2_profit_ida_total = 0

    step3_soc_idc_total = []
    step3_cha_idc_total = []
    step3_dis_idc_total = []
    step3_cha_daididc_total = []
    step3_dis_daididc_total = []
    step3_profit_idc_total = 0


    for i in range(QuartersInDay*(Sim_StartDay_index-1) ,QuartersInDay*Sim_EndDay_index, QuartersInDay):

        #Step 1: Dayahead Optimization
        
        daa_price_vector_Day = daa_price_vector[i:i + QuartersInDay]
        step1_soc_daa,step1_cha_daa,step1_dis_daa, step1_profit_daa = optimize_wholesale.step1_optimize_daa(n_cycles=DA_Cycles, energy_cap=DA_Cap, power_cap=power_cap, daa_price_vector=daa_price_vector_Day)
        step1_soc_daa_total = step1_soc_daa_total + step1_soc_daa

        step1_cha_daa_total = step1_cha_daa_total + step1_cha_daa
        step1_dis_daa_total = step1_dis_daa_total + step1_dis_daa

        step1_profit_daa_total = step1_profit_daa_total + step1_profit_daa

        #--------------------------------------------------------------------------------------------------------------

        #Step 2: Intraday Optimization

        ida_price_vector_Day = ida_price_vector[i:i + QuartersInDay]
        step2_soc_ida, step2_cha_ida, step2_dis_ida, step2_cha_ida_close, step2_dis_ida_close, step2_profit_ida, step2_cha_daaida, step2_dis_daaida = optimize_wholesale.step2_optimize_ida(n_cycles=ID_Cycles, energy_cap=ID_Cap, power_cap=power_cap, ida_price_vector=ida_price_vector_Day, step1_cha_daa=step1_cha_daa, step1_dis_daa=step1_dis_daa)
        step2_soc_ida_total = step2_soc_ida_total + step2_soc_ida

        step2_cha_ida_total = step2_cha_ida_total + step2_cha_ida
        step2_dis_ida_total = step2_dis_ida_total + step2_dis_ida

        step2_cha_daida_total = step2_cha_daida_total + [x + y for x, y in zip(step2_cha_ida, step2_cha_ida_close)]
        step2_dis_daida_total = step2_dis_daida_total + [x + y for x, y in zip(step2_dis_ida, step2_dis_ida_close)]
        step2_profit_ida_total = step2_profit_ida_total + step2_profit_ida

        #--------------------------------------------------------------------------------------------------------------

        #Step 3: Intraday Cont Optimization

        idc_price_vector_Day = idc_price_vector[i:i + QuartersInDay]
        step3_soc_idc, step3_cha_idc, step3_dis_idc, step3_cha_idc_close, step3_dis_idc_close, step3_profit_idc, step3_cha_daaidaidc, step3_dis_daaidaidc = optimize_wholesale.step3_optimize_idc(n_cycles=IDc_Cycles, energy_cap=IDc_Cap, power_cap=power_cap, idc_price_vector=idc_price_vector_Day, step2_cha_daaida=step2_cha_daaida, step2_dis_daaida=step2_dis_daaida)
        step3_soc_idc_total = step3_soc_idc_total + step3_soc_idc

        step3_cha_idc_total = step3_cha_idc_total + step3_cha_idc
        step3_dis_idc_total = step3_dis_idc_total + step3_dis_idc

        step3_cha_daididc_total = step3_cha_daididc_total + [x + y for x, y in zip(step3_cha_idc, step3_cha_idc_close)]
        step3_dis_daididc_total = step3_dis_daididc_total + [x + y for x, y in zip(step3_dis_idc, step3_dis_idc_close)]
        step3_profit_idc_total = step3_profit_idc_total + step3_profit_idc
            
        
    #---------------------------------------------------------------------------------------------------------------------

    # Revenue Calculation

    revenue_daa = np.sum( np.asarray([x - y for x, y in zip(step1_dis_daa_total, step1_cha_daa_total)]) * power_cap/4 * np.asarray(daa_price_vector[QuartersInDay*(Sim_StartDay_index-1) :QuartersInDay*Sim_EndDay_index ]) )
    revenue_ida = np.sum( np.asarray([x - y for x, y in zip(step2_dis_ida_total, step2_cha_ida_total)]) * power_cap/4 * np.asarray(ida_price_vector[QuartersInDay*(Sim_StartDay_index-1) :QuartersInDay*Sim_EndDay_index ]) )
    revenue_idc = np.sum( np.asarray([x - y for x, y in zip(step3_dis_idc_total, step3_cha_idc_total)]) * power_cap/4 * np.asarray(idc_price_vector[QuartersInDay*(Sim_StartDay_index-1) :QuartersInDay*Sim_EndDay_index ]) )
    revenue_daida = np.sum( np.asarray([x - y for x, y in zip(step2_dis_daida_total, step2_cha_daida_total)]) * power_cap/4 * np.asarray(ida_price_vector[QuartersInDay*(Sim_StartDay_index-1) :QuartersInDay*Sim_EndDay_index ]) )
    revenue_daididc = np.sum( np.asarray([x - y for x, y in zip(step3_dis_idc_total, step3_cha_daididc_total)]) * power_cap/4 * np.asarray(idc_price_vector[QuartersInDay*(Sim_StartDay_index-1) :QuartersInDay*Sim_EndDay_index ]) )

 
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------


    # Dataframes Creation: (Each Dataframe has charging/discharging Position Profile, Power Profile, SOC Profile and Revenue attribute)


    if ID_Cap == 0 and IDc_Cap == 0:
        pp_DA = np.asarray([x - y for x, y in zip( step1_cha_daa_total,step1_dis_daa_total)]) * power_cap

        Output_df = pd.DataFrame({
            'Charging_DA': np.asarray(step1_cha_daa_total)/4 * power_cap,
            'Discharging_DA': np.asarray(step1_dis_daa_total)*-1/4 * power_cap,
            'PowerProfile_DA': pp_DA,
            'PowerProfile_Resultant': pp_DA,
            'SOC': np.asarray(step1_soc_daa_total)/BESS_cap,
            })
        
        Output_df.Revenue = revenue_daa

    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    elif DA_Cap == 0 and IDc_Cap == 0:
        pp_ID = np.asarray([x - y for x, y in zip(step2_cha_ida_total,step2_dis_ida_total)]) * power_cap

        Output_df = pd.DataFrame({
            'Charging_ID': np.asarray(step2_cha_ida_total)/4 * power_cap,
            'Discharging_ID': np.asarray(step2_dis_ida_total)*-1/4 * power_cap,
            'PowerProfile_ID': pp_ID,
            'PowerProfile_Resultant': pp_ID,
            'SOC': np.asarray(step2_soc_ida_total)/BESS_cap,
            })
        
        Output_df.Revenue = revenue_ida

    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------

    elif DA_Cap == 0 and ID_Cap == 0:
        pp_IDc = np.asarray([x - y for x, y in zip(step3_cha_idc_total,step3_dis_idc_total)]) * power_cap
        Output_df = pd.DataFrame({
            'Charging_IDc': np.asarray(step3_cha_idc_total)/4 * power_cap,
            'Discharging_IDc': np.asarray(step3_dis_idc_total)*-1/4 * power_cap,
            'PowerProfile_IDc': pp_IDc,
            'PowerProfile_Resultant': pp_IDc,
            'SOC': np.asarray(step3_soc_idc_total)/BESS_cap,
            })
        
        Output_df.Revenue = revenue_idc

    #----------------------------------------------------------------------------------------------------------------------------------------------------------------- 
    
    elif IDc_Cap == 0 :
        pp_DA = np.asarray([x - y for x, y in zip( step1_cha_daa_total,step1_dis_daa_total)]) * power_cap
        pp_ID = np.asarray([x - y for x, y in zip(step2_cha_daida_total,step2_dis_daida_total)]) * power_cap

        Output_df = pd.DataFrame({
            'Charging_DA': np.asarray(step1_cha_daa_total)/4 * power_cap,
            'Discharging_DA': np.asarray(step1_dis_daa_total)*-1/4 * power_cap,
            'Charging_ID': np.asarray(step2_cha_daida_total)/4 * power_cap,
            'Discharging_ID': np.asarray(step2_dis_daida_total)*-1/4 * power_cap,


            'PowerProfile_DA': pp_DA,
            'PowerProfile_ID': pp_ID,
            'PowerProfile_Resultant': [x + y for x, y in zip(pp_DA,pp_ID)],

            'SOC': np.asarray(step2_soc_ida_total)/BESS_cap,
            })
        
        Output_df.Revenue = revenue_daa + revenue_daida
    
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    elif DA_Cap is not None and ID_Cap is not None and IDc_Cap is not None:
        pp_DA = np.asarray([x - y for x, y in zip( step1_cha_daa_total,step1_dis_daa_total)]) * power_cap
        pp_ID = np.asarray([x - y for x, y in zip( step2_cha_daida_total,step2_dis_daida_total)]) * power_cap
        pp_IDc = np.asarray([x - y for x, y in zip( step3_cha_daididc_total,step3_dis_daididc_total)]) * power_cap

        Output_df = pd.DataFrame({
            'Charging_DA': np.asarray(step1_cha_daa_total)/4 * power_cap,
            'Discharging_DA': np.asarray(step1_dis_daa_total)*-1/4 * power_cap,
            'Charging_ID': np.asarray(step2_cha_daida_total)/4 * power_cap,
            'Discharging_ID': np.asarray(step2_dis_daida_total)*-1/4 * power_cap,
            'Charging_IDc': np.asarray(step3_cha_daididc_total)/4 * power_cap,
            'Discharging_IDc': np.asarray(step3_dis_daididc_total)*-1/4 * power_cap,


            'PowerProfile_DA': pp_DA,
            'PowerProfile_ID': pp_ID,
            'PowerProfile_IDc': pp_IDc,
            'PowerProfile_Resultant': [x + y + z for x, y, z in zip(pp_DA,pp_ID,pp_IDc)],

            'SOC': np.asarray(step3_soc_idc_total)/BESS_cap,
            })
        
        Output_df.Revenue = revenue_daa + revenue_daida + revenue_daididc

    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    elif DA_Cap is None and ID_Cap is None and IDc_Cap is None:
        pp_DA = np.asarray([x - y for x, y in zip( step1_cha_daa_total,step1_dis_daa_total)]) * power_cap
        pp_ID = np.asarray([x - y for x, y in zip( step2_cha_daida_total,step2_dis_daida_total)]) * power_cap
        pp_IDc = np.asarray([x - y for x, y in zip( step3_cha_daididc_total,step3_dis_daididc_total)]) * power_cap

        Output_df = pd.DataFrame({
            'Charging_DA': np.asarray(step1_cha_daa_total)/4 * power_cap,
            'Discharging_DA': np.asarray(step1_dis_daa_total)*-1/4 * power_cap,
            'Charging_ID': np.asarray(step2_cha_daida_total)/4 * power_cap,
            'Discharging_ID': np.asarray(step2_dis_daida_total)*-1/4 * power_cap,
            'Charging_IDc': np.asarray(step3_cha_daididc_total)/4 * power_cap,
            'Discharging_IDc': np.asarray(step3_dis_daididc_total)*-1/4 * power_cap,


            'PowerProfile_DA': pp_DA,
            'PowerProfile_ID': pp_ID,
            'PowerProfile_IDc': pp_IDc,
            'PowerProfile_Resultant': [x + y + z for x, y, z in zip(pp_DA,pp_ID,pp_IDc)],

            'SOC': np.asarray(step3_soc_idc_total)/BESS_cap,
            })
        
        Output_df.Revenue = revenue_daa + revenue_daida + revenue_daididc
    
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        
    num_rows = len(Output_df)
    date = datetime.datetime(Year, 1, 1) + datetime.timedelta(days=Sim_StartDay_index - 1)
    Output_df['Timestamp'] = pd.date_range(start=f'{Year}-{date.month}-{date.day} 00:00', periods=num_rows, freq='15min')
    Output_df.set_index('Timestamp', inplace=True)

    return Output_df



 





    