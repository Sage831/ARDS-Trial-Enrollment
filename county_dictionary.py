from collections import defaultdict                                      #imports defaultdict so new county entries can be created automatically


def make_county_entry():                                                 #creates the default structure for one county in the master county dictionary

    return {                                                             #returns a new dictionary every time a new county FIPS is first accessed
        "county": None,                                                  #stores the county name
        "state": None,                                                   #stores the state abbreviation
        "latest_population": None,                                       #stores the latest available population for the county
        "latest_year": None,                                             #stores the year connected to the latest available population
        "diseases": {}                                                   #stores nested disease-specific summaries for this county
    }


def build_county_dictionary(aggregated):                                 #builds one master county dictionary from all aggregated disease summaries

    county_data = defaultdict(make_county_entry)                         #creates a dictionary that automatically creates a blank county entry for new FIPS codes

    for disease_name, disease_summary in aggregated.items():             #loops through each disease name and its aggregated county summary dictionary

        for fips, summary in disease_summary.items():                    #loops through each county FIPS code and its summary for the current disease

            county = county_data[fips]                                   #gets the county entry, automatically creating it if the FIPS is new

            county["county"] = summary["county"]                         #stores or updates the county name from the current disease summary
            county["state"] = summary["state"]                           #stores or updates the state abbreviation from the current disease summary

            existing_year = county["latest_year"]                        #gets the population year currently stored for this county
            new_year = summary["latest_year"]                            #gets the population year from the current disease summary
            new_population = summary["latest_population"]                #gets the population value from the current disease summary

            if new_year is not None and new_population is not None:      #checks if the current disease summary has usable population-year data

                if existing_year is None or new_year > existing_year:    #checks if the current disease summary has the newest population year so far
                    county["latest_population"] = new_population         #stores the newest available population value
                    county["latest_year"] = new_year                     #stores the newest available population year

            county["diseases"][disease_name] = {                         #stores the current disease summary inside the county's disease dictionary
                "total_deaths": summary["total_deaths"],                 #stores total deaths across valid years for this disease
                "average_deaths": summary["average_deaths"],             #stores average yearly deaths across valid years for this disease
                "average_crude_rate": summary["average_crude_rate"],     #stores average crude mortality rate across valid years for this disease
                "valid_death_years": summary["valid_death_years"],       #stores the number of valid years for death counts
                "valid_rate_years": summary["valid_rate_years"],         #stores the number of valid years for crude mortality rates
                "total_years": summary["total_years"],                   #stores the total number of years found for this county and disease
                "missing_death_years": summary["missing_death_years"],   #stores the number of missing or unusable death-count years
                "missing_rate_years": summary["missing_rate_years"]      #stores the number of missing or unusable crude-rate years
            }

    return dict(county_data)                                             #converts the defaultdict back into a normal dictionary and returns it

