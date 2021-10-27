import dash
from dash import dcc
from dash import html
import json 
from plotly import graph_objs as go

from dash.exceptions import PreventUpdate
from dash.dependencies import Output, Input, State, ALL 

from queries import dummy 

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
)

fig = go.Figure(data=[], layout=l)
app = dash.Dash(
	__name__, 
	url_base_pathname='/graggle/'
)

app.title = 'Stock Price Analyzer'
app.layout = html.Div([     
    dcc.Store(id='memory'),
    dcc.Store(id='graph-cache'),

    # Header
    html.Div([
        html.H1(
            'Stock Tools', 
            style={
                'margin-bottom': '0px'
            }
        )],
        style={
            'top': '0px',
            'width': '100%',
            'height': '75px',
            'color': 'white',
            'text-align': 'center',
            'background': "linear-gradient(90deg, rgba(3,60,90,1) 0%, rgba(3,44,65,1) 100%)",
            'padding-top': '10px',
            'margin-top': '-20px',
            'padding-bottom': '15px'
        }
    ),
    
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
            'background': "linear-gradient(90deg, rgba(170,152,104,1) 0%, rgba(140,126,88,1) 100%)",
            'width': '100%',
            'height': '60px',
            'text-align': 'center',
        }
    ),

    # Middle
    html.Div([
        'Securities:', 
        # Where stocks will go 
        html.Div(id='stocks'), 

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
                    'height': 'calc(70vh - 50px)'
                }
            )], 
        style={
                'width': '65%',
                'float': 'right',
                'height': '80vh',
                'text-align': 'center'
        })    
    ]),

    # Otherwise dash has a hissy-fit
    html.Button(
        id='del-button',
        style={'display': 'none'}
    )
    ], 
    style={
        'font-family': 'sans-serif',
        'color': 'rgba(3,60,90,1)'
    }
)

######## CALLBACKS ########
@app.callback(
    [
        Output('live-graph', 'figure'),
        Output('graph-cache', 'data')
    ],
    Input({'type': 'derivatives', 'index': ALL}, 'value'),
    [
        State('live-graph', 'figure'),
        State('memory', 'data'),
        State('graph-cache', 'data')
    ],
    prevent_initial_call=True
)
def update_graph(_, figure, mem, cached):
    ctx = dash.callback_context.triggered
    print('update_graph: ' + str(ctx))
    print(mem)

    if ctx[0]['prop_id'] == '.':
        figure['data'] = []
        return figure, None 

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
            data[pid][v] = get_series(mem['data'][pid], v, pid)
        
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

def get_series(ticker, deriv, pid):
    x,y = dummy()
    return go.Scatter(x=x, y=y, name=ticker + ':' + str(deriv), customdatasrc=pid)

def remove_data(figure, mem, cached):
    print(figure['data'])
    return figure, cached # TODO

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
        Input({'type': 'dynamic-delete', 'index': ALL}, 'n_clicks')
    ],
    [
        State('search-text', 'value'),
        State('stocks', 'children')
    ],
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
        html.P(ticker),
        dcc.Checklist(
                id={'type': 'derivatives', 'index': idx},
                options=[
                    {'label': 'Base Price\n', 'value': 0},
                    {'label': 'd/dx', 'value': 1},
                    {'label': 'd^2/dx', 'value': 2}
                ],
                value=[]
        ), 
        html.Button(
            'Delete', 
            id={'type': 'dynamic-delete', 'index': idx}
        )], 
        style={ 
            'margin-left': 50, 
            'float': 'left',
            'width': '28%',
            'margin-top': 15
        },
        id={'type': 'dynamic-div', 'index': idx}
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
	app.run_server(debug=True, use_reloader=True, host='0.0.0.0', dev_tools_hot_reload=True)