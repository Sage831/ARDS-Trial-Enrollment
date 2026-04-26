def get_disease_metric(county, disease_name, metric_name):                          #safely retrieves one metric from one disease inside a county dictionary

    diseases = county.get("diseases", {})                                           #gets the nested diseases dictionary, or an empty dictionary if it is missing

    disease = diseases.get(disease_name)                                            #gets the requested disease dictionary from the county

    if disease is None:                                                             #checks if the requested disease is missing for this county
        return 0                                                                    #returns zero so missing disease data does not crash scoring

    value = disease.get(metric_name)                                                #gets the requested metric from the disease dictionary

    if value is None:                                                               #checks if the requested metric is missing or unusable
        return 0                                                                    #returns zero so missing metric values do not crash scoring

    return value                                                                    #returns the usable metric value


def has_minimum_valid_data(county, required_diseases=None, min_valid_years=3):      #checks if a county has enough valid data to be included in ranking

    if required_diseases is None:                                                   #checks if no custom required disease list was provided
        required_diseases = ["sepsis", "pneumonia"]                                 #defaults to sepsis and pneumonia because they are the main ARDS proxy diseases

    diseases = county.get("diseases", {})                                           #gets the nested diseases dictionary for this county

    for disease_name in required_diseases:                                          #loops through each disease required for reliable ranking

        disease = diseases.get(disease_name)                                        #gets the disease summary for the current required disease

        if disease is None:                                                         #checks if the disease is missing entirely for this county
            return False                                                            #returns False because the county does not have enough required data

        valid_death_years = disease.get("valid_death_years", 0)                     #gets the number of valid death-count years for this disease

        if valid_death_years < min_valid_years:                                     #checks if the disease has too few valid years
            return False                                                            #returns False because the county has insufficient reliable data

    return True                                                                     #returns True if all required diseases have enough valid data


def filter_counties_by_data_quality(county_data, required_diseases=None, min_valid_years=3):  #filters out counties with insufficient disease data

    filtered_counties = {}                                                          #initializes a dictionary to store counties that pass the quality filter

    for fips, county in county_data.items():                                        #loops through each FIPS code and county dictionary

        if has_minimum_valid_data(county, required_diseases, min_valid_years):      #checks if the county has enough valid data
            filtered_counties[fips] = county                                        #adds the county to the filtered dictionary

    return filtered_counties                                                        #returns only counties with enough usable data


def sepsis_death_score(county):                                                     #scores a county by average yearly sepsis deaths

    return get_disease_metric(county, "sepsis", "average_deaths")                   #returns the average sepsis deaths for this county


def pneumonia_death_score(county):                                                  #scores a county by average yearly pneumonia deaths

    return get_disease_metric(county, "pneumonia", "average_deaths")                #returns the average pneumonia deaths for this county


def hypertension_death_score(county):                                               #scores a county by average yearly hypertension deaths

    return get_disease_metric(county, "hypertension", "average_deaths")             #returns the average hypertension deaths for this county


def sepsis_rate_score(county):                                                      #scores a county by average sepsis crude mortality rate

    return get_disease_metric(county, "sepsis", "average_crude_rate")               #returns the average sepsis crude mortality rate for this county


def pneumonia_rate_score(county):                                                   #scores a county by average pneumonia crude mortality rate

    return get_disease_metric(county, "pneumonia", "average_crude_rate")            #returns the average pneumonia crude mortality rate for this county


def hypertension_rate_score(county):                                                #scores a county by average hypertension crude mortality rate

    return get_disease_metric(county, "hypertension", "average_crude_rate")         #returns the average hypertension crude mortality rate for this county


def ards_proxy_volume_score(county):                                                #scores a county by ARDS-related death volume using sepsis and pneumonia

    sepsis_deaths = get_disease_metric(county, "sepsis", "average_deaths")          #gets the average yearly sepsis deaths
    pneumonia_deaths = get_disease_metric(county, "pneumonia", "average_deaths")    #gets the average yearly pneumonia deaths

    score = (                                                                       #creates a weighted volume score from the two primary ARDS proxy diseases
        0.60 * sepsis_deaths                                                        #weights sepsis deaths at 60 percent because sepsis is a major ARDS pathway
        + 0.40 * pneumonia_deaths                                                   #weights pneumonia deaths at 40 percent because pneumonia is a direct respiratory ARDS pathway
    )

    return score                                                                    #returns the weighted ARDS proxy volume score


def ards_proxy_rate_score(county):                                                  #scores a county by ARDS-related crude mortality rate using sepsis and pneumonia

    sepsis_rate = get_disease_metric(county, "sepsis", "average_crude_rate")        #gets the average sepsis crude mortality rate
    pneumonia_rate = get_disease_metric(county, "pneumonia", "average_crude_rate")  #gets the average pneumonia crude mortality rate

    score = (                                                                       #creates a weighted crude-rate score from the two primary ARDS proxy diseases
        0.60 * sepsis_rate                                                          #weights sepsis rate at 60 percent because sepsis is a major ARDS pathway
        + 0.40 * pneumonia_rate                                                     #weights pneumonia rate at 40 percent because pneumonia is a direct respiratory ARDS pathway
    )

    return score                                                                    #returns the weighted ARDS proxy rate score


def hypertension_context_score(county):                                                 #scores a county by hypertension death burden as secondary comorbidity context

    hypertension_deaths = get_disease_metric(county, "hypertension", "average_deaths")  #gets average yearly hypertension deaths

    return hypertension_deaths                                                          #returns average hypertension deaths as the context score


def min_max_normalize(value, minimum, maximum):                                     #normalizes a numeric value to a 0-to-1 range

    if value is None:                                                               #checks if the value is missing
        return 0                                                                    #returns zero for missing values

    if maximum == minimum:                                                          #checks if normalization would divide by zero
        return 0                                                                    #returns zero because all values are identical and cannot be meaningfully separated

    normalized_value = (value - minimum) / (maximum - minimum)                      #calculates min-max normalized value

    return normalized_value                                                         #returns the normalized value


def get_score_range(county_data, score_function):                                   #finds the minimum and maximum score values for a scoring function

    scores = []                                                                     #initializes a list to store score values

    for county in county_data.values():                                             #loops through each county dictionary
        score = score_function(county)                                              #calculates the score for the current county
        scores.append(score)                                                        #adds the score to the list

    if len(scores) == 0:                                                            #checks if no counties were available to score
        return 0, 0                                                                 #returns a safe empty range so the program does not crash

    minimum = min(scores)                                                           #gets the lowest score
    maximum = max(scores)                                                           #gets the highest score

    return minimum, maximum                                                         #returns the minimum and maximum score values


def add_ards_scores(county_data):                                                   #adds raw, normalized, and final ARDS proxy scores to each county

    min_volume, max_volume = get_score_range(county_data, ards_proxy_volume_score)  #gets the min and max ARDS volume scores
    min_rate, max_rate = get_score_range(county_data, ards_proxy_rate_score)        #gets the min and max ARDS rate scores

    for county in county_data.values():                                             #loops through each county dictionary

        raw_volume_score = ards_proxy_volume_score(county)                          #calculates the county's raw ARDS proxy volume score
        raw_rate_score = ards_proxy_rate_score(county)                              #calculates the county's raw ARDS proxy rate score

        normalized_volume_score = min_max_normalize(                                #normalizes the county's volume score
            raw_volume_score,                                                       #passes the county's raw volume score
            min_volume,                                                             #passes the minimum volume score
            max_volume                                                              #passes the maximum volume score
        )

        normalized_rate_score = min_max_normalize(                                  #normalizes the county's rate score
            raw_rate_score,                                                         #passes the county's raw rate score
            min_rate,                                                               #passes the minimum rate score
            max_rate                                                                #passes the maximum rate score
        )

        final_score = (                                                             #combines normalized volume and rate into one final ARDS score
            0.75 * normalized_volume_score                                          #weights volume more heavily because clinical trials need enough patients to enroll
            + 0.25 * normalized_rate_score                                          #weights rate less heavily because high-rate small counties may still have low patient volume
        )

        county["scores"] = {                                                        #creates a nested scores dictionary for this county
            "raw_ards_volume_score": raw_volume_score,                              #stores the unnormalized ARDS volume score
            "raw_ards_rate_score": raw_rate_score,                                  #stores the unnormalized ARDS rate score
            "normalized_volume_score": normalized_volume_score,                     #stores the normalized volume score
            "normalized_rate_score": normalized_rate_score,                         #stores the normalized rate score
            "final_ards_score": final_score                                         #stores the final weighted ARDS score
        }

    return county_data                                                              #returns the county dictionary with scores added


def final_ards_score(county):                                                       #retrieves the final ARDS score from a scored county dictionary

    scores = county.get("scores", {})                                               #gets the county's scores dictionary, or an empty dictionary if missing

    score = scores.get("final_ards_score")                                          #gets the final ARDS score

    if score is None:                                                               #checks if the final ARDS score is missing
        return 0                                                                    #returns zero so ranking does not crash

    return score                                                                    #returns the final ARDS score


def rank_counties(county_data, score_function, top_n=20):                           #ranks counties using any scoring function

    ranked_counties = sorted(                                                       #sorts counties into a ranked list
        county_data.items(),                                                        #gets county entries as (FIPS, county dictionary) pairs
        key=lambda item: score_function(item[1]),                                   #scores each county using the provided scoring function
        reverse=True                                                                #sorts from highest score to lowest score
    )

    return ranked_counties[:top_n]                                                  #returns only the top N counties


def build_scored_counties(county_data, min_valid_years=3):                          #filters counties and adds final ARDS scores

    filtered_counties = filter_counties_by_data_quality(                            #filters counties based on required valid sepsis/pneumonia data
        county_data,                                                                #passes the master county dictionary
        required_diseases=["sepsis", "pneumonia"],                                  #requires the two main ARDS proxy diseases
        min_valid_years=min_valid_years                                             #requires the chosen number of valid years
    )

    scored_counties = add_ards_scores(filtered_counties)                            #adds ARDS scores to the filtered county dictionary

    return scored_counties                                                          #returns filtered and scored counties


def get_top_ards_counties(county_data, top_n=20, min_valid_years=3):                #returns the top counties ranked by final ARDS proxy score

    scored_counties = build_scored_counties(                                        #filters counties and adds ARDS scores
        county_data,                                                                #passes the master county dictionary
        min_valid_years=min_valid_years                                             #passes the minimum valid-year threshold
    )

    ranked_counties = rank_counties(                                                #ranks counties by final ARDS score
        scored_counties,                                                            #passes the filtered and scored county dictionary
        final_ards_score,                                                           #uses final ARDS score as the ranking function
        top_n=top_n                                                                 #limits the output to the requested number of counties
    )

    return scored_counties, ranked_counties                                         #returns both the scored county dictionary and the ranked top counties

