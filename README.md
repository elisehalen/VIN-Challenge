# Koffie-VIN-Challenge
by Elise H. Cuevas

## Description

This API allows users to work with VIN data while using a SQLite cache and the NHTSA Product Information Catalog Vehicle Listing (vPIC) API. It uses the web framework FastAPI. More information on FastAPI, SQLite and the vPIC API are below.

The API endpoints and their capabilities are as follows:

### /lookup

The /lookup endpoint takes one or more VIN codes entered by the user and searches for data associated with these VINs in a newly built cache. The table containing VIN data in the cache is called "vintable".

If any VINs specified by the user are found in the cache, records containing these VINs are returned. An additional boolean field "CachedResult" is printed showing "True" to indicate that the data was fetched from the cache.

If VINs specified by the user do not exist in the cache, the API connects to and searches the vPIC API for the VIN codes. Once they are located, records containing these VINs are returned and saved in the cache. An additional boolean field "CachedResult" is printed showing "False" to indicate that the data was fetched from the vPIC API.

### /remove

/remove looks up one or more filtered VINs from the user and removes records associated with these VINs in the cache.

A copy of the cache data is created. Next, the user-filtered VINs are stored in another dataframe. Each contains a flag to mark VINs that currently exist in the cache and VINs that the user would like to remove. 

The dataframes are merged together to evaluate all the data. Using the flags, the records are separated into groups: one containing VINs that are in the cache and filtered for- which are to be deleted from the cache- and one containing filtered VINs that do not exist in the cache. The VINs in the cache are removed and a message confirming this is returned. VINs not in the cache return a message stating this.

### /export

Finally, the /export endpoint extracts all data from the cache (vintable) and saves it as a binary file in parquet format. No user input is required.

## Required Installations and Libraries

This API relies on the installation of Python, FastAPI and SQLite3. Also used in this API are the packages: pandas, requests, pydantic and typing.

## Running the API and Testing the Endpoints

To run this API in the terminal, make sure that you are in the right path. The path should point to the folder containing three files: main.py, query_helper.py and classes.py.

Once you are in the right path, run the command "uvicorn main:app" in the terminal to run the main.py file. The http address that returns should be copied and pasted into your browser. Add the extension "/docs" to the end and press Enter. The three API endpoints will appear.

### /lookup

To test /lookup, enter the following three VINs in a list format: 1XPWD40X1ED215307, 1XKWDB0X57J211825, 1XP5DB9X7YN526158. Then, click Execute.

Neither of these VINs exist in the cache, meaning all three VINs will be fetched from the vPIC API. The data corresponding with these VINs will return, as well as a "False" CachedResult value.

Clicking Execute a second time will return the same VIN data from the cache. To confirm, the CachedResult value of "False" will be replaced with "True".

### /remove

This endpoint must be tested after VIN data is added to the cache via the /lookup endpoint. After /lookup has been tested, enter the following VINs in list format: 1XPWD40X1ED215307, 1XKWDB0X57J211825, V123. VIN "V123" is the only VIN of the three being filtered for that does not exist in the cache.

After clicking Execute, a message will appear showing which VINs were removed from the cache and any VINs that could not be located within the cache to be deleted.

### /export

/export can run as long as data exists in the cache. Simply click Execute and a file will be downloaded displaying the cached data in parquet format.


## More Information:

FastAPI:
https://fastapi.tiangolo.com/ 

SQLite:
https://www.sqlite.org/index.html

NHTSA Product Information Catalog Vehicle Listing (vPIC) API:
https://vpic.nhtsa.dot.gov/api/


## Contact

Email: elisehalen@outlook.com

LinkedIn: https://www.linkedin.com/in/elise-cuevas/
