import dash
from dash import dcc
from dash import html
import json 
from plotly import graph_objs as go
from plotly.subplots import make_subplots

from datetime import datetime as dt 
from dash.exceptions import PreventUpdate
from dash.dependencies import Output, Input, State, ALL 

import queries as q

######## WEB LAYOUT ########
l = go.Layout(
    title={
        'text': '',
        'xanchor': 'center'
    },
    showlegend=True,
    autosize=True,
    margin=dict(
        t=25,
        b=0,
        l=0,
        r=25
    ),
    hovermode='closest',
    clickmode='event',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white',
    yaxis={'side': 'left'},
    yaxis2={
        'gridcolor': '#444',
        'zerolinecolor': '#4AF626',
        'side': 'right'
    }
)

fig = go.Figure(data=[], layout=l)
fig = make_subplots(specs=[[{'secondary_y': True}]], figure=fig)
app = dash.Dash(
	__name__
)

app.title = 'Stock Price Analyzer'
app.layout = html.Div(
    [     
        dcc.Store(id='memory'),
        dcc.Store(id='graph-cache'),
        dcc.Store(id='last-forecast'),
        
        # Search bar
        html.Div([
            html.Div([
                dcc.Input(
                    id='search-text',
                    type='text',
                    placeholder='DDD, LWLG, CRSPR, ...',
                    value='',
                    debounce=True,
                    style={
                        'display': 'inline-block',
                        'width': '60%',
                        'height': '30px',
                        'border-radius': '10px',
                        'margin-right': '5px',
                        'font-size': '15px'
                    }
                ),
                html.Button(
                    'Search', 
                    id='search-button',
                    style={
                        'display': 'inline-block',
                        'border-radius': '4px',
                        'height': '30px',
                    }
                ),
                ],
                style={
                    'width': '100%',
                    'position': 'relative',
                    'top': '50%',
                    '-ms-transform': 'translateY(-50%)',
                    'transform': 'translateY(-50%)'
                }
            ),
            ],
            style={
                'width': '100%',
                'height': '60px',
                'text-align': 'center',
            }
        ),

        # Middle
        html.Div(
            [
                # Where stocks will go 
                html.Div(
                    id='stocks',
                    style={ 
                        'float': 'left',
                        'width': '30%',
                        'margin-left': 15,
                        'height': '75vh',
                        'overflow': 'overlay',
                        'outline' : '2px dotted LightGray'
                    }    
                ), 

                # Graph
                html.Div([
                    dcc.Graph(
                        id='live-graph',
                        figure=fig, 
                        config={'scrollZoom': True, 'staticPlot': False}, 
                        #animate=True,
                        #animation_options={'frame': {'redraw': True}},
                        style={
                            'width': '95%',
                            'height': '100%',
                            'margin': 'auto'
                        }
                    ), 
                ], 
                style={
                        'width': '65%',
                        'float': 'right',
                        'height': '75vh',
                        'text-align': 'center'
                })
            ],
            style={
                'margin-top': '15px'
            }
        ),

        # Footer tools
        html.Div(
            [
                html.Div([
                    html.P('Derivative Delta Size: ', style={'display': 'inline-block'}),
                    dcc.Input(
                        id='rolling-avg',
                        value='4',
                        type='number',
                        style={
                            'width': '40px',
                            'background-color': 'gray',
                            'color': 'white',
                            'margin-left': '5px',
                            'margin-right': '5px',
                            'border-radius': '10px',
                        },
                        debounce=False
                    ),
                    html.P('weeks', style={'display': 'inline-block','margin-right': '10px'})
                ],
                style={'display': 'inline-block'}
                ),
                html.Div([
                    html.P("Display forecast: ", style={'display': 'inline-block'}),
                    dcc.RadioItems(
                        id='forecast',
                        options=[
                            {'label': '', 'value': ''}
                        ],
                        style={'display': 'inline-block'},
                        labelStyle={'display': 'inline-block'},
                        value=''
                    )
                ],
                style={'display': 'inline-block'}
                )
            ],
            style={
                'width': '100%',
            }
        )
    ], 
    style={
        'font-family': 'sans-serif',
        'color': 'white',
        'height': '100vh'
    }
)

######## CALLBACKS ########
@app.callback(
    [
        Output('live-graph', 'figure'),
        Output('graph-cache', 'data'),
        Output('last-forecast', 'data')
    ],
    [
        Input({'type': 'derivatives', 'index': ALL}, 'value'),
        Input('rolling-avg', 'value'),
        Input('forecast', 'value')
    ],
    [
        State('live-graph', 'figure'),
        State('memory', 'data'),
        State('graph-cache', 'data'),
        State('last-forecast', 'data')
    ],
    prevent_initial_call=True
)
def update_graph(_, smooth, forecast, figure, mem, cached, last_forecast):
    ctx = dash.callback_context.triggered

    if smooth is None:
        return figure, cached, last_forecast

    smooth = int(smooth)
    cached = dict() if cached is None else cached
    last_forecast = '' if last_forecast is None else last_forecast

    if ctx[0]['prop_id'] == '.':
        figure['data'] = []
        figure['layout']['annotations'] = []
        return {'data': figure['data'], 'layout': figure['layout']}, dict(), ''

    # Update forecast
    if ctx[0]['prop_id'] == 'forecast.value':
        if forecast == '':
            figure['layout']['annotations'] = []
            return {
                'data': figure['data'],
                'layout': figure['layout']
            }, cached, ''

        if forecast not in cached:
            print("Generating data for %s" % forecast)
            cached[forecast] = q.get_all(forecast, smooth=smooth)
            #cached['data'] = data 

        figure['layout']['annotations'] = cached[forecast][3][:10]
        return {
            'data': figure['data'],
            'layout': figure['layout']
        }, cached, forecast

    # Update smoothing on derivatives
    if ctx[0]['prop_id'] == 'rolling-avg.value':
        fig_dat = []

        to_update = {}
        for series in figure['data']:
            ticker, deriv = series['name'].split(':')
            
            if ticker not in to_update:
                to_update[ticker] = []
            
            to_update[ticker].append(deriv)
    
        for ticker, derivs in to_update.items():
            # Only update valid stocks
            if cached[ticker][0]:
                cached[ticker][1] = q.first(*cached[ticker][0], smooth)
                cached[ticker][2] = q.second(*cached[ticker][1], smooth)
                cached[ticker][3] = q.find_zeros(*cached[ticker][2])

                fig_dat += [
                    get_series(cached[ticker][int(i)], ticker, i) 
                    for i in derivs if int(i) < 3
                ]
                
                if last_forecast == ticker:
                    figure['layout']['annotations'] = cached[ticker][3]

        return {
            'data': fig_dat,
            'layout': figure['layout']
        }, cached, last_forecast
            

    pids = [str(json.loads(child['prop_id'].split('.')[0])['index']) for child in ctx]

    # Len is only greater than 1 if adding new stock
    if len(pids) > 1:
        for pid in pids:
            if pid not in cached:
                to_cache = q.get_all(pid, smooth=smooth)
                if to_cache is None:
                    cached[pid] = [[[],[]] * 3, []]
                else:
                    cached[pid] = to_cache 

        return figure, cached, last_forecast

    # Adding a new or cached chart
    values = [str(v) for v in ctx[0]['value']]
    ticker = pids[0]
    
    # Avoid duplicates and remove deleted series
    new_dat = []
    for d in figure['data']:
        print(d['customdatasrc'])
        if d['customdatasrc'] != ticker and d['customdatasrc'] in mem['data']:
            new_dat.append(d)

    figure['data'] = new_dat

    # Query yfinance if this is the first time seeing ticker
    if ticker not in cached:
        to_cache = q.get_all(ticker, smooth=smooth)
        if to_cache is None:
            cached[ticker] = [[[],[]] * 3, []]
        else:
            cached[ticker] = to_cache 

    for v in values:
        if v != '3':
            series = get_series(cached[ticker][int(v)], ticker, v)
            figure['data'].append(series)
    
    # Sync pid cache and graph cache
    cached_keys = list(cached.keys())
    for ticker in cached_keys:
        if ticker not in mem['data']:
            del cached[ticker]
            if ticker == last_forecast:
                figure['layout']['annotations'] = []
                last_forecast = ''

    return {
        'data': figure['data'], 
        'layout': figure['layout']
    }, cached, last_forecast

def get_series(xy, ticker, deriv):
    #if deriv == '3':
    #    fig['layout']['annotatons'] = xy

    x,y = xy[0], xy[1]
    return go.Scatter(
        x=x, y=y, 
        name=ticker + ':' + deriv, 
        customdatasrc=ticker,
        yaxis='y' if deriv=='0' else 'y2'
    )


@app.callback(
    Output('forecast', 'options'),
    Input('memory', 'data'),
    State('forecast', 'options')
)
def update_forecast_options(mem, options):
    opts = [{'label': 'None', 'value': ''}]
    for m in mem['data']:
        opts.append(
            {'label': m, 'value': m}
        )
    
    return opts 

@app.callback(
    [
        Output('memory', 'data'),
        Output('search-text', 'value')
    ],
    Input({'type': 'dynamic-delete', 'index': ALL}, 'n_clicks'),
    [
        State('memory', 'data'),
        State('search-text', 'value')
    ]
)
def update_memory(_, mem, ticker):
    ctx = dash.callback_context.triggered

    # Final stock has been deleted
    if ctx[0]['prop_id'] == '.':
        return {'data': []}, ticker

    mem = mem or {'data': []}

    # If the id is not in the dict, it's new. Otherwise, we're deleting it
    prop_ids = [str(json.loads(child['prop_id'].split('.')[0])['index']) for child in ctx]
    data = mem['data']

    # Delete button was clicked
    if ctx[0]['value'] == 1:
        data.remove(prop_ids[0])
        mem['data'] = data 
        return mem, ticker

    # New stock added
    for pid in prop_ids:
        if pid not in data:
            data.append(ticker.upper())
            break 
    
    mem['data'] = data 
    print("update_memory out: " + str(mem))
    return mem, ''


@app.callback(
    Output('stocks', 'children'),
    [
        Input('search-button', 'n_clicks'),
        Input({'type': 'dynamic-delete', 'index': ALL}, 'n_clicks'),
        Input('search-text', 'value')
    ],
    [
        State('stocks', 'children'),
        State('memory', 'data')
    ],
    prevent_initial_call=True
)
def add_or_del_security(_, d, text, children, mem):
    ctx = dash.callback_context.triggered[0]
    pid = ctx['prop_id']
    text = text.upper()
    mem = mem or {'data': []}
    mem = mem['data']

    # Don't add blanks or dupes
    if 'search' in pid:
        if text == '' or text in mem: 
            return children

    if children is None:
        children = [] 

    if 'search' in pid:
        return add_new_stock(text, children)

    else:
        text = json.loads(ctx['prop_id'].split('.')[0])['index']
        return delete_stock(text, children)

def add_new_stock(ticker, component):
    children = component or []

    new_div = html.Div([
        html.P(
            ticker,
            style={'text-align': 'center'}
        ),
        dcc.Checklist(
                id={'type': 'derivatives', 'index': ticker},
                options=[
                    {'label': 'Base Price\n', 'value': 0},
                    {'label': 'd/dx', 'value': 1},
                    {'label': 'd^2/dx', 'value': 2}
                ],
                value=[],
                style={'text-align': 'center'}
        ), 
        html.Button(
            'Delete', 
            id={'type': 'dynamic-delete', 'index': ticker},
            style={'width': '100%', 'margin': 'auto'}
        )],
        id={'type': 'dynamic-div', 'index': ticker},
        style={
            'width': '90%',
            'margin': 'auto',
            'padding': '1% 5% 2.5% 5%',
            'outline': '2px solid gray'
}
    )

    children.append(new_div)
    return children

def delete_stock(ticker, children):
    for i in range(len(children)):
        cn = children[i]['props']['id']['index']

        if cn == ticker:
            del children[i]
            break

    return children or []
     

######## START EVERYTHING ########    
if __name__ == '__main__':
	app.run_server(debug=True, use_reloader=True, dev_tools_hot_reload=True)