import dash
import dash_core_components as dcc
import dash_html_components as html
import json 
from plotly import graph_objs as go

from dash.exceptions import PreventUpdate
from dash.dependencies import Output, Input, State, ALL 

import queries as q

######## WEB LAYOUT ########
l = go.Layout(
    title={
        'text': 'Price Comparison',
        'x': 0.5,
        'xanchor': 'center'
    },
    showlegend=True,
    autosize=True,
    margin=dict(
        t=25,
        b=0,
        l=0,
        r=0
    ),
    hovermode='closest',
    clickmode='event',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white'
)

fig = go.Figure(data=[], layout=l)
app = dash.Dash(
	__name__
)

app.title = 'Stock Price Analyzer'
app.layout = html.Div(
    [     
        dcc.Store(id='memory'),
        dcc.Store(id='graph-cache'),
        
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
                html.P('Derivative Delta Size: ', style={'display': 'inline-block'}),
                dcc.Input(
                    id='rolling-avg',
                    value='4',
                    type='number',
                    style={
                        'width': '20px',
                        'background-color': 'gray',
                        'color': 'white',
                        'margin-left': '5px',
                        'margin-right': '5px',
                        'border-radius': '10px',
                    },
                    debounce=True
                ),
                html.P('weeks', style={'display': 'inline-block'})
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
        Output('graph-cache', 'data')
    ],
    [
        Input({'type': 'derivatives', 'index': ALL}, 'value'),
        Input('rolling-avg', 'value')
    ],
    [
        State('live-graph', 'figure'),
        State('memory', 'data'),
        State('graph-cache', 'data')
    ],
    prevent_initial_call=True
)
def update_graph(_, avg, figure, mem, cached):
    ctx = dash.callback_context.triggered
    print('update_graph: ' + str(ctx))
    print(mem)

    if ctx[0]['prop_id'] == '.':
        figure['data'] = []
        return figure, None 

    if ctx[0]['prop_id'] == 'rolling-avg.value':
        #TODO
        return figure, cached

    cached = {} if cached is None else cached
    data = {} if not cached else cached['data']
    pids = [str(json.loads(child['prop_id'].split('.')[0])['index']) for child in ctx]

    # Len is only greater than 1 if adding new stock
    if len(pids) > 1:
        print("Returning just the one")
        return figure, cached 

    # Adding a new or cached chart
    values = [str(v) for v in ctx[0]['value']]
    pid = pids[0]
    
    # Avoid duplicates and remove deleted series
    new_dat = []
    for d in figure['data']:
        print(d['customdatasrc'])
        if d['customdatasrc'] != pid and d['customdatasrc'] in mem['data']:
            new_dat.append(d)

    figure['data'] = new_dat

    for v in values:
        if pid not in data:
            data[pid] = {}
        if v not in data[pid]:
            series = get_series(mem['data'][pid], v, pid, int(avg))
            
            if series: 
                data[pid][v] = series
            else: 
                print("Something went wrong; series %s, %s returned NULL" % (mem['data'][pid], v))
        
        figure['data'].append(data[pid][v])
    
    # Sync pid cache and graph cache
    cached_keys = list(data.keys())
    for pid in cached_keys:
        if pid not in mem['data']:
            del data[pid]

    cached['data'] = data

    return {
        'data': figure['data'], 
        'layout': figure['layout']
    }, cached 

def get_series(ticker, deriv, pid, avg):
    if deriv == '0':
        x,y = q.base(ticker)
    elif deriv == '1': 
        x,y = q.first(ticker, smooth=avg)
    else:
        return None
    
    return go.Scatter(x=x, y=y, name=ticker + ':' + str(deriv), customdatasrc=pid)


@app.callback(
    Output('memory', 'data'),
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
        return {'data': {}}

    mem = mem or {'data': {}}

    # If the id is not in the dict, it's new. Otherwise, we're deleting it
    prop_ids = [str(json.loads(child['prop_id'].split('.')[0])['index']) for child in ctx]
    data = mem['data']

    # Delete button was clicked
    if ctx[0]['value'] == 1:
        del data[prop_ids[0]]
        mem['data'] = data 
        return mem

    # New stock added
    for pid in prop_ids:
        if pid not in data:
            data[pid] = ticker.upper()
            break 
    
    mem['data'] = data 
    return mem


@app.callback(
    Output('stocks', 'children'),
    [
        Input('search-button', 'n_clicks'),
        Input({'type': 'dynamic-delete', 'index': ALL}, 'n_clicks'),
        State('search-text', 'value')
    ],
    State('stocks', 'children'),
    prevent_initial_call=True
)
def add_or_del_security(idx, d, text, children):
    ctx = dash.callback_context.triggered[0]
    pid = ctx['prop_id']
    text = text.upper()

    if pid == 'search-button.n_clicks' and text == '': 
        return []

    if children is None:
        children = [] 

    if 'search' in pid:
        return add_new_stock(text, children, idx)

    else:
        idx = json.loads(pid.split('.')[0])['index']
        return delete_stock(idx, children)

def add_new_stock(ticker, component, idx):
    children = component or []

    new_div = html.Div([
        html.P(
            ticker,
            style={'text-align': 'center'}
        ),
        dcc.Checklist(
                id={'type': 'derivatives', 'index': idx},
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
            id={'type': 'dynamic-delete', 'index': idx},
            style={'width': '100%', 'margin': 'auto'}
        )],
        id={'type': 'dynamic-div', 'index': idx},
        style={
            'width': '90%',
            'margin': 'auto',
            'padding': '1% 5% 2.5% 5%',
            'outline': '2px solid gray'
}
    )

    children.append(new_div)
    return children

def delete_stock(d, children):
    for i in range(len(children)):
        cn = children[i]['props']['id']['index']

        if cn == d:
            del children[i]
            break

    return children or []
     

######## START EVERYTHING ########    
if __name__ == '__main__':
	app.run_server(debug=True, use_reloader=True, dev_tools_hot_reload=True)