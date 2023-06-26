# ------ Import required libraries ------

from fastapi import FastAPI
import pandas as pd
import sqlite3
from classes import *
import query_helper
import requests
import fastparquet


# --------- Define API ---------

app = FastAPI()


# ------ Open database using SQLite and set cursor ------

conn = sqlite3.connect('cache.db', check_same_thread=False)
cur = conn.cursor()
conn.commit()

# ------ Create empty table called "vintable" in cache ------

cur.execute("""
DROP TABLE IF EXISTS vintable
""")
cur.fetchall()

cur.execute("""
CREATE TABLE vintable (
    VIN,
    Make,
    Model,
    ModelYear,
    BodyClass
    )
    """)
cur.fetchall()


# ------------------- ENDPOINT #1 -------------------
# This route will first check the SQLite database to see if a cached result is available. If so, it should be returned from the database.
# If not, your API should contact the vPIC API to decode the VIN, store the results in the database, and return the result.
# The request should contain a single string called "vin". It should contain exactly 17 alphanumeric characters.
# The response object should contain the following elements:
# •	Input VIN Requested (string, exactly 17 alphanumeric characters)
# •	Make (String)
# •	Model (String)
# •	Model Year (String)
# •	Body Class (String)
# •	Cached Result? (Boolean)


@app.post("/lookup")
async def lookup_vin(item: GetVinData):
    # ------- PART 1 - DATA FROM CACHE -------
    # Execute query that filters for specified VINs and pulls corresponding data from cache.
    query = query_helper.print_vin(item)
    cur.execute(query, item.vin)
    x = cur.fetchall()
    # Column names are not included in result. Extract these from cur.description and add to result.
    cols = [col[0] for col in cur.description] 
    cache_result = [dict(zip(cols, row)) for row in x] 
    # Add a "CachedResult" key and set value = True.
    for row in cache_result:
        row['CachedResult'] = True    
    # ------- PART 2 - DATA FROM vPIC API -------
    # Identify location of API
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"
    # Create and fill placeholder to enter VINs being filtered for.
    v_n = "; ".join(["?"] * len(item.vin))   
    v_n = "; ".join([vin for vin in item.vin])
    data = {
        "format": "json",
        "data": v_n          
                }
    try:
        # Fetch VINs from API.
        api_result = requests.post(url, data=data)
        api_result.raise_for_status()
        api_result = api_result.json()
        if api_result.get("Results"):
            # Store results in api_result.
            api_result = api_result["Results"]
            # Since this data is from API, CachedResult = False.
            for row in api_result:
                row['CachedResult'] = False
            # Convert results from cache and API to dataframes.
            cache_result = pd.DataFrame(cache_result)
            api_result = pd.DataFrame(api_result)
            # Shorten api_result so columns align with those in cache_result.
            api_result = api_result[['VIN', 'Make', 'Model', 'ModelYear', 'BodyClass', 'CachedResult']]
            # Append API and cache results together; remove any VINs/rows from API that we already have from cache.
            return_result = cache_result.append(api_result)
            return_result = return_result.sort_values(by=['VIN', 'CachedResult'], ascending=False).drop_duplicates(subset=['VIN'], keep='first') # Dropping rows returned by API that already exist in and are being returned from cache.
            # Import new rows from API into cache.
            add_to_cache = return_result[return_result['CachedResult'] == False]
            add_to_cache = add_to_cache[['VIN', 'Make', 'Model', 'ModelYear', 'BodyClass']]
            add_to_cache.to_sql('vintable', con=conn, if_exists='append', index=False)
            # Check what's left in the cache/vintable in Terminal.
            cur.execute("SELECT * FROM vintable")  
            x = cur.fetchall()
            print(x)
            # Commit changes.
            conn.commit()
        return return_result.to_dict('records')
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}




# ------------------- ENDPOINT #2 -------------------  
# /remove
# This route will remove a entry from the cache.
# The request should contain a single string called "vin". It should contain exactly 17 alphanumeric characters.
# The response object should contain the following elements:
# •	Input VIN Requested (string, exactly 17 alphanumeric characters)
# •	Cache Delete Success? (boolean)



@app.post("/remove")
async def remove_vin(item: GetVinData):
    # Create copy of cache to work with - shows all data currently in cache/vintable.
    query = ("SELECT * FROM vintable")
    cur.execute(query)
    cache = cur.fetchall()
    cache = pd.DataFrame(cache)
    cache.columns = ['VIN', 'Make', 'Model', 'ModelYear', 'BodyClass']
    # Add a flag column to mark records currently in cache (for merge later).
    cache['Cache_Flag'] = 1
    # Create variable for VINs we want to remove.
    filtered_vins = item.vin
    filtered_vins = pd.DataFrame(filtered_vins)
    filtered_vins.columns = ['VIN']
    # Add a flag column to mark VINs filtered for- may or may not be in the cache.
    filtered_vins['Filter_Flag'] = 1
    # Merge dataframes to see all data. This helps decipher what's going on.
    cache_vins = filtered_vins.merge(cache, how='outer', left_on='VIN', right_on='VIN') 
    # View all data in Terminal - filtered vins and all VIN data currently in cache.
    print(cache_vins)
    # Create subsets for filtered vins we will delete (1 in both flag columns) and filtered vins not in cache (1 in Filter_Flag, Null in Cache_Flag).
    delete_from_cache = cache_vins[(cache_vins['Filter_Flag'] == 1) & (cache_vins['Cache_Flag'] == 1)]
    delete_from_cache = delete_from_cache['VIN']
    not_in_cache = cache_vins[(cache_vins['Filter_Flag'] == 1) & (cache_vins['Cache_Flag'].isnull())]
    not_in_cache = not_in_cache['VIN']
    # Delete filtered vins.
    item.vin = list(delete_from_cache)
    query = query_helper.delete_vin(item)
    cur.execute(query, item.vin)
    # Check remaining cache data in Terminal.
    cur.execute("SELECT * FROM vintable")
    x = cur.fetchall()
    print(x)
    # Print message - displaying results differently here (no boolean field).
    not_in_cache = list(not_in_cache)
    message1 = f'VIN(s) {item.vin} were removed from the cache.'
    message2 = f'VIN(s) {not_in_cache} cannot be found in the cache.'
    message = message1 + ' ' + message2
    # Commit changes to cache.
    conn.commit()
    return message



# ------------------- ENDPOINT #3 -------------------
# /export
# This route will export the SQLite database cache and return a binary file (parquet format) containing the data in the cache.
# No additional input/data should be required to make the request.
# The response object should be a binary file downloaded by the client containing all currently cached VINs in a table stored in parquet format.


@app.get("/export")
async def export_data():
    # Extract all data from cache.
    cur.execute("SELECT * FROM vintable")
    x = cur.fetchall()
    x = pd.DataFrame(x)
    # Assign column names to x before converting x to parquet format.
    cols = [col[0] for col in cur.description]
    x.columns = cols
    # Convert all columns to strings.
    x = x.astype({column: str for column in x.columns})
    print(x)
    # Save as parquet file.
    x.to_parquet('vintable.parquet', engine='fastparquet')
    message = 'File downloaded.'
    return message


# Test VINs:
# 1XPWD40X1ED215307
# 1XKWDB0X57J211825
# 1XP5DB9X7YN526158
# 4V4NC9EJXEN171694
# 1XP5DB9X7XD487964
