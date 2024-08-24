import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import io
import base64
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


# Inicjalizacja aplikacji Dash
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Aplikacja do analizy korelacji" 
app.config.suppress_callback_exceptions = True
server = app.server


# Layout aplikacji
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1("Macierz Korelacji z Pliku CSV/XLS/XLSX", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Przeciągnij i upuść lub ', html.A('wybierz plik')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'cursor': 'pointer'
        },
        multiple=False
    ),
    
    html.Div([
        html.Label("Wybierz format pliku:"),
        dcc.RadioItems(
            id='file-format',
            options=[
                {'label': 'CSV', 'value': 'csv'},
                {'label': 'Excel (XLS/XLSX)', 'value': 'excel'}
            ],
            value='csv',
            labelStyle={'display': 'inline-block', 'marginRight': '20px'}
        )
    ], style={'textAlign': 'center', 'marginTop': '20px'}),

    html.Div([
        html.Label("Wybierz paletę kolorów:"),
        dcc.Dropdown(
            id='color-scale',
            options=[
                {'label': 'RdBu_r', 'value': 'RdBu_r'},
                {'label': 'Viridis', 'value': 'Viridis'},
                {'label': 'Cividis', 'value': 'Cividis'},
                {'label': 'Plasma', 'value': 'Plasma'},
                {'label': 'Blues', 'value': 'Blues'},
                {'label': 'Greens', 'value': 'Greens'},
                {'label': 'Reds', 'value': 'Reds'},
                {'label': 'Purples', 'value': 'Purples'},
                {'label': 'Oranges', 'value': 'Oranges'},
                {'label': 'Magma', 'value': 'Magma'},
                {'label': 'Inferno', 'value': 'Inferno'},
                {'label': 'Jet', 'value': 'Jet'},
                {'label': 'Rainbow', 'value': 'Rainbow'},
                {'label': 'YlGnBu', 'value': 'YlGnBu'},
                {'label': 'BuPu', 'value': 'BuPu'},
                {'label': 'OrRd', 'value': 'OrRd'}
            ],
            value='RdBu_r',
            clearable=False,
            style={'width': '50%', 'margin': 'auto'}
        )
    ], style={'textAlign': 'center', 'marginTop': '20px'}),
    
    html.Div(id='correlation-description', style={'textAlign': 'center', 'marginTop': '20px', 'padding': '20px', 'border': '1px solid #ccc', 'borderRadius': '5px'}),
    
    dcc.Graph(id='correlation-matrix'),

    html.Footer([
        'Created by ', 
        html.A('Mateusz Kozera', href='https://www.linkedin.com/in/mateusz-kozera/', target='_blank')
    ], style={
        'position': 'relative', 
        'bottom': '0', 
        'width': '100%', 
        'background-color': '#f1f1f1', 
        'text-align': 'center', 
        'padding': '10px 0'
    }),

])

# Callback do przetwarzania pliku CSV/XLS/XLSX i generowania macierzy korelacji
@app.callback(
    [Output('correlation-matrix', 'figure'), Output('correlation-description', 'children')],
    [Input('upload-data', 'contents'), Input('file-format', 'value'), Input('color-scale', 'value')]
)
def update_output(file_contents, file_format, color_scale):
    if file_contents is None:
        return {}, "Załaduj plik CSV lub XLS/XLSX, aby zobaczyć wyniki."

    try:
        # Dekodowanie pliku
        content_type, content_string = file_contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Wybór metody wczytywania pliku na podstawie wyboru użytkownika
        if file_format == 'csv':
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif file_format == 'excel':
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return px.imshow([[0]], text_auto=True, aspect="auto", title="Nieobsługiwany format pliku"), "Obsługiwane formaty: CSV, XLS, XLSX."

        # Filtracja kolumn liczbowych
        numeric_df = df.select_dtypes(include=['number'])

        if numeric_df.empty:
            return px.imshow([[0]], text_auto=True, aspect="auto", title="Brak danych liczbowych"), "Brak danych liczbowych do analizy."

        # Generowanie macierzy korelacji
        correlation_matrix = numeric_df.corr()

        # Znajdowanie największej i najmniejszej korelacji
        corr_values = correlation_matrix.values
        np.fill_diagonal(corr_values, np.nan)  # Usunięcie 1 z przekątnej
        max_corr = np.nanmax(corr_values)
        min_corr = np.nanmin(corr_values)
        
        max_pair = np.unravel_index(np.nanargmax(corr_values), correlation_matrix.shape)
        min_pair = np.unravel_index(np.nanargmin(corr_values), correlation_matrix.shape)
        
        max_corr_desc = f"Największa korelacja: {max_corr:.2f} (między '{correlation_matrix.columns[max_pair[0]]}' a '{correlation_matrix.columns[max_pair[1]]}')"
        min_corr_desc = f"Najmniejsza korelacja: {min_corr:.2f} (między '{correlation_matrix.columns[min_pair[0]]}' a '{correlation_matrix.columns[min_pair[1]]}')"

        # Średnia korelacja
        mean_corr = np.nanmean(np.abs(corr_values))
        mean_corr_desc = f"Średnia wartość korelacji: {mean_corr:.2f}"

        description = f"{max_corr_desc}\n\n{min_corr_desc}\n\n{mean_corr_desc}"

        # Rysowanie macierzy korelacji za pomocą Plotly
        fig = px.imshow(correlation_matrix, text_auto=True, aspect="auto", color_continuous_scale=color_scale, title="Macierz Korelacji")
        
        return fig, description
    except Exception as e:
        print(f"Error: {str(e)}")
        return px.imshow([[0]], text_auto=True, aspect="auto", title="Błąd podczas analizy danych"), f"Wystąpił błąd: {str(e)}"

# Uruchomienie serwera
if __name__ == '__main__':
    app.run_server(debug=False)

