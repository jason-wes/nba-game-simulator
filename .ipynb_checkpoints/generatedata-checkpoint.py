from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import boxscoreadvancedv2
from nba_api.stats.library.parameters import SeasonType
import pandas as pd
import time
import random as rand
from IPython.display import clear_output
import sqlite3 as sql
import statistics as stats

def get_game_data(season, league_id='00', test=False):
    '''Query NBA stats via the nba-api
    
    Parameters
    ----------
    season: format is yyyy-yy ie. 2020-21
    league_id = '00' => NBA
    Returns
    -------
    result: dict of 2 DataFrames {"games_basic": , "games_adv": }
    '''
    #first we need to get all of the basic game data
    gamefinder = leaguegamefinder.LeagueGameFinder(league_id_nullable=league_id,
                                                   season_nullable=season,
                                                   season_type_nullable=SeasonType.regular)
    
    games_basic_df = gamefinder.get_data_frames()[0]
    
    #then we need to get the advanced game data. Slow, game by game.
    #we need to get a list of the games
    game_ids = list(games_basic_df['GAME_ID'].unique())
    
    games_adv_df = pd.DataFrame()
    if test:
        c = 0 # this is here for testing only
    
    #now we iterate over the list of game_ids
    while len(game_ids) > 0:
        for i in game_ids:
            cooldown = rand.gammavariate(alpha=9, beta=0.4)
            clear_output(wait=True)

            for attempt in range(10):
                try:
                    time.sleep(cooldown)
                    data = boxscoreadvancedv2.BoxScoreAdvancedV2(end_period=4,
                                                                 end_range=0,
                                                                 game_id=i,
                                                                 range_type=0,
                                                                 start_period=1,
                                                                 start_range=0)
                except:
                    time.sleep(cooldown)
                    data = boxscoreadvancedv2.BoxScoreAdvancedV2(end_period=4,
                                                                 end_range=0,
                                                                 game_id=i,
                                                                 range_type=0,
                                                                 start_period=1,
                                                                 start_range=0)
                else:
                    break
            else:
                print('Connection Error')
                break
            data_df = data.get_data_frames()[1]

            if games_adv_df.empty:
                games_adv_df = data_df
            else:
                games_adv_df = games_adv_df.append(data_df, ignore_index=True)

            game_ids.remove(i)
            print (i , "completed", len(game_ids), "games left", sep="---")    

            if test:
                c += 1
                if c > 3: #again for testing only
                    games_df_dict = {"games_basic": games_basic_df, "games_adv": games_adv_df}
                    print('DONE!')
                    return games_df_dict
    games_df_dict = {"games_basic": games_basic_df, "games_adv": games_adv_df}
    print('DONE!')
    return games_df_dict
        
def prep_games(dictionary, left_key, right_key, left, right):
    '''join two dataframes
    
    Paramaters
    ----------
    dictionary: Input dict
    left_key: dictionary key for left dataframe
    right_key: dictionary key for right dataframe
    left: list of columns for left join
    right: list of columns for right join
    
    Returns
    -------
    result: DataFrame
    '''
    #join the two DataFrames using the paramaters
    joined = dictionary[left_key].merge(dictionary[right_key],
                                 left_on=left,
                                 right_on=right)
     # Join every row to all others with the same game ID.
    joined = pd.merge(joined, joined, suffixes=['_HOME', '_AWAY'],
                      on=['SEASON_ID', 'GAME_ID', 'GAME_DATE'])
    # Filter out any row that is joined to itself.
    result = joined[joined.TEAM_ID_HOME != joined.TEAM_ID_AWAY]
    result = result[result.MATCHUP_HOME.str.contains(' vs. ')]
    #lowercase the columnn names for easier access
    result.columns = result.columns.str.lower() 
    return result

def calc_points_per_possession(df):
    '''Calculate the home/away points per possesion and update the dataframe'''
    
    df['points_per_possession_home'] = df['pts_home'] / df['pace_home']
    df['points_per_possession_away'] = df['pts_away'] / df['pace_home']
    
    return df
    
def save_df_to_db(df, db_name, table_name, exists='replace'):
    '''Saves a dataframe to a table in a sqlite database
    
    Paramaters
    ----------
    df: DataFrame to save to table
    db_name: name of database
    table_name: name of table
    exists: what to do if table exists, default='replace'
    
    Return
    ------
    return:
    '''
    conn = None
    try:
        conn = sql.connect(db_name)
        df.to_sql(table_name, conn, if_exists=exists)
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()
    

def generate_season_data(season):
  '''this will call all the functions needed to get and save a season of data'''
  
  df = get_game_data(season)
  df = prep_games(df,
                  left_key='games_basic',
                  right_key='games_adv',
                  left=['GAME_ID' , 'TEAM_ID' , 'TEAM_ABBREVIATION'], 
                  right=['GAME_ID' , 'TEAM_ID' , 'TEAM_ABBREVIATION'])
  df = calc_points_per_possession(df)
  save_df_to_db(df, 'nba_data.db', 'games')
  
  return True

season_data = generate_season_data('2022-23')
if season_data:
  print(season_data, "SEASON GENERATED AND SAVED SUCCESFULLY")