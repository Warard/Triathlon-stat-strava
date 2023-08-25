import requests 
import pandas as pd 
from datetime import datetime, timedelta, date
import json
import matplotlib.pyplot as plt

###----- CONSTANTS DEFINITION -----###
today = date.today()
today_datetime =datetime(today.year, today.month, today.day)

last_monday = today - timedelta(days=today.weekday())
last_monday_datetime = datetime(last_monday.year, last_monday.month, last_monday.day)

scnd_last_monday = last_monday - timedelta(days=7)
scnd_last_monday_datetime = datetime(scnd_last_monday.year, scnd_last_monday.month, scnd_last_monday.day)

last_sunday_datetime = datetime(last_monday.year, last_monday.month, last_monday.day-1)
# >------after_date SHOW_THOSE_RUNS before_date ------>
after_date = last_monday_datetime # Show run after this date   (YYYY, MM, DD)  
before_date = today_datetime # Show run before this date

# Zones limits
zone_1 = 144
zone_2 = 158
zone_3 = 172
zone_4 = 186

def read_text_from_file(file_name: str) -> str:
    """
    Read a text from a single line txt file and return it
    parameter
        str file_name : Name of the file (with the extension in the name)
    return 
        str text : the one line text from the file file_name
    """
    with open(file_name) as file:
        text = file.readline()
    return text

client_id = int(read_text_from_file('client_id.txt'))
client_secret = read_text_from_file('client_secret.txt')
refresh_token = read_text_from_file('refresh_token.txt')

print('\n \n', '----- CONNECTION TO STRAVA SERVER DEBUG -----')
###----- ACCESS TOKEN -----###
def get_access_token() -> str:
    """
    Call to the API to get the access token
    return 
        str access token
    """
    print('Refreshing access token...\n')

    API_url_for_auth_token = "https://www.strava.com/oauth/token"
    payload_for_auth_token = {
        "client_id": client_id, # From my account
        "client_secret": client_secret, # From my account
        "refresh_token": refresh_token, # See https://www.youtube.com/watch?v=sgscChKfGyg to see how to get a refresh token
        "grant_type": "refresh_token"
        #"code":"",
        #"grant_type": "authorization_code"
    }
    
    r = requests.post(API_url_for_auth_token, data=payload_for_auth_token)
    if r.status_code == 200:
        api_access_token = r.json()['access_token']
        print(f"The access token is {api_access_token}")
    else:
        print("Erreur, code de statut ", r.status_code)

    return api_access_token


###----- GET LIST OF ACTIVITIES -----###
def get_all_activities(api_access_token: str):
    """
    Call to the API to get the list of all the recorded activities
    parameter
        str api_access_token
    return 
        json file 
    """
    print('Getting all activities')
    API_url_for_activities = "https://www.strava.com/api/v3/athlete/activities"
    header = {"Authorization": "Bearer " + api_access_token}
    param = {'per_page': 200, 'page': 1}
    
    r = requests.get(API_url_for_activities, headers=header, params=param)
    json_data = r.json() # Convert the server answer in json format
    with open('data.json', 'w') as file:
        json.dump(json_data, file) # Write the json file in the current directory
    return json_data

###----- GET A RUN DATAS FROM A RUN_ID -----###
def get_activity_by_id(api_access_token: str, id: int):
    """
    Call to the API to get details on an activity from its id
    parameters
        str api_access_token  
    return 
        json file
    """
    API_url_for_activities = "https://www.strava.com/api/v3/activities/" + str(id)
    header = {"Authorization": "Bearer " + api_access_token}
    param = {"id": id}

    r = requests.get(API_url_for_activities, headers=header, params=param)
    json_data = r.json()
    with open('run_data.json', 'w') as f:
        json.dump(json_data, f)
    return json_data

def extract_datas_from_activities(activities_id: list) -> dict:
    """
    Extract informations from activities
    parameters
        str activities_id : id of the activity 
    return 
        dict which contains all the extracted informations
    """
    
    list_zone_1 = []; list_zone_2 = []; list_zone_3 = []; list_zone_4 = []; list_zone_5 = [] 
    list_of_HR = []
    list_of_elapsed_time = []
    list_of_distances = []
    result = dict()

    compteur = 0
    i = 0
    for id in activities_id:
        # Get datas from one run
        json_run_data = get_activity_by_id(api_access_token, id) 
        
        compteur +=1
        print(f'Analyse du run n°{compteur} / {len(activities_id)} ')
        
        # Sorting HR in the 5 zones
        for run_data in json_run_data['splits_metric']:
            try:
                HeartRate = run_data['average_heartrate']
                elapsed_time = run_data['elapsed_time']
                distance = run_data['distance']
                list_of_HR.append(HeartRate) 
                list_of_elapsed_time.append(elapsed_time) 
                list_of_distances.append(distance) 

                if HeartRate <= zone_1:
                    list_zone_1.append(list_of_elapsed_time[i])
                elif HeartRate > zone_1 and HeartRate <= zone_2:
                    list_zone_2.append(list_of_elapsed_time[i])
                elif HeartRate > zone_2 and HeartRate <= zone_3:
                    list_zone_3.append(list_of_elapsed_time[i])
                elif HeartRate > zone_3 and HeartRate <= zone_4:
                    list_zone_4.append(list_of_elapsed_time[i])
                else:
                    list_zone_5.append(list_of_elapsed_time[i])
                i += 1
            except Exception as e:
                print(f'An error occured while getting datas on run {compteur} / {len(activities_id)}')
                print(e)

    result['total_time'] = sum(list_of_elapsed_time)
    result['total_distance'] = sum(list_of_distances)
    result['times_in_zone_1'] = list_zone_1
    result['times_in_zone_2'] = list_zone_2
    result['times_in_zone_3'] = list_zone_3
    result['times_in_zone_4'] = list_zone_4
    result['times_in_zone_5'] = list_zone_5
            
    return result

def check_date(date: str, format = 'Strava', before_date_param: datetime = before_date, after_date_param: datetime = after_date) -> bool:
    """
    Check if a date is in the specified segment [after_date_param-----date-----before_date_param]
    parameters
        str date : Date to check. If format is set to 'datetime', date object has to be of type datetime
        datetime before_date_param : The right part of the segment
        datetime after_date_param : The left part of the segment
    return 
        bool True if the date is in the segment
    """
    if format == 'Strava':
        year_of_run = int(date[0:4])
        month_of_run = int(date[5:7])
        day_of_run = int(date[8:10])
        date_of_run = datetime(year_of_run, month_of_run, day_of_run)
    elif format == 'datetime':
        date_of_run = date

    if date_of_run >= after_date_param and date_of_run <= before_date_param:
        return True
    return False

def make_all_sports_stats(bef_date: datetime=before_date, aft_date: datetime=after_date) -> dict:
    """
    Makes some time stats from the list of all activities
    parameters
        datetime bef_date
        datetime aft_date
    return 
        dict containing datas of interest
    """
    
    run_time = []
    swim_time = []
    bike_time = []
    otherSport_time = []

    run_distances = []
    swim_distances = []
    bike_distances = []

    days_of_activities = []
    times_of_activities = []
   
    result = dict()

    data = pd.read_json('data.json')

    i = 0
    list_of_dates = data['start_date'].values.tolist()
    list_of_sports_types = data['sport_type'].values.tolist()
    list_of_distances = data['distance'].values.tolist()
    print(f'')
    index_for_sum = 0
    for time in data['moving_time']:
        if check_date(date=list_of_dates[i], format='Strava', before_date_param=bef_date, after_date_param=aft_date):
            # Sorting times in its corresponding activity 
            if list_of_sports_types[i] == 'Run':
                run_time.append(time)
                run_distances.append(list_of_distances[i])
            elif list_of_sports_types[i] == 'Swim':
                swim_time.append(time)
                swim_distances.append(list_of_distances[i])
            elif list_of_sports_types[i] == 'Ride':
                bike_time.append(time)
                bike_distances.append(list_of_distances[i])
            else:
                otherSport_time.append(time)

            # Store the duration of activity for each activity
            times_of_activities.append(round(time/60, 1))
            days_of_activities.append(int(list_of_dates[i][8:10]))
        i += 1
    
    cumuled_sum_time_of_act = []
    times_of_activities_reversed = times_of_activities[::-1]
    csum = 0
    for j in range(len(times_of_activities)):
        csum += times_of_activities_reversed[j]
        cumuled_sum_time_of_act.append(round(csum, 1))

    result['total_run_time'] = round(sum(run_time)/60, 1)
    result['total_swim_time'] = round(sum(swim_time)/60, 1)
    result['total_bike_time'] = round(sum(bike_time)/60, 1)
    result['otherSport_time'] = round(sum(otherSport_time)/60, 1)
    result['times_of_activities'] = sum(times_of_activities)

    result['total_run_distance'] = round(sum(run_distances)/1000, 1)
    result['total_bike_distance'] = round(sum(bike_distances)/1000, 1)
    result['total_swim_distance'] = round(sum(swim_distances)/1000, 1)

    result['sum_times_of_activities'] = cumuled_sum_time_of_act
    result['days_of_activities'] = days_of_activities

    print(f' run distances : {run_distances}')

    return result

def min_to_hhmm(minutes: int) -> str:
    minutes = int(minutes)
    hh = minutes // 60
    mm = minutes - hh*60
    return f'{hh}h{mm}'


fig, ax = plt.subplots(2, 2)
###----- TOP LEFT CHART : TIME IN ZONES -----###
# GET ALL ACTIVITES TO OBTAIN RUN IDs
api_access_token = get_access_token() # Request the access token from the API
all_activities_in_raw_data = get_all_activities(api_access_token) # Request the list of all activities, save it in "data.json" and return the json file

df_activities = pd.read_json('data.json') # Store all activities data in a pandas dataframe from the data.json file

# List of the running id
# Filter dataframe to conserv only runnings
running_activities = df_activities.loc[df_activities['type'] == 'Run'] # Filter the dataframe to conserv only runs
list_of_running_activities_id = running_activities['id'].values.tolist() # Store the running id in a python list

#Filter dataframe to conserv only date of interest
list_of_dates = running_activities['start_date'].values.tolist()
filtered_list_of_running_activities_id = []
for i in range(len(list_of_dates)):
    # If the date is ok, store the id of the run in a python list
    if(check_date(list_of_dates[i])):
        filtered_list_of_running_activities_id.append(list_of_running_activities_id[i])

# Get hr from runs 
result = extract_datas_from_activities(filtered_list_of_running_activities_id)

print('\n \n', '----- TOP LEFT CHART -----')
print(f'Analyse des runs entre le {after_date} et le {before_date} \n')

print(f"Temps total de course : {timedelta(seconds=result['total_time'])}")
print(f"Distance totale de course : {round(result['total_distance'] / 1000, 1)} kms \n")

time_in_zones = [sum(result['times_in_zone_1']), sum(result['times_in_zone_2']), sum(result['times_in_zone_3']), sum(result['times_in_zone_4']), sum(result['times_in_zone_5'])]

# print(f"Temps en zone 1 : {timedelta(seconds=time_in_zones[0])} / {timedelta(seconds=result['total_time'])}, soit {round(time_in_zones[0]/result['total_time'] * 100)} %")
# print(f"Temps en zone 2 : {timedelta(seconds=time_in_zones[1])} / {timedelta(seconds=result['total_time'])}, soit {round(time_in_zones[1]/result['total_time'] * 100)} %")
# print(f"Temps en zone 3 : {timedelta(seconds=time_in_zones[2])} / {timedelta(seconds=result['total_time'])}, soit {round(time_in_zones[2]/result['total_time'] * 100)} %")
# print(f"Temps en zone 4 : {timedelta(seconds=time_in_zones[3])} / {timedelta(seconds=result['total_time'])}, soit {round(time_in_zones[3]/result['total_time'] * 100)} %")
# print(f"Temps en zone 5 : {timedelta(seconds=time_in_zones[4])} / {timedelta(seconds=result['total_time'])}, soit {round(time_in_zones[4]/result['total_time'] * 100)} %")


data_to_plot = []
labels = 'zone 1 [0-' + str(zone_1) + ']', 'Z2, E.F. [' + str(zone_1) + '-' + str(zone_2) + ']', 'Z3/S.V.1, E.A. [' + str(zone_2) + '-' + str(zone_3) + ']', 'Z4/S.V.2, Seuil aérobie [' + str(zone_3) + '-' + str(zone_4) + ']', 'Z5, Seuil anaérobie [' + str(zone_4) + '-' + '220]'
for time in time_in_zones:
    data_to_plot.append(time)

if data_to_plot != [0, 0, 0, 0, 0]:
    ax[0, 0].pie(data_to_plot, labels=labels, autopct='%1.1f%%', colors=['blue', 'green', 'orange', 'red', 'purple'], shadow=True)
    ax[0, 0].set_title('Du ' + str(after_date.day) + '/' + str(after_date.month) + ' au ' + str(before_date.day) + '/' + str(before_date.month) +' | ' + str(timedelta(seconds=result['total_time'])) + ' | ' + str(round(result['total_distance']/1000, 1)) + 'kms')
else:
    ax[0, 0].text(0.5, 0.5, 'No run this week yet !', horizontalalignment = 'center', verticalalignment = 'center')

###----- TOP RIGHT CHART : THIS WEEK ACTIVITIES -----###
# Get this week activities time data
# From the last sunday to today (both are include)

this_wk_act = make_all_sports_stats(aft_date=last_monday_datetime, bef_date=today_datetime)
from_begin_of_month_act = make_all_sports_stats(aft_date=datetime(today.year, today.month, 1), bef_date=today_datetime)
last_month_act = make_all_sports_stats(aft_date=datetime(today.year, today.month-1, 1), bef_date=datetime(today.year, today.month-1, 31))
last_wk_act = make_all_sports_stats(aft_date=scnd_last_monday_datetime, bef_date=last_sunday_datetime)


if this_wk_act['total_run_time'] > 0 or this_wk_act['total_swim_time'] > 0 or this_wk_act['total_bike_time'] > 0 :
    ax[0, 1].set_ylim(0, max(this_wk_act['total_run_time'], this_wk_act['total_bike_time'], this_wk_act['total_swim_time']) + 20)
    ax[0, 1].bar(["Run", "Swim", "Bike", "Other"], [this_wk_act['total_run_time'], this_wk_act['total_swim_time'], this_wk_act['total_bike_time'], this_wk_act['otherSport_time']])
    ax[0, 1].set_title(f"{len(this_wk_act['days_of_activities'])} activités cette semaine ({min_to_hhmm(this_wk_act['times_of_activities'])})")
    
    ax[0, 1].text(-0.1, this_wk_act['total_run_time'] + 2, this_wk_act['total_run_distance'])
    ax[0, 1].text(0.9, this_wk_act['total_swim_time'] + 2, this_wk_act['total_swim_distance'])
    ax[0, 1].text(1.9, this_wk_act['total_bike_time'] + 2, this_wk_act['total_bike_distance'])
else:
    ax[0, 1].text(0.5, 0.5, 'No activity this week yet !', horizontalalignment = 'center', verticalalignment = 'center')


###----- BOTTOM LEFT CHART : THIS WEEK VS THIS MONTH ACTIVITIES CURVE -----###
# From the 1st of the month to the last day of the month (both include)
ax[1, 0].plot(from_begin_of_month_act['days_of_activities'][::-1], from_begin_of_month_act['sum_times_of_activities'], 'orange')

ax[1, 0].plot(last_month_act['days_of_activities'][::-1], last_month_act['sum_times_of_activities'], 'blue')
ax[1, 0].set_title(f"{len(from_begin_of_month_act['days_of_activities'])} activités depuis le 1er du mois ({min_to_hhmm(from_begin_of_month_act['times_of_activities'])})")



###----- BOTTOM RIGHT CHART : LAST WEEK -----###
# From the last monday to the last sunday (both include)
if last_wk_act['total_run_time'] > 0 or last_wk_act['total_swim_time'] > 0 or last_wk_act['total_bike_time'] > 0 :
    ax[1, 1].set_ylim(0, max(last_wk_act['total_run_time'], last_wk_act['total_bike_time'], last_wk_act['total_swim_time'])+20)
    ax[1, 1].bar(["Run", "Swim", "Bike", "Other"], [last_wk_act['total_run_time'], last_wk_act['total_swim_time'], last_wk_act['total_bike_time'], last_wk_act['otherSport_time']])
    ax[1, 1].set_title(f"{len(last_wk_act['days_of_activities'])} activités la semaine passée ({min_to_hhmm(last_wk_act['times_of_activities'])})")
    
    ax[1, 1].text(-0.1, last_wk_act['total_run_time'] + 2, last_wk_act['total_run_distance'])
    ax[1, 1].text(0.9, last_wk_act['total_swim_time'] + 2, last_wk_act['total_swim_distance'])
    ax[1, 1].text(1.9, last_wk_act['total_bike_time'] + 2, last_wk_act['total_bike_distance'])
else:
    ax[1, 1].text(0.5, 0.5, 'No activity last week !', horizontalalignment = 'center', verticalalignment = 'center')


print('\n \n', '----- DATE DEBUG -----')
print(f'Lundi de la semaine passée : {scnd_last_monday_datetime} | Dimanche de la semaine passée :  {last_sunday_datetime}')
print(f"Etendue des dates de la semaine passée contenant une activité {last_wk_act['days_of_activities'][::-1]}")

print(f'Dates de la semaine courante : {last_monday_datetime} au {today_datetime}')
print(f"Etendue des dates de la semaine courante contenant une activité  {this_wk_act['days_of_activities'][::-1]}")

print(f"Etendue des dates du mois courant contenant une activité {from_begin_of_month_act['days_of_activities'][::-1]}")

plt.show()