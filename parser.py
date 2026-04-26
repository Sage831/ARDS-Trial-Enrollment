import csv                                                           #imports Python's built-in CSV module for reading structured text files
from pathlib import Path                                             #imports Path for cleaner file path handling
from pprint import pprint                                            #imports pprint to print nested dictionaries in a readable way


def clean_numeric(value, as_int = False):                                           #cleans a value from the file and converts it into a number if possible

    value = str(value).strip()                                                      #converts value to a string and removes whitespaces

    invalid_values = {"", "Suppressed", "Unreliable", "Missing", "None"}            #set of values that should be treated as missing

    if value in invalid_values:                                                     #checks if the value is missing, suppressed, unreliable, or invalid
        return None                                                                 #returns None to mark the value as unusable numeric data

    try:                                                                            #attempts to convert the cleaned value into a number
        number = float(value.replace(",", ""))                                      #removes commas and converts the value into a float

        if as_int:                                                                  #checks if the caller wants the result as an integer
            return int(number)                                                      #converts the number to an integer and returns it

        return number                                                               #returns the float value if an integer was not requested

    except ValueError:                                                              #catches the error caused by trying to convert non-numeric text into a float
        return None                                                                 #returns None instead of allowing the program to crash


def split_county_state(county_string):                               #separates a combined county/state string into county name and state abbreviation

    county_string = county_string.strip()                            #removes whitespaces from the county string
    county_string = county_string.strip('"')                         #removes quotation marks from the beginning/end if present

    if "," not in county_string:                                     #checks if the county string does not contain a comma
        return county_string, None                                   #returns the whole string as county name and None for state

    county, state = county_string.rsplit(",", 1)                     #splits the string at the last comma into county and state parts

    county = county.strip()                                          #removes whitespace around the county name
    state = state.strip()                                            #removes whitespace around the state abbreviation

    return county, state                                             #returns the separated county and state values


def parse_disease_file(file_path):                                          #parses one disease text file into year-by-year county data

    disease_data = {}                                                       #initializes an empty dictionary to store parsed county data

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:    #opens the disease file for reading
        reader = csv.DictReader(file, delimiter="\t")                       #creates a dictionary reader for tab-separated rows

        for row in reader:                                                  #loops through each row in the file
            fips = row.get("County Code", "")                               #gets the county FIPS code from the row
            fips = str(fips).strip()                                        #converts FIPS to string and removes whitespace
            fips = fips.zfill(5)                                            #pads FIPS with leading zeroes so all county codes are 5 digits

            county_raw = row.get("County", "")                              #gets the raw county/state string from the row
            year_raw = row.get("Year Code")                                 #gets the year code from the row
            deaths_raw = row.get("Deaths")                                  #gets the deaths value from the row
            population_raw = row.get("Population")                          #gets the population value from the row
            crude_rate_raw = row.get("Crude Rate")                          #gets the crude rate value from the row

            year = clean_numeric(year_raw, as_int=True)                     #cleans and converts the year into an integer
            deaths = clean_numeric(deaths_raw, as_int=True)                 #cleans and converts deaths into an integer
            population = clean_numeric(population_raw, as_int=True)         #cleans and converts population into an integer
            crude_rate = clean_numeric(crude_rate_raw)                      #cleans and converts crude rate into a float

            if not fips:                                                    #checks if FIPS is empty
                continue                                                    #skips the row if there is no usable FIPS code

            if fips == "00000":                                             #checks for an invalid all-zero FIPS code
                continue                                                    #skips the row if the FIPS code is invalid

            if year is None:                                                #checks if year could not be parsed
                continue                                                    #skips the row because year is required

            county_name, state = split_county_state(county_raw)             #separates the raw county string into county name and state

            if fips not in disease_data:                                    #checks if this county has not been added yet
                disease_data[fips] = {                                      #creates a new dictionary entry for this county
                    "county": county_name,                                  #stores the county name
                    "state": state,                                         #stores the state abbreviation
                    "years": {}                                             #creates a nested dictionary for year-by-year data
                }

            disease_data[fips]["years"][year] = {                           #stores this row's data under the matching year
                "deaths": deaths,                                           #stores cleaned deaths value
                "population": population,                                   #stores cleaned population value
                "crude_rate": crude_rate,                                   #stores cleaned crude rate value
                "death_suppressed": deaths is None,                         #stores whether deaths were missing/suppressed/unusable
                "rate_unreliable": crude_rate is None                       #stores whether crude rate was missing/unreliable/unusable
            }

    return disease_data                                                     #returns the completed year-by-year disease dictionary


def get_population_year(population_entry):                           #helper function used to compare population entries by year

    return population_entry[0]                                       #returns the year from a (year, population) tuple


def aggregate_disease_data(disease_data):                            #aggregates year-by-year disease data into county-level summary metrics

    aggregated = {}                                                  #initializes an empty dictionary for aggregated county data

    for fips, county_info in disease_data.items():                   #loops through each county in the parsed disease data
        years = county_info["years"]                                 #gets the nested year-by-year dictionary for this county

        valid_deaths = []                                            #initializes a list for usable death values
        valid_rates = []                                             #initializes a list for usable crude rate values
        valid_populations = []                                       #initializes a list for usable population values paired with years

        for year, year_data in years.items():                        #loops through each year of data for this county
            if year_data["deaths"] is not None:                      #checks if deaths value is usable
                valid_deaths.append(year_data["deaths"])             #adds the usable deaths value to the deaths list

            if year_data["crude_rate"] is not None:                  #checks if crude rate value is usable
                valid_rates.append(year_data["crude_rate"])          #adds the usable crude rate value to the rates list

            if year_data["population"] is not None:                  #checks if population value is usable
                population_entry = (year, year_data["population"])   #creates a tuple containing year and population
                valid_populations.append(population_entry)           #adds the population entry to the population list

        latest_population = None                                     #initializes latest population as None
        latest_year = None                                           #initializes latest year as None

        if len(valid_populations) > 0:                                          #checks if there is at least one usable population value
            latest_entry = max(valid_populations, key=get_population_year)      #finds the population entry with the latest year
            latest_year = latest_entry[0]                                       #extracts the latest year from the latest population entry
            latest_population = latest_entry[1]                                 #extracts the population from the latest population entry

        total_deaths = None                                          #initializes total deaths as None
        average_deaths = None                                        #initializes average deaths as None
        average_crude_rate = None                                    #initializes average crude rate as None

        if len(valid_deaths) > 0:                                    #checks if there are usable death values
            total_deaths = sum(valid_deaths)                         #calculates total deaths across all valid years
            average_deaths = sum(valid_deaths) / len(valid_deaths)   #calculates average deaths across all valid years

        if len(valid_rates) > 0:                                     #checks if there are usable crude rate values
            average_crude_rate = sum(valid_rates) / len(valid_rates) #calculates average crude rate across all valid years

        aggregated[fips] = {                                         #creates the aggregated county entry
            "county": county_info["county"],                         #stores the county name
            "state": county_info["state"],                           #stores the state abbreviation
            "latest_year": latest_year,                              #stores the latest year with usable population data
            "latest_population": latest_population,                  #stores the latest available population
            "total_deaths": total_deaths,                            #stores total deaths across valid years
            "average_deaths": average_deaths,                        #stores average deaths across valid years
            "average_crude_rate": average_crude_rate,                #stores average crude rate across valid years
            "valid_death_years": len(valid_deaths),                  #stores the number of years with usable death values
            "valid_rate_years": len(valid_rates),                    #stores the number of years with usable crude rate values
            "total_years": len(years),                               #stores the total number of years found for this county
            "missing_death_years": len(years) - len(valid_deaths),   #stores number of years with missing/suppressed death values
            "missing_rate_years": len(years) - len(valid_rates)      #stores number of years with missing/unreliable rate values
        }

    return aggregated                                                #returns the completed aggregated county dictionary


def parse_all_disease_files(file_map):                               #parses and aggregates all disease files listed in file_map

    parsed = {}                                                      #initializes dictionary for detailed year-by-year disease data
    aggregated = {}                                                  #initializes dictionary for summarized disease data

    for disease_name, file_path in file_map.items():                 #loops through each disease name and its file path
        disease_data = parse_disease_file(file_path)                 #parses the disease file into year-by-year county data
        disease_summary = aggregate_disease_data(disease_data)       #aggregates the parsed data into county-level summaries

        parsed[disease_name] = disease_data                          #stores detailed data under the disease name
        aggregated[disease_name] = disease_summary                   #stores aggregated data under the disease name

    return parsed, aggregated                                        #returns both detailed and aggregated disease dictionaries


def main():                                                          #main function that runs when the script is executed directly

    files = {                                                        #creates a dictionary mapping disease names to file paths
        "sepsis": Path("Sepsis.txt"),                                #stores the file path for the sepsis data
        "pneumonia": Path("Pneumonia.txt"),                          #stores the file path for the pneumonia data
        "hypertension": Path("Hypertension.txt")                     #stores the file path for the hypertension data
    }

    parsed, aggregated = parse_all_disease_files(files)              #parses and aggregates all disease files

    pprint(aggregated["sepsis"]["01001"])                            #prints one sample county's aggregated sepsis data for testing


if __name__ == "__main__":                                           #checks if this script is being run directly
    main()                                                           #runs the main function

