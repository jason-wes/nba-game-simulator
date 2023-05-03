import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import simulategames

nba_data = simulategames.retrieve_data()
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def get_options(df, colname):
    '''take a column from a dataframe and create and options list'''

    new_list = df[colname].tolist()
    options_list = []
    for i in new_list:
        options_list.append({'label': i, 'value': i})

    return options_list


controls = dbc.Card(
[

  dbc.FormGroup(
    [
      dbc.Label("Home Team"),
      dcc.Dropdown(
        id='hteam',
        options=get_options(nba_data['teams'], 'team_abbreviation_home'),
        value='PHX'
        ),
    ]
    ),
  dbc.FormGroup(
    [
      dbc.Label('Away Team'),
      dcc.Dropdown(
        id='ateam',
        options=get_options(nba_data['teams'], 'team_abbreviation_home'),
        value='LAL'
        ),
    ]
    )
],
body=True
)

table_header = [
  html.Thead(html.Tr([html.Th() , html.Th("Home Team") , html.Th("Away Team")]))
]
row1 = html.Tr([html.Th("Win %"),
                html.Td(id='htwinper'),
                html.Td(id='atwinper')])
row2 = html.Tr([html.Th("Avg. Margin of Victory"),
                html.Td(id='htmvict'),
                html.Td(id='atmvict')])
row3 = html.Tr([html.Th("Avg. Points Scored"),
                html.Td(id='htpts'),
                html.Td(id='atpts')])
table_body = [html.Tbody([row1 , row2, row3])]
table = dbc.Table(table_header + table_body)
simResults = dbc.Card(
	[

		
	html.H4('Simulation Results'),
	table
	],
	body=True
	)

app.layout = dbc.Container(
		[
			html.H1(children='Choose two teams to see the results of 10k sims', style={'textAlign':'center'}),
			html.Hr(),
			dbc.Row(
				[
					dbc.Col([controls, html.Br(), simResults], md=4),
					dbc.Col([html.H3('All margins of victory | Home - Away'), dcc.Graph(id='histogram')] , md=8)
				],
				align='center',
				),
		],
		fluid=True
	)

@app.callback(
Output('histogram' , 'figure'),
Output('htwinper' , 'children'),
Output('atwinper' , 'children'),
Output('htmvict' , 'children'),
Output('atmvict' , 'children'),
Output('htpts' , 'children'),
Output('atpts', 'children'),
Input('hteam' , 'value' ),
Input('ateam' , 'value'))

def callback( home , away):
  results = simulategames.nba_game_simulator(nba_data['games'],
                                              home, away, sims=10000)

  return px.histogram(results['margins']),\
         results['home_win_pct'],\
         results['away_win_pct'],\
         results['home_avg_margin'],\
         results['away_avg_margin'],\
         results['home_avg_pts'],\
         results['away_avg_pts']

if __name__ == '__main__':
    app.run_server(debug=True)