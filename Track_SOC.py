
import pandas as pd
import numpy as np

def Track_SOC(power_df, init_SOC, total_capacity, target_SOC=50, upper_SOC_limit = 100, lower_SOC_limit = 0):
    """
    Tracks SOC over 4-hour blocks.

    Parameters:
    - power_df: DataFrame with 'Power' and index as Timestamps (1-sec resolution).
    - init_SOC: Initial state of charge (percentage).
    - total_capacity: Total Allocated capacity.
    - nom_SOC: Target SOC (default 50%).

    Returns:
    - Updated power_df with modified 4h blocks if necessary.
    """

    df = power_df.copy()
    df = df.rename("Power").to_frame()
    df = df.sort_index()
    
    # Ensure timestamp is datetime
    df.index = pd.to_datetime(df.index)

    time_step_hr = 1 / 3600

    soc_track = [init_SOC]
    current_SOC = init_SOC

    # Iterate over 4-hour blocks
    start_time = df.index.min()
    end_time = df.index.max()
    block_start = start_time

    while block_start < end_time:
        block_end = block_start + pd.Timedelta(hours=4)
        block_mask = (df.index >= block_start) & (df.index < block_end)
        block = df.loc[block_mask]

        if block.empty:
            break

        # Energy throughput (sum of power * delta_t)
        energy_kWh = block['Power'].sum() * time_step_hr
        # Energy as % of capacity
        delta_SOC_percent = (energy_kWh / total_capacity) * 100

        new_SOC = current_SOC + delta_SOC_percent

        if lower_SOC_limit <= new_SOC <= upper_SOC_limit:
            # Within bounds — accept and move on
            current_SOC = new_SOC
        else:
            # Outside bounds — modify the block to reach nominal SOC (50%)
            delta_needed = target_SOC - current_SOC
            energy_needed_kWh = (delta_needed / 100) * total_capacity
            # Constant power over 4 hours
            const_power = energy_needed_kWh / (4)  # kW
            # Apply constant power to the block
            df.loc[block_mask, 'Power'] = const_power
            # Set SOC to nominal for next block
            current_SOC = target_SOC

        soc_track.append(current_SOC)
        block_start = block_end

    return df, soc_track