from classes import *


def print_vin(item: GetVinData):   
    query = """
    SELECT *
    FROM vintable
    WHERE VIN IN (v_n)
    """
    v_n = ", ".join(["?"] * len(item.vin)) 
    query = query.replace('v_n', v_n)
    return query



def delete_vin(item: GetVinData):   
    query = """
    DELETE FROM vintable WHERE VIN IN (v_n)
    """
    v_n = ", ".join(["?"] * len(item.vin))  
    query = query.replace('v_n', v_n)
    return query
