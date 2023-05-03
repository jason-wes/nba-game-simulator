import pandas as pd
import time
import random as rand
#from IPython.display import clear_output
import sqlite3 as sql
import statistics as stats

def get_df_from_db(db_name, table_name, select=['*'],
                   order_by='', descending=False):
    '''Runs a select from a database and returns a DataFrame
    
    Paramaters
    ----------
    db_name: name of database
    table_name: name of table
    select: list of columns to select, default = ['*']
    order_by: column name to order by
    descending: if order by is to be set as ascending
    
    Returns
    -------
    result: DataFrame
    '''
    select_string = ', '.join(select)
    order_by_string = ''
    if order_by:
        order_by_string = " ORDER BY " + order_by
        if descending:
            order_by_string = order_by_string + " DESC"
    
    query_string = "SELECT " + select_string + " FROM " + table_name + order_by_string
    conn = None
    try:
        conn = sql.connect(db_name)
        df = pd.read_sql_query(query_string , conn)
    except Exception as e:
        print(e)
        return
    finally:
        if conn:
            conn.close
            
    return df

def calc_std_dev_and_mean(df_column):
    '''calculates the standard deviation and mean of a DataFrame column, return dict'''
    
    std_dev = df_column.std()
    mean = df_column.mean()
    stats_dict = {'std_dev': std_dev, 'mean': mean}
    return stats_dict

def get_team_stats(df, home=True):
    '''gets all the needed stats for a team for the simulator, return dict'''
    
    pace = calc_std_dev_and_mean(df['pace_home'])
    home_pts_per_possession = calc_std_dev_and_mean(df['points_per_possession_home'])
    away_pts_per_possession = calc_std_dev_and_mean(df['points_per_possession_away'])
    if home:
        stats_dict = {"pace": pace, 
                      "points_scored": home_pts_per_possession,
                      "points_given_up": away_pts_per_possession}
    else:
        stats_dict = {"pace": pace,
                      "points_scored": away_pts_per_possession,
                      "points_given_up": home_pts_per_possession}
        
    return stats_dict

def simulate_game(home_stats, away_stats):
    '''uses stats from home and away teams to simulate a single game'''
    # set the margin to 0 for our while loop
    margin = 0
    while(margin == 0):
        home_pace = rand.gauss(home_stats['pace']['mean'],
                               home_stats['pace']['std_dev'])
        home_pts_scored = rand.gauss(home_stats['points_scored']['mean'],
                                     home_stats['points_scored']['std_dev'])
        home_pts_given_up = rand.gauss(home_stats['points_given_up']['mean'],
                                       home_stats['points_given_up']['std_dev'])
        away_pace = rand.gauss(away_stats['pace']['mean'],
                               away_stats['pace']['std_dev'])
        away_pts_scored = rand.gauss(away_stats['points_scored']['mean'],
                                     away_stats['points_scored']['std_dev'])
        away_pts_given_up = rand.gauss(away_stats['points_given_up']['mean'],
                                       away_stats['points_given_up']['std_dev'])
        pace = round((home_pace + away_pace) / 2)
        home_pts = round(((home_pts_scored + away_pts_given_up) / 2) * pace)
        away_pts = round(((away_pts_scored + home_pts_given_up) / 2) * pace)
        margin = home_pts - away_pts
        
    results = {"home_pts": home_pts, "away_pts": away_pts, "pace": pace, "margin": margin}
    return results

def nba_game_simulator(dframe, home='MIN', away='DEN', sims=1000):
    '''This will run x number of game simulations'''
    #containers for counts
    home_wins = 0
    away_wins = 0
    
    #containers for stats
    margins = []
    home_margins = []
    away_margins = []
    home_pts = []
    away_pts = []
    
    home_df = dframe.loc[(dframe['team_abbreviation_home'] == home)]
    away_df = dframe.loc[(dframe['team_abbreviation_away'] == away)]
    home_stats = get_team_stats(home_df)
    away_stats = get_team_stats(away_df, home=False)
    for i in range(sims):
        game_result = simulate_game(home_stats, away_stats)
        home_pts.append(game_result['home_pts'])
        away_pts.append(game_result['away_pts'])
        margins.append(game_result['margin'])
        if (game_result['margin'] > 0):
            home_wins += 1
            home_margins.append(game_result['margin'])
        else:
            away_wins += 1
            away_margins.append(-game_result['margin'])
    
    home_win_pct = round(home_wins / 100)
    away_win_pct = round(away_wins / 100)
    home_avg_pts = round(stats.mean(home_pts))
    away_avg_pts = round(stats.mean(away_pts))
    home_avg_margin = round(stats.mean(home_margins))
    away_avg_margin = round(stats.mean(away_margins))
    results = {"home_avg_margin": home_avg_margin, "away_avg_margin": away_avg_margin,
               "home_win_pct": home_win_pct, "away_win_pct": away_win_pct,
               "home_avg_pts": home_avg_pts, "away_avg_pts": away_avg_pts,
               "margins": margins,}
    return results

def retrieve_data():
  '''retrieves data_frame'''
  
  games_df = get_df_from_db('nba_data.db','games',
                          select=['team_abbreviation_home', 'team_abbreviation_away',
                                  'points_per_possession_home', 'points_per_possession_away',
                                  'pace_home'],
                          order_by='game_date')
  
  teams_df = get_df_from_db('nba_data.db', 'games',
                          select=['DISTINCT team_abbreviation_home'],
                          order_by='team_abbreviation_home')

  dfs_dict = {"games":games_df, "teams":teams_df}

  return dfs_dict