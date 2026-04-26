from pathlib import Path                                                            #imports Path for cleaner file path handling

from parser import parse_all_disease_files                                          #imports the parser function that reads and aggregates the disease files
from county_dictionary import build_county_dictionary                               #imports the function that builds the master county dictionary
from scoring import (                                                               #imports scoring, filtering, and ranking functions
    filter_counties_by_data_quality,                                                #imports the function that filters counties with insufficient usable data
    add_ards_scores,                                                                #imports the function that adds ARDS proxy scores to counties
    rank_counties,                                                                  #imports the generic ranking function
    sepsis_death_score,                                                             #imports the score function for average sepsis deaths
    pneumonia_death_score,                                                          #imports the score function for average pneumonia deaths
    hypertension_death_score,                                                       #imports the score function for average hypertension deaths
    sepsis_rate_score,                                                              #imports the score function for average sepsis crude mortality rate
    pneumonia_rate_score,                                                           #imports the score function for average pneumonia crude mortality rate
    hypertension_rate_score,                                                        #imports the score function for average hypertension crude mortality rate
    final_ards_score,                                                               #imports the score function for the final ARDS trial prioritization score
    filter_counties_by_population,                                                  #imports the filter function for counties with population greater than 250000
    get_disease_metric                                                              #imports the helper function used to safely retrieve disease metrics
)


def load_county_data():                                                             #loads raw files, parses them, builds the county dictionary, filters, and scores counties

    base_dir = Path(__file__).parent                                                #gets the folder where this main.py file is located

    files = {                                                                       #creates a dictionary mapping disease names to their file paths
        "sepsis": base_dir / "Sepsis.txt",                                          #stores the path for the sepsis file
        "pneumonia": base_dir / "Pneumonia.txt",                                    #stores the path for the pneumonia file
        "hypertension": base_dir / "Hypertension.txt"                               #stores the path for the hypertension file
    }

    _, aggregated = parse_all_disease_files(files)                                  #parses and aggregates all disease files

    county_data = build_county_dictionary(aggregated)                               #builds one master county dictionary from the aggregated disease summaries

    county_data = filter_counties_by_data_quality(                                  #filters counties based on minimum valid disease data
        county_data,                                                                #passes the master county dictionary
        required_diseases=["sepsis", "pneumonia"],                                  #requires sepsis and pneumonia because they are the primary ARDS proxy diseases
        min_valid_years=3                                                           #requires at least three valid death-count years for each required disease
    )

    county_data = filter_counties_by_population(                                    #filters out small counties that may not support enough trial enrollment volume
        county_data,                                                                #passes the data-quality-filtered county dictionary
        min_population=250000                                                       #requires at least 250,000 people in the county
    )

    county_data = add_ards_scores(county_data)                                      #adds raw, normalized, and final ARDS prioritization scores

    return county_data                                                              #returns the prepared county dictionary

def print_menu():                                                                   #prints the interactive menu of ranking options

    print()                                                                         #prints a blank line for readability
    print("County Ranking Options")                                                 #prints the menu title
    print("1. Most sepsis deaths")                                                  #prints option 1
    print("2. Highest sepsis crude mortality rate")                                 #prints option 2
    print("3. Most pneumonia deaths")                                               #prints option 3
    print("4. Highest pneumonia crude mortality rate")                              #prints option 4
    print("5. Most hypertension deaths")                                            #prints option 5
    print("6. Highest hypertension crude mortality rate")                           #prints option 6
    print("7. Best overall ARDS trial counties")                                    #prints option 7
    print("8. Quit")                                                                #prints quit option
    print()                                                                         #prints a blank line for readability


def get_ranking_options():                                                          #creates the dictionary that maps menu choices to ranking functions and titles

    ranking_options = {                                                             #initializes a dictionary of possible ranking choices
        "1": {                                                                      #defines menu option 1
            "title": "Top counties by average yearly sepsis deaths",                #stores the display title for option 1
            "score_function": sepsis_death_score                                    #stores the scoring function for option 1
        },
        "2": {                                                                      #defines menu option 2
            "title": "Top counties by average sepsis crude mortality rate",         #stores the display title for option 2
            "score_function": sepsis_rate_score                                     #stores the scoring function for option 2
        },
        "3": {                                                                      #defines menu option 3
            "title": "Top counties by average yearly pneumonia deaths",             #stores the display title for option 3
            "score_function": pneumonia_death_score                                 #stores the scoring function for option 3
        },
        "4": {                                                                      #defines menu option 4
            "title": "Top counties by average pneumonia crude mortality rate",      #stores the display title for option 4
            "score_function": pneumonia_rate_score                                  #stores the scoring function for option 4
        },
        "5": {                                                                      #defines menu option 5
            "title": "Top counties by average yearly hypertension deaths",          #stores the display title for option 5
            "score_function": hypertension_death_score                              #stores the scoring function for option 5
        },
        "6": {                                                                      #defines menu option 6
            "title": "Top counties by average hypertension crude mortality rate",   #stores the display title for option 6
            "score_function": hypertension_rate_score                               #stores the scoring function for option 6
        },
        "7": {                                                                      #defines menu option 7
            "title": "Top counties by final ARDS trial prioritization score",       #stores the display title for option 7
            "score_function": final_ards_score                                      #stores the scoring function for option 7
        }
    }

    return ranking_options                                                          #returns the completed ranking-options dictionary


def get_top_n_choice():                                                             #asks the user how many counties to display

    top_n_raw = input("How many counties should be shown? Press Enter for 20: ")     #gets user input for number of counties
    top_n_raw = top_n_raw.strip()                                                   #removes extra whitespace from the input

    if top_n_raw == "":                                                             #checks if the user pressed Enter without typing a number
        return 20                                                                   #returns the default value of 20

    try:                                                                            #attempts to convert the input into an integer
        top_n = int(top_n_raw)                                                      #converts the input string into an integer

    except ValueError:                                                              #runs if the input cannot be converted into an integer
        print("Invalid number. Defaulting to top 20 counties.")                     #prints a warning message
        return 20                                                                   #returns the default value of 20

    if top_n <= 0:                                                                  #checks if the user entered zero or a negative number
        print("Invalid number. Defaulting to top 20 counties.")                     #prints a warning message
        return 20                                                                   #returns the default value of 20

    return top_n                                                                    #returns the valid top-N value


def print_ranked_counties(ranked_counties, score_function):                         #prints ranked counties in a readable table-like format

    print()                                                                         #prints a blank line for readability
    print("Rank | FIPS  | County                    | State | Population | Score    | Sepsis Deaths | Pneumonia Deaths | Sepsis Rate | Pneumonia Rate")  #prints the table header
    print("-" * 135)                                                                #prints a separator line

    for rank, ranked_item in enumerate(ranked_counties, start=1):                   #loops through ranked counties with rank numbers starting at 1

        fips = ranked_item[0]                                                       #gets the FIPS code from the ranked item
        county = ranked_item[1]                                                     #gets the county dictionary from the ranked item

        county_name = county["county"]                                              #gets the county name
        state = county["state"]                                                     #gets the state abbreviation
        population = county["latest_population"]                                    #gets the latest available population

        score = score_function(county)                                              #calculates the score used for this ranking

        sepsis_deaths = get_disease_metric(county, "sepsis", "average_deaths")      #gets average sepsis deaths for display
        pneumonia_deaths = get_disease_metric(county, "pneumonia", "average_deaths")#gets average pneumonia deaths for display
        sepsis_rate = get_disease_metric(county, "sepsis", "average_crude_rate")    #gets average sepsis crude rate for display
        pneumonia_rate = get_disease_metric(county, "pneumonia", "average_crude_rate")  #gets average pneumonia crude rate for display

        print(                                                                      #prints one formatted county row
            f"{rank:<4} | "                                                         #prints rank left-aligned
            f"{fips:<5} | "                                                         #prints FIPS left-aligned
            f"{county_name:<25} | "                                                 #prints county name left-aligned
            f"{state:<5} | "                                                        #prints state abbreviation left-aligned
            f"{str(population):<10} | "                                             #prints population left-aligned
            f"{score:<8.2f} | "                                                     #prints score rounded to 2 decimals
            f"{sepsis_deaths:<13.2f} | "                                            #prints sepsis deaths rounded to 2 decimals
            f"{pneumonia_deaths:<16.2f} | "                                         #prints pneumonia deaths rounded to 2 decimals
            f"{sepsis_rate:<11.2f} | "                                              #prints sepsis crude rate rounded to 2 decimals
            f"{pneumonia_rate:<14.2f}"                                              #prints pneumonia crude rate rounded to 2 decimals
        )


def run_ranking_menu(county_data):                                                  #runs the interactive ranking menu

    ranking_options = get_ranking_options()                                         #loads the ranking option dictionary

    while True:                                                                     #starts a loop that continues until the user quits

        print_menu()                                                                #prints the menu options

        choice = input("Enter choice number: ")                                     #asks the user to choose a ranking option
        choice = choice.strip()                                                     #removes extra whitespace from the choice

        if choice == "8":                                                           #checks if the user selected quit
            print("Exiting county ranking tool.")                                   #prints an exit message
            break                                                                   #exits the interactive loop

        ranking_config = ranking_options.get(choice)                                #gets the ranking configuration for the selected choice

        if ranking_config is None:                                                  #checks if the choice was invalid
            print("Invalid choice. Please choose a number from 1 to 8.")             #prints an invalid-choice warning
            continue                                                                #returns to the top of the loop

        top_n = get_top_n_choice()                                                  #asks how many counties should be shown

        ranked_counties = rank_counties(                                            #ranks counties using the chosen scoring function
            county_data,                                                            #passes the prepared county dictionary
            ranking_config["score_function"],                                       #passes the selected score function
            top_n=top_n                                                             #passes the selected number of results
        )

        print()                                                                     #prints a blank line for readability
        print(ranking_config["title"])                                              #prints the ranking title

        print_ranked_counties(                                                      #prints the ranked result table
            ranked_counties,                                                        #passes the ranked counties
            ranking_config["score_function"]                                        #passes the score function used for ranking
        )


def main():                                                                         #main function that runs the full program

    county_data = load_county_data()                                                #loads, cleans, builds, filters, and scores county data

    run_ranking_menu(county_data)                                                   #starts the interactive ranking menu


if __name__ == "__main__":                                                          #checks if this script is being run directly

    main()                                                                          #runs the program

