#!/usr/bin/env python
# coding: utf-8

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import json
from collections import defaultdict
from datetime import datetime
import os
from itertools import chain

import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import PathPatch
import matplotlib.image as mpimg

import folium
from folium import plugins
import seaborn as sns
import plotly.graph_objects as go

plt.rcParams.update({'xtick.labelsize': 14, 'ytick.labelsize': 14, 'axes.labelsize' : 15, 'axes.titlesize' : 20})

SAVE = 'graphs/'
if not os.path.exists(SAVE):
    os.mkdir(SAVE)


######################################## data cleaning and organization

def read_data():
    beers = {} # initizalizing dict
    date_badges = defaultdict(list) # default dict of list
    single_badges = []
    level_badges = {}
    brewery_locations = {} # dict for brewery locations
    venue_locations = {}
    top_descriptions = ['reached the top!']
    badge_urls = {}

    with open('data/untappd_checkins.json') as json_file: # read in data from untappd api
        data = json.load(json_file)[::-1]

    # fields to save
    for checkin in data:
        beers[checkin['checkin_id']] = {}
        beers[checkin['checkin_id']]['date_GMT'] = checkin['created_at']
        beers[checkin['checkin_id']]['rating'] = checkin['rating_score']
        beers[checkin['checkin_id']]['style'] = checkin['beer']['beer_style']
        beers[checkin['checkin_id']]['abv'] = checkin['beer']['beer_abv']
        beers[checkin['checkin_id']]['beer'] = checkin['beer']['beer_name']
        beers[checkin['checkin_id']]['brewery_name'] = checkin['brewery']['brewery_name']
        beers[checkin['checkin_id']]['brewery_country'] = checkin['brewery']['country_name'].upper()
        beers[checkin['checkin_id']]['brewery_state'] = checkin['brewery']['location']['brewery_state'].upper()
        beers[checkin['checkin_id']]['brewery_city'] = checkin['brewery']['location']['brewery_city'].upper()
        beers[checkin['checkin_id']]['number_badges'] = checkin['badges']['count']

        try:
            beers[checkin['checkin_id']]['venue_name'] = checkin['venue']['venue_name']
            beers[checkin['checkin_id']]['venue_type'] = checkin['venue']['primary_category']
        except:
            beers[checkin['checkin_id']]['venue_name'] = None
            beers[checkin['checkin_id']]['venue_type'] = None


        # save brewery locations if not in the brewery location dictionary already
        if checkin['brewery']['brewery_name'] not in brewery_locations:
            brewery_locations[checkin['brewery']['brewery_name']] = [float(checkin['brewery']['location']['lat']),
                                                            (checkin['brewery']['location']['lng'])]

        # save venue locations if not in the venue location dictionary already
        if beers[checkin['checkin_id']]['venue_name'] != None:
            if checkin['venue']['venue_name'] not in venue_locations:
                venue_locations[checkin['venue']['venue_name']] = [float(checkin['venue']['location']['lat']),
                (checkin['venue']['location']['lng'])]

        # save badge dates and level of each badge
        if checkin['badges']['count'] > 0: # if there were badges in the checkin
            temp = checkin['badges']['items'] # save the badges       
            for badge in temp: # for each badge        
                # save the date and name and description
                date = badge['created_at'] 
                name = badge['badge_name'].strip()
                badge_urls[name.split(' (Level')[0]] = 'data/badge_images/' + badge['badge_image']['lg'].split('/')[-1] 
                description = badge['badge_description']
                if 'Level' in name:
                    name,level = name.split(' (Level ')
                    level = int(level[:-1])
                    level_badges[name] = level
                    date_badges[name].append(date) # append the date to the badges dictionary 
                elif 'Level ' in  description:
                    level_badges[name] = 1
                    date_badges[name].append(date) # append the date to the badges dictionary 
                else: # if no level in name
                    single_badges.append(name)

    beers = pd.DataFrame(beers).T # turn beer dictionary into pandas dataframe

    # convert rating and abv to floats
    beers["rating"] = beers.rating.astype(float)
    beers["abv"] = beers.abv.astype(float)

    # convert dates to datetime
    beers['date_GMT'] = pd.to_datetime(beers['date_GMT'])
    beers = beers.sort_values(['date_GMT'], ascending = False)

    # convert badge dates to datetime
    for name,level_date in date_badges.items():
        date_badges[name] = sorted([datetime.strptime(x, '%a, %d %b %Y %H:%M:%S %z') for x in level_date])
    
    del level_badges['Land of the Free ']
    del level_badges['I Believe in IPA!']
    del level_badges['New Brew Thursday']

    return beers, date_badges, level_badges, single_badges, brewery_locations, venue_locations, badge_urls

def read_unique_beer_data():
    unique = {} # initizalizing dict

    with open('data/untappd_unique_beer.json') as json_file: # read in data from untappd api
        data = json.load(json_file)

    # fields to save
    for checkin in data:
        unique[checkin['first_checkin_id']] = {}
        unique[checkin['first_checkin_id']]['date'] = datetime.strptime(checkin['first_created_at'],'%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
        unique[checkin['first_checkin_id']]['rating'] = checkin['rating_score']
        unique[checkin['first_checkin_id']]['style'] = checkin['beer']['beer_style']
        unique[checkin['first_checkin_id']]['abv'] = checkin['beer']['beer_abv']
        unique[checkin['first_checkin_id']]['beer'] = checkin['beer']['beer_name']
        unique[checkin['first_checkin_id']]['ibu'] = checkin['beer']['beer_ibu']


    unique = pd.DataFrame(unique).T # turn beer dictionary into pandas dataframe

    # convert rating and abv to floats
    unique["rating"] = unique.rating.astype(float)
    unique["abv"] = unique.abv.astype(float)
    unique["ibu"] = unique.ibu.astype(float)
    unique.set_index('date', inplace = True)
    unique.index = pd.to_datetime(unique.index)
    unique['hour'] = unique.index.hour
    unique['day'] = unique.index.day
    unique['month'] = unique.index.month
    unique['year'] = unique.index.year
    unique['day_of_week'] = unique.index.to_series().dt.weekday_name.values

    return unique

######################################## 

def most_drunk_beers(beers):
    '''
    most drunk beers
    '''
    fig, ax = plt.subplots(figsize = (12,8))

    # group data by beer, count occrence, sort, show top 15
    occurrence = pd.DataFrame(beers.groupby('beer')['beer'].count().sort_values(ascending=False)[0:15])
    
    # plot
    sns.barplot(x='beer', y=occurrence.index, palette="rocket", ax=ax, data = occurrence)

    ax.set_ylabel('Beer')
    ax.set_xlabel('Frequency')
    ax.set_title('Most Drunk Beers');

    plt.tight_layout()
    plt.savefig(SAVE + 'beer_occurence.png', dpi = 300)

def rating_frequency(beers):
    '''
    rating frequency 
    '''
    fig, ax = plt.subplots(figsize = (12,8))

    # make a histogram of rating
    ratings = pd.DataFrame(beers.groupby('rating').size())
    pal = sns.color_palette("rocket", len(ratings))
    rank = ratings[0].values.argsort().argsort()
    sns.barplot(x=ratings.index, y=0, palette= np.array(pal[::-1])[rank], ax=ax, data = ratings)
    ax.set_ylabel('Frequency');
    ax.set_xlabel('Rating')
    ax.set_title('Rating Histogram')

    plt.tight_layout()
    plt.savefig(SAVE + 'rating_frequency.png', dpi = 300)

def style_frequency(beers):
    '''
    style frequency 
    '''
    fig, ax = plt.subplots(figsize = (8,8))

    # group data by style, count occurence, sort by occurence and show top 15
    occurence = pd.DataFrame(beers.groupby('style').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)[0:15]
    # plot
    sns.barplot(x='Frequency', y=occurence.index, palette="rocket", ax=ax, data = occurence)
    
    ax.set_ylabel('Frequency');
    ax.set_ylabel('Beer Style');
    ax.set_title('Most Drunk Styles')

    plt.tight_layout()
    plt.savefig(SAVE + 'Style_frequency.png', dpi = 300)

def ABV_frequency(beers):
    '''
    ABV frequency 
    '''
    fig, ax = plt.subplots(figsize = (6,6))

    # get abvs
    abvs = list(beers['abv'].values)

    # plot histogram    
    sns.distplot(a= abvs, ax=ax, kde=False)
    
    ax.set_xlabel('ABV')
    ax.set_ylabel('Frequency')
    ax.set_title('ABV Histogram');

    plt.tight_layout()
    plt.savefig(SAVE + 'ABV_frequency.png', dpi = 300)

def brewery_information(beers):
    '''
    brewing information 
    '''
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize = (18,12))

    # for the brewery name, city, state, and country
    # groupby the filter, count occurence, sort by occurence, and then plot top 15
    name = pd.DataFrame(beers.groupby('brewery_name').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)[0:15]
    sns.barplot(x = 'Frequency', y = name.index, data = name, ax = axes[0,0], palette = 'rocket')

    city = pd.DataFrame(beers.groupby('brewery_city').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)[0:15]
    sns.barplot(x = 'Frequency', y = city.index, data = city, ax = axes[1,0], palette = 'rocket')

    state = pd.DataFrame(beers.groupby('brewery_state').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)[0:15]
    sns.barplot(x = 'Frequency', y = state.index, data = state, ax = axes[0,1], palette = 'rocket')
    
    country = pd.DataFrame(beers.groupby('brewery_country').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)
    sns.barplot(x = 'Frequency', y = country.index, data = country, ax = axes[1,1], palette = 'rocket')

    axes[0,1].set_title('States')
    axes[0,0].set_title('Most Drunk Breweries')
    axes[1,0].set_title('Cities')
    axes[1,1].set_title('Countries')
    axes[1,1].set_xscale('log')
    
    axes[0,1].set_ylabel('Frequency');
    axes[0,0].set_xlabel('');
    axes[1,0].set_xlabel('');
    axes[1,1].set_xlabel('');
        
    for ax in axes.flatten():
        ax.set_ylabel('');
        
    plt.tight_layout()
    plt.savefig(SAVE + 'brewery_info.png', dpi = 300)

def badges_per_checkin(beers):
    '''
    numebr of badges per checkin
    '''

    fig, ax = plt.subplots(figsize = (5,5))

    # group number of badges per checkin and count the number of occurences
    # store as a zipped list
    zipped = list(beers.groupby('number_badges').size().iteritems())
    # randomly shuffle the list so that the pie chart changes order each time
    random.shuffle(zipped)
    # save number of badges as labels and occurence as size
    labels,sizes = map(list, zip(*zipped))

    # print pie chart
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance = 0.8, labeldistance = 0.5)
    #draw circle
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    ax.axis('equal') 
    ax.set_title('Number of Badges per Checkin')

    plt.tight_layout()
    plt.savefig(SAVE + 'badge_checkin.png', dpi = 300)

def beer_style_by_rating(beers):
    '''
    Top and Bottom beer styles by rating
    '''

    fig, ax = plt.subplots(figsize = (18,10));

    # group the data by style and only keep styles with at least 5 occurrences
    style_amount_filter = beers.groupby("style").filter(lambda x: x['style'].size > 5)

    # filter the styles by rating, sort by median, and then keep top 15
    abvs_to_keep = pd.DataFrame(style_amount_filter.groupby('style')['rating'].apply(np.median)).sort_values('rating', ascending=False)[0:15].index.tolist()
    # filter the styles by rating, sort by median, and then keep bottom 15
    abvs_to_keep.extend(pd.DataFrame(style_amount_filter.groupby('style')['rating'].apply(np.median)).sort_values('rating', ascending=True)[0:15].index)

    # only keep styles that are in the top and bottom 15
    abv_beers = style_amount_filter[style_amount_filter['style'].isin(abvs_to_keep)]

    # sort plot by top 15 and then bottom 15
    meds = abv_beers.groupby('style').apply(np.mean).sort_values(by = 'rating', ascending = False)
    abv_beers['style'] = pd.Categorical(abv_beers['style'], meds.index)
    abv_beers.sort_values("style", inplace = True)
    sns.boxplot(x="style", y="rating", data=abv_beers, ax = ax, palette = 'rocket')
    

    plt.suptitle("");
    ax.set_title('Top and Bottom 15 Styles (>5) by Rating')
    ax.set_ylabel('Rating')
    ax.set_xlabel('Beer Style')
    ax.set_xticklabels(ax.get_xticklabels(), rotation = 90);
    ax.grid(axis='y', alpha=0.75)

    plt.axvline(x=14.5, color = 'purple')
    colors = ['green'] * 15 + ['red'] * 15
    for xtick, color in zip(ax.get_xticklabels(), colors):
        xtick.set_color(color)

    for i,artist in enumerate(ax.artists):
        # Set the linecolor on the artist to the facecolor, and set the facecolor to None
        col = artist.get_facecolor()
        artist.set_edgecolor(col)
        artist.set_facecolor('None')

        # Each box has 6 associated Line2D objects (to make the whiskers, fliers, etc.)
        # Loop over them here, and use the same colour as above
        for j in range(i*6,i*6+6):
            line = ax.lines[j]
            line.set_color(col)
            line.set_mfc(col)
            line.set_mec(col)

    plt.axvline(x=14.5, color = 'purple')
    plt.tight_layout()
    plt.savefig(SAVE + 'style_by_rating.png', dpi = 300)   

def beer_style_by_abv(beers):
    '''
    Top and Bottom beer styles by abv
    '''

    fig, ax = plt.subplots(figsize = (18,10));

    # group the data by style and only keep styles with at least 5 occurrences
    style_amount_filter = beers.groupby("style").filter(lambda x: x['style'].size > 5)

    # filter the styles by abv, sort by median, and then keep top 15
    abvs_to_keep = pd.DataFrame(style_amount_filter.groupby('style')['abv'].apply(np.median)).sort_values('abv', ascending=False)[0:15].index.tolist()
    # filter the styles by abv, sort by median, and then keep bottom 15
    abvs_to_keep.extend(pd.DataFrame(style_amount_filter.groupby('style')['abv'].apply(np.median)).sort_values('abv', ascending=True)[0:15].index)

    # only keep styles that are in the top and bottom 15
    abv_beers = style_amount_filter[style_amount_filter['style'].isin(abvs_to_keep)]

    # sort plot by top 15 and then bottom 15
    meds = abv_beers.groupby('style').apply(np.mean).sort_values(by = 'abv', ascending = False)
    abv_beers['style'] = pd.Categorical(abv_beers['style'], meds.index)
    abv_beers.sort_values("style", inplace = True)
    sns.boxplot(x="style", y="abv", data=abv_beers, ax = ax, palette = 'rocket')
    
    plt.suptitle("");
    ax.set_title('Top and Bottom 15 Styles (>5) by ABV')
    ax.set_ylabel('ABV')
    ax.set_xlabel('Beer Style')
    ax.set_xticklabels(ax.get_xticklabels(), rotation = 90);
    ax.grid(axis='y', alpha=0.75)
    
    plt.axvline(x=14.5, color = 'purple')
    colors = ['green'] * 15 + ['red'] * 15
    for xtick, color in zip(ax.get_xticklabels(), colors):
        xtick.set_color(color)
    
    for i,artist in enumerate(ax.artists):
        # Set the linecolor on the artist to the facecolor, and set the facecolor to None
        col = artist.get_facecolor()
        artist.set_edgecolor(col)
        artist.set_facecolor('None')

        # Each box has 6 associated Line2D objects (to make the whiskers, fliers, etc.)
        # Loop over them here, and use the same colour as above
        for j in range(i*6,i*6+6):
            line = ax.lines[j]
            line.set_color(col)
            line.set_mfc(col)
            line.set_mec(col)

    plt.tight_layout()
    plt.savefig(SAVE + 'style_by_abv.png', dpi = 300)

def inter_drink_time(beers, unique):

    fig, ax = plt.subplots(figsize = (10,8));
    
    dates = pd.Series(unique.index)
    # take dataframe of time and find difference between the times
    # find total number of seconds in the time difference
    unique_seconds_iet = (dates - dates.shift(-1))[:-1].apply(lambda x: x.total_seconds())
    total_seconds_iet = (beers['date_GMT'] - beers['date_GMT'].shift(-1))[:-1].apply(lambda x: x.total_seconds())
    # make lists of time labels and number of seconds in each time label
    ticks = [3600, 86400, 259200, 432000, 604800]
    labels =  ["Hour",'1 Day', '3 Days','5 Days', 'Week']

    maxs  = max(max(unique_seconds_iet.values),max(total_seconds_iet.values))
    mins  = min(min(unique_seconds_iet.values),min(total_seconds_iet.values))
    bins = np.linspace(mins,maxs,40)

    # plot histogrma of secoonds
    sns.distplot(a=total_seconds_iet, kde = False, bins=bins, label = 'All Beers', ax = ax)
    sns.distplot(a=unique_seconds_iet, kde = False, bins=bins, label = 'Unique Beers',ax = ax)
    
    ax.set_ylabel('Frequency')
    ax.set_xlabel('Time')
    ax.set_title('Inter-Drink Time')
    # set ticks to the custom time labels
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation = 25)
    plt.yscale('log')
    plt.legend(fontsize = 20)

    plt.tight_layout()
    plt.savefig(SAVE + 'inter_drink_time.png', dpi = 300)

def time_to_badge(date_badges):

    fig, ax = plt.subplots(figsize = (18,10));

    # for each badge of at least level 10, 
    # find the difference in times of levelling up and convert from seconds to days.
    # store as a list of lists. 
    # flatten list of lists and turn into pandas datafrme
    badges_iet = pd.DataFrame(
        [ind for flatten in 
         [[[x,(t - s).total_seconds() / (60 * 60 * 24)] for s, t in zip(date_badges[x], date_badges[x][1:])] 
          for x in date_badges.keys() if len(date_badges[x]) > 10]
         for ind in flatten],
        columns = ['Badge','Time']
    )

    # group the data by badge, sort by median time
    badges_to_keep = pd.DataFrame(badges_iet.groupby('Badge')['Time'].apply(np.median)).sort_values('Time', ascending=True).index.tolist()
    badges_iet[badges_iet['Badge'].isin(badges_to_keep)]
    
    # sort plot by fastest obtained badges
    meds = badges_iet.groupby('Badge').apply(np.mean).sort_values(by = 'Time', ascending = True)
    badges_iet['Badge'] = pd.Categorical(badges_iet['Badge'], meds.index)
    badges_iet.sort_values("Badge", inplace = True)
    sns.boxplot(x="Time", y="Badge", data=badges_iet, ax = ax, palette = 'rocket_r')

    plt.suptitle("");
    ax.set_title('Amount of Time to Level Up a Badge (> Level 10)')
    ax.set_xlabel('Days')


    plt.tight_layout()
    plt.savefig(SAVE + 'badge_level_up.png', dpi = 300)

def brewery_heatmap(brewery_locations):
    # get coordinates
    coords = brewery_locations.values()

    # starting coordinates
    start = [20, -30]
    zoom = 2
    # make list of lists of lats/longs
    coords = list(zip([x[0] for x in coords],[x[1] for x in coords]))
    # make map
    m = folium.Map(location=start, zoom_start=zoom,)
    # plot heatmap
    m.add_child(plugins.HeatMap(coords, radius=15))
    m.save(outfile= SAVE + "brewery_heatmap.html")

def brewery_popup(brewery_locations, beers):

    # count occurence of breweries
    frequency = beers.groupby('brewery_name').size().to_dict()

    coords = brewery_locations.values()
    # starting point of map
    start = [20, -30]
    zoom = 2
    coords = list(zip([x[0] for x in coords],[x[1] for x in coords]))
    # start map
    m = folium.Map(location=start, zoom_start=zoom)

    # for each brewery, add a popup wiith name, checkins, and checkin dates
    # add popup to map
    for name,loc in brewery_locations.items():
        prop = name + '<br>' + str(frequency[name]) + ' checkins <br>First check in: ' + str(beers[beers.brewery_name == name]['date_GMT'].min().date()) + '<br>Last check in: ' + str(beers[beers.brewery_name == name]['date_GMT'].max().date())
        folium.Circle([loc[0],loc[1]], radius = frequency[name] * 10000, fill=True, color = 'crimson', fill_color = 'crimson').add_child(folium.Popup(prop, min_width=200, max_width=500)).add_to(m)

    m.save(outfile= SAVE + "brewery_popup_map.html")

def common_venue_names(beers):
    fig, ax = plt.subplots(figsize = (12,12))

    # group data by style, count occurence, sort by occurence and show top 15
    venues = pd.DataFrame(beers.dropna().groupby('venue_name').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)[0:15]

    sns.barplot(x='Frequency', y=venues.index, palette="rocket", ax=ax, data = venues)
    ax.set_ylabel('Frequency');
    ax.set_ylabel('Venue');
    ax.set_title('Most Frequented Venues')

    plt.tight_layout()
    plt.savefig(SAVE + 'Venue_frequency.png', dpi = 300)

def common_venue_types(beers):
    fig, ax = plt.subplots(figsize = (8,8))

    venues = pd.DataFrame(beers.dropna().groupby('venue_type').size(), columns = ['Frequency']).sort_values('Frequency', ascending=False)

    sns.barplot(x='Frequency', y=venues.index, palette="rocket", ax=ax, data = venues)
    ax.set_ylabel('Frequency');
    ax.set_ylabel('Venue Type');
    ax.set_title('Most Frequented Venues')
    ax.set_xscale('log')

    plt.tight_layout()
    plt.savefig(SAVE + 'Venue_Type_frequency.png', dpi = 300)

def venue_heatmap(venue_locations):
    # get coordinates
    coords = venue_locations.values()

    # starting coordinates
    start = [20, -30]
    zoom = 2
    # make list of lists of lats/longs
    coords = list(zip([x[0] for x in coords],[x[1] for x in coords]))
    # make map
    m = folium.Map(location=start, zoom_start=zoom,)
    # plot heatmap
    m.add_child(plugins.HeatMap(coords, radius=15))
    m.save(outfile= SAVE + "venue_heatmap.html")

def venue_popup(venue_locations, beers):
    # count occurence of breweries
    frequency = beers.groupby('venue_name').size().to_dict()

    coords = venue_locations.values()
    # starting point of map
    start = [20, -30]
    zoom = 2
    coords = list(zip([x[0] for x in coords],[x[1] for x in coords]))
    # start map
    m = folium.Map(location=start, zoom_start=zoom)

    # for each brewery, add a popup wiith name, checkins, and checkin dates
    # add popup to map
    for name,loc in venue_locations.items():
        prop = name + '<br>' + str(frequency[name]) + ' checkins <br>First check in: ' + str(beers[beers.venue_name == name]['date_GMT'].min().date()) + '<br>Last check in: ' + str(beers[beers.venue_name == name]['date_GMT'].max().date())
        folium.Circle([loc[0],loc[1]], radius = frequency[name] * 1000, fill=True, color = 'crimson', fill_color = 'crimson').add_child(folium.Popup(prop, min_width=200, max_width=500)).add_to(m)

    m.save(outfile= SAVE + "venue_popup_map.html")

def brewery_rating(beers):

    # initialize plot
    fig, ax = plt.subplots(figsize = (10,12))

    # group by size, keep breweries with more than 5 beers
    occurences = beers.groupby('brewery_name').size()
    to_keep = occurences[occurences > 5].index

    # sort by mean rating
    ratings = pd.DataFrame(beers[beers['brewery_name'].isin(to_keep)].groupby('brewery_name')['rating'].apply(np.mean)).sort_values(by=['rating'], ascending = False)
    
    # plot
    sns.barplot(x='rating', y=ratings.index, palette= 'rocket', data = ratings, ax = ax)

    ax.set_xlabel('Rating')
    ax.set_ylabel('Brewery');
    ax.set_title('Brewery Rating')
    
    plt.tight_layout()
    plt.savefig(SAVE + 'brewery_ratings.png', dpi = 300)

def brewery_state(beers):
    states = pd.DataFrame(beers[beers['brewery_state'].str.len() == 2].groupby('brewery_state').size())
    states.columns = ['Frequency']

    fig = go.Figure(data=go.Choropleth(
        locations=states.index, # Spatial coordinates
        z = states['Frequency'].astype(float), # Data to be color-coded
        locationmode = 'USA-states', # set of locations match entries in `locations`
        colorscale = 'Blues',
        colorbar_title = "Frequency",
    ))

    fig.update_layout(
        title_text = 'Brewery State Frequency',
        geo_scope='usa',
        autosize=False,
        width=1000,
        height=1000
    )
    
    fig.write_image("graphs/brewery_state.png")  
    
def brewery_country(beers):    
    country = pd.DataFrame(beers.groupby('brewery_country').size())
    country.columns = ['Frequency']

    fig = go.Figure(data=go.Choropleth(
        locations=country.index, # Spatial coordinates
        z = country['Frequency'].astype(float), # Data to be color-coded
        locationmode = 'country names', # set of locations match entries in `locations`
        colorscale = 'Reds',
        colorbar_title = "Frequency",
    ))

    fig.update_layout(
        title_text = 'Brewery Country Frequency',
        geo_scope='world',
        autosize=False,
        width=1000,
        height=1000
    )

    fig.write_image("graphs/brewery_country.png")

def IBU_Unique_frequency(unique):
    '''
    Unique IBU frequency 
    '''
    fig, ax = plt.subplots(figsize = (6,6))

    # get abvs
    ibu = unique['ibu']

    # plot histogram    
    sns.distplot(a= ibu, ax=ax, kde=False)
    
    ax.set_xlabel('IBU')
    ax.set_ylabel('Frequency')
    ax.set_title('Unique IBU Histogram');

    plt.tight_layout()
    plt.savefig(SAVE + 'Unique_IBU_frequency.png', dpi = 300)

def cumulative(beers,unique):
    '''
    cumulativfe beer count - total and unique
    '''
    fig, ax = plt.subplots(figsize = (12,6))

    group_u = pd.DataFrame(unique.groupby(pd.Grouper(freq = '1D')).size().cumsum())
    plt.fill_between(group_u.index, [0 for x in range(len(group_u))] , group_u[0].values, color = 'green', alpha = 0.5, label = 'Unique Beers' ) 
    group = pd.DataFrame(beers.set_index('date_GMT').groupby(pd.Grouper(freq = '1D')).size().cumsum())
    plt.fill_between(group.index, [0 for x in range(len(group))] , group[0].values, color = 'red', alpha = 0.1, label = 'All Beers' ) 
    
    ax.set_ylabel('Number of Beers')
    ax.set_title('Cumulative Beer Count')
    plt.legend(loc = 'upper left', fontsize = 20 )
    
    plt.tight_layout()
    plt.savefig(SAVE + 'cumulative.png', dpi = 300)

def ave_unique_counts(unique):
    '''
    unique beer counts
    '''
    
    fig, axes = plt.subplots(2,2, figsize = (25,25))
    
    counts = pd.DataFrame(unique.groupby(['hour']).size())
    counts.columns = ['Counts']
    pal = sns.color_palette("rocket", len(counts))
    rank = counts['Counts'].values.argsort().argsort()
    sns.barplot(x=counts.index, y="Counts", data=counts, ax = axes[0,0], palette= np.array(pal[::-1])[rank], ci = None)
    
    counts = pd.DataFrame(unique.groupby(['day']).size())
    counts.columns = ['Counts']
    pal = sns.color_palette("rocket", len(counts))
    rank = counts['Counts'].values.argsort().argsort()
    sns.barplot(x=counts.index, y="Counts", data=counts, ax = axes[0,1], palette= np.array(pal[::-1])[rank], ci = None)
    
    counts = pd.DataFrame(unique.groupby(['month']).size())
    counts.columns = ['Counts']
    pal = sns.color_palette("rocket", len(counts))
    rank = counts['Counts'].values.argsort().argsort()
    sns.barplot(x=counts.index, y="Counts", data=counts, ax = axes[1,0], palette= np.array(pal[::-1])[rank], ci = None)

    counts = pd.DataFrame(unique.groupby(['year']).size())
    counts.columns = ['Counts']
    pal = sns.color_palette("rocket", len(counts))
    rank = counts['Counts'].values.argsort().argsort()
    sns.barplot(x=counts.index, y="Counts", data=counts, ax = axes[1,1], palette= np.array(pal[::-1])[rank], ci = None)

    title = fig.suptitle('Number of Unique Beers', y = 1.05, fontsize = 35)
    axes[0,0].set_ylabel('Counts', fontsize = 30)
    axes[0,1].set_ylabel('')
    axes[1,1].set_ylabel('')
    axes[1,0].set_ylabel('')
    axes[0,0].set_xlabel('Hour', fontsize = 30)
    axes[0,1].set_xlabel('Day', fontsize = 30)
    axes[1,1].set_xlabel('Year', fontsize = 30)
    axes[1,0].set_xlabel('Month', fontsize = 30)
    
    for ax in axes.flatten():
        ax.tick_params(axis='both', which='major', labelsize=20)

    plt.tight_layout()
    plt.savefig(SAVE + 'unique_beer_count_time.png', dpi = 300,bbox_inches='tight',bbox_extra_artists=[title])

def ave_unique_rating(unique):
    '''
    unique beer rating
    '''

    fig, axes = plt.subplots(2,2, figsize = (25,25))
    
    groups = unique[['hour','rating','abv']]
    rating = pd.DataFrame(groups.groupby('hour')['rating'].apply(np.mean))
    rating = rating.to_dict()
    for x in range(24):
        if x not in rating['rating']:
            rating['rating'][x] = 0    
    rating = pd.DataFrame(rating)

    pal = sns.color_palette("rocket", len(rating))
    rank = rating['rating'].values.argsort().argsort()
    sns.barplot(x=rating.index, y="rating", data=rating, ax = axes[0,0], palette= np.array(pal[::-1])[rank], ci = None)

    axes[0,0].set_ylim(0,5)
    axes[0,0].set_ylabel('Rating')
    axes[0,0].set_xlabel('Hour')
    axes[0,0].set_title('Average Rating by Hour')  
    
    
    groups = unique[['day','rating','abv']]
    rating = pd.DataFrame(groups.groupby('day')['rating'].apply(np.mean))
    rating = rating.to_dict()
    for x in range(1,32):
        if x not in rating['rating']:
            rating['rating'][x] = 0    
    rating = pd.DataFrame(rating)

    pal = sns.color_palette("rocket", len(rating))
    rank = rating['rating'].values.argsort().argsort()
    sns.barplot(x=rating.index, y="rating", data=rating, ax = axes[0,1], palette= np.array(pal[::-1])[rank], ci = None)

    axes[0,1].set_ylim(0,5)
    axes[0,1].set_ylabel('Rating')
    axes[0,1].set_xlabel('Day')
    axes[0,1].set_title('Average Rating by Day')
    
    groups = unique[['month','rating','abv']]
    rating = pd.DataFrame(groups.groupby('month')['rating'].apply(np.mean))
    rating = rating.to_dict()
    for x in range(1,13):
        if x not in rating['rating']:
            rating['rating'][x] = 0    
    rating = pd.DataFrame(rating)

    pal = sns.color_palette("rocket", len(rating))
    rank = rating['rating'].values.argsort().argsort()
    sns.barplot(x=rating.index, y="rating", data=rating, ax = axes[1,0], palette= np.array(pal[::-1])[rank], ci = None)

    axes[1,0].set_ylim(0,5)
    axes[1,0].set_ylabel('Rating')
    axes[1,0].set_xlabel('Month')
    axes[1,0].set_title('Average Rating by Month')


    groups = unique[['year','rating','abv']]
    rating = pd.DataFrame(groups.groupby('year')['rating'].apply(np.mean))
    pal = sns.color_palette("rocket", len(rating))
    rank = rating['rating'].values.argsort().argsort()
    sns.barplot(x=rating.index, y="rating", data=rating, ax = axes[1,1], palette= np.array(pal[::-1])[rank], ci = None)

    axes[1,1].set_ylim(0,5)
    axes[1,1].set_ylabel('Rating')
    axes[1,1].set_xlabel('Year')
    axes[1,1].set_title('Average Rating by Year')
    
    
    title = fig.suptitle('Average Rating for Unique Beers', y = 1.05, fontsize = 35)
    axes[0,0].set_ylabel('Rating', fontsize = 30)
    axes[0,1].set_ylabel('')
    axes[1,1].set_ylabel('')
    axes[1,0].set_ylabel('')
    axes[0,0].set_xlabel('Hour', fontsize = 30)
    axes[0,1].set_xlabel('Day', fontsize = 30)
    axes[1,0].set_xlabel('Month', fontsize = 30)
    axes[1,1].set_xlabel('Year', fontsize = 30)
    
    for ax in axes.flatten():
        ax.tick_params(axis='both', which='major', labelsize=20)

    plt.tight_layout()
    plt.savefig(SAVE + 'unique_beer_rating_time.png', dpi = 300, bbox_inches='tight',bbox_extra_artists=[title])

def unique_rating_day_of_wekk(unique):
    '''
    unique beer rating by day
    '''

    fig, ax = plt.subplots(figsize = (12,8))

    occurrence = pd.DataFrame(unique.groupby('day_of_week').size())
    occurrence.index = pd.Categorical(occurrence.index, ["Monday", "Tuesday", "Wednesday", "Thursday", 
                                                  'Friday', 'Saturday', "Sunday"])
    occurrence.sort_index(inplace = True)
    pal = sns.color_palette("rocket", len(occurrence))
    rank = occurrence[0].argsort().argsort()
    # plot
    sns.barplot(x=occurrence.index, y=0, palette=np.array(pal[::-1])[rank], ax=ax, data = occurrence)

    ax.set_ylabel('Unique Beer Count')
    ax.set_xlabel('Day of Week')
    ax.set_title('Unique Beer Count by Day of Week');

    plt.tight_layout()
    plt.savefig(SAVE + 'unique_day_of_week.png', dpi = 300)

def title_splitter_level(title, level,n):
    t = title.split()
    t = list(chain(*[t[i:i+n] + ['\n'] if len(t[i:i+n]) == n else t[i:i+n] for i in range(0, len(t), n)]))
    t = ' '.join(t).strip()
    t += '\n' + str(level) + '/100'
    return t, t.count('\n')

def title_splitter(title,n):
    t = title.split()
    t = list(chain(*[t[i:i+n] + ['\n'] if len(t[i:i+n]) == n else t[i:i+n] for i in range(0, len(t), n)]))
    t = ' '.join(t).strip()
    return t, t.count('\n')

def badge_pdf(single_badges, level_badges, badge_urls):
    order = ['Newbie','Apprentice','Journeyman', 'Artisan','Master','Legendary','Extraordinary','Elite', 'Epic','Uber']
    single = order + sorted([x for x in single_badges if x not in order], reverse = False)
    sorted_levels = sorted(list(map(list, level_badges.items())), key = lambda x: x[1], reverse = True)
    
    rows = max(len(single),len(sorted_levels)) // 5 + 1
    columns = 10
    
    fig,axes = plt.subplots(rows,columns, figsize = (27,45))
    plt.subplots_adjust(hspace = 0.5, wspace =  0.3)

    ax1 = axes[:,0:5].flatten()
    for ax in ax1: ax.axis('off')
    ax_ix = 0
    for b in single:
        try:
            img=mpimg.imread(badge_urls[b])
            imgplot = ax1[ax_ix].imshow(img)
            t,n = title_splitter(b,3)
            text = ax1[ax_ix].text(0.5,-0.1 - 0.1 * n,t,size=13, ha="center",va = 'top', transform=ax1[ax_ix].transAxes)
            ax_ix += 1
        except KeyError:
            pass

    ax2 = axes[:,5:].flatten()
    for ax in ax2: ax.axis('off')
    ax_ix = 0
    for b,level in sorted_levels:
        try:
            img=mpimg.imread(badge_urls[b])
            imgplot = ax2[ax_ix].imshow(img,  alpha = 0.2 + (1 - 0.2) / 100 * level)
            t,n = title_splitter_level(b, level,3)
            text = ax2[ax_ix].text(0.5,-0.1 - 0.1 * n,t,size=13, ha="center", va = 'center', transform=ax2[ax_ix].transAxes)
            ax_ix += 1
        except:
            pass

    my_suptitle = fig.suptitle("Unique Badges              Leveled Badges", fontsize=60, y=0.91, x = 0.51)
    plt.savefig(SAVE + 'badge_chart.pdf', dpi = 300, bbox_inches = 'tight', pad_inches = 0.5, bbox_extra_artists=[my_suptitle])
    
    

if __name__ == '__main__':
    beers, date_badges, level_badges, single_badges, brewery_locations, venue_locations, badge_urls = read_data()
    unique = read_unique_beer_data()

    most_drunk_beers(beers)
    rating_frequency(beers)
    ABV_frequency(beers)
    style_frequency(beers)
    brewery_information(beers)
    badges_per_checkin(beers)
    beer_style_by_rating(beers)
    beer_style_by_abv(beers)
    inter_drink_time(beers, unique)
    time_to_badge(date_badges)
    brewery_heatmap(brewery_locations)
    brewery_popup(brewery_locations, beers)
    common_venue_names(beers)
    common_venue_types(beers)
    venue_heatmap(venue_locations)
    venue_popup(venue_locations, beers)
    brewery_rating(beers)
    IBU_Unique_frequency(unique)
    cumulative(beers, unique)
    ave_unique_counts(unique)
    ave_unique_rating(unique)
    unique_rating_day_of_wekk(unique)
    brewery_state(beers)
    brewery_country(beers)
    badge_pdf(single_badges, level_badges, badge_urls)