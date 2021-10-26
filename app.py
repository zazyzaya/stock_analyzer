import dash
from dash import dcc
from dash import html
import json 
from plotly import graph_objs as go

from dash.exceptions import PreventUpdate
from dash.dependencies import Output, Input, State, ALL 

######## WEB LAYOUT ########
l = go.Layout(
    title={
        'text': 'Price Comparison',
        'x': 0.5,
        'xanchor': 'center'
    },
    showlegend=False,
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

#Xn, Yn, edges, titles, labels, ids = get_all_g()
data = [] 
last_id = None
fig = go.Figure(data=data, layout=l)

app = dash.Dash(
	__name__, 
	url_base_pathname='/graggle/'
)

app.title = 'Stock Price Analyzer'
app.layout = html.Div([     
    dcc.Store(id='memory'),

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
                animate=True,
                animation_options={'frame': {'redraw': True}},
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
    Output('live-graph', 'figure'),
    Input({'type': 'derivatives', 'index': ALL}, 'value'),
    [
        State('live-graph', 'figure'),
        State('memory', 'data')
    ],
    prevent_initial_call=True
)
def update_graph(values, figure, idx_map):
    ctx = dash.callback_context.triggered[0]['prop_id']

    pid = json.loads(ctx.split('.')[0])['index'] 
    #ticker = idx_map[str(pid)]

    #print(ticker)
    print(values)

    return figure

@app.callback(
    Output('stocks', 'children'),
    [
        Input('search-button', 'n_clicks'),
        Input({'type': 'dynamic-delete', 'index': ALL}, 'n_clicks')
    ],
    [
        State('search-text', 'value'),
        State('stocks', 'children'),
        State('memory', 'data')
    ],
    prevent_initial_call=True
)
def add_or_del_security(idx, d, text, children, mem):
    ctx = dash.callback_context.triggered[0]
    pid = ctx['prop_id']
    text = text.upper()

    mem = mem or {}

    if pid == 'search-button.n_clicks' and text == '': 
        return []

    if children is None:
        children = [] 

    if 'search' in pid:
        print("children add_or_del: " + str(children))
        mem[idx] = text
        return add_new_stock(text, children, idx)#, mem

    else:
        idx = json.loads(pid.split('.')[0])['index']
        #mem = {key:val for key,val in idx_map if val != d}
        return delete_stock(idx, children)#, mem

def add_new_stock(ticker, component, idx):
    print('add_new_stock:' + str(component))
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
    print("Searching for div with " + str(d))

    for i in range(len(children)):
        cn = children[i]['props']['id']['index']
        print(cn)

        if cn == d:
            del children[i]
            break

    return children or []
     

######## START EVERYTHING ########    
if __name__ == '__main__':
	app.run_server(debug=True, use_reloader=True, host='0.0.0.0', dev_tools_hot_reload=True)