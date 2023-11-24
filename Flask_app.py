from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import calendar
import plotly.express as px

app = Flask(__name__)

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fondos-mutuos')
def fondos_mutuos():
    return render_template('index.html')


@app.route('/rentabilidades', methods=['GET', 'POST'])
def rentabilidades():
    fecha_datepicker = request.form.get('datepicker')
    df = pd.read_csv('uploads/rentabilidades_acumuladas.csv', sep=";", index_col=None)

    #Nuevo % rent acumu
    df['rent_acumulada'] = (df['rent_acumulada'] * 100).map('{:.2f}%'.format)

    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
    fechas = df['fecha'].unique()

    if fecha_datepicker is None:
        fecha_datepicker = fechas.max()
        fecha_str = fecha_datepicker.date().strftime('%m/%d/%Y')
        df_fecha = df[df['fecha'] == fecha_datepicker]
    else:
        fecha_typo_date = datetime.strptime(fecha_datepicker, '%m/%d/%Y')
        df_fecha = df[df['fecha'] == fecha_typo_date]
        fecha_str = fecha_datepicker

    if df_fecha.empty:
        html = "<p>No hay información para este periodo</p>"
    else:
        html = get_rentabilidades(df_fecha)
    print(html)
    return render_template('rentabilidades.html', html=html, fecha_actual=fecha_str)

@app.route('/portafolios', methods=['GET', 'POST'])
def portafolios():
    tipo_cartera = request.form.get('tipos')
    df = pd.read_csv('uploads/portafolio_nacional.csv', sep=";", index_col=None)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

    fondos = df['Run Fondo'].unique()

    run = str(request.form.get('fondos'))
    fecha = request.form.get("datepicker")

    date_picker = fecha

    if fecha != None and fecha != '':
        fecha = datetime.strptime(fecha, '%m/%d/%Y')
        fecha = ultimo_dia_del_mes(fecha)


    if run is None or tipo_cartera is None:
        html = ""
    else:
        html = get_portafolio(run, tipo_cartera, fecha)

    return render_template('portafolios.html', fondos=fondos, tipos=['Nacional', 'Internacional'], html=html)

#Nuevo
@app.route('/rentabilidades-graficos', methods=['GET', 'POST'])
def ren_graficos():
    fecha_datepicker = request.form.get('datepicker', default='07/31/2023')
    run_selected = request.form.get('run', default=None)
    
    # Convertir la fecha al formato del DataFrame
    fecha_datepicker_formatted = datetime.strptime(fecha_datepicker, '%m/%d/%Y').strftime('%Y-%m-%d')

    df = pd.read_csv('uploads/rentabilidades_acumuladas.csv', sep=";", index_col=None)

    # Obtén la lista de RUT únicos de la columna 'Run Fondo'
    runs = df['Run Fondo'].unique()

    # Filtrar por fecha y run seleccionado usando la función query
    df_filtrado = df.query(f"fecha == '{fecha_datepicker_formatted}' and `Run Fondo` == {run_selected}")

    # Revisar infoS
    print(df)
    print(df_filtrado)
    print(f"Fecha seleccionada: {fecha_datepicker}")
    print(f"RUT seleccionado: {run_selected}")

    # Crear el gráfico de barras con Plotly Express utilizando el DataFrame filtrado
    fig = px.bar(df_filtrado, x='periodo', y='rent_acumulada', title=f'Rentabilidad Acumulada a lo largo del tiempo para el fondo {run_selected} en la fecha {fecha_datepicker}')

    # Ajustar las etiquetas del eje y para agregar el símbolo de porcentaje
    fig.update_layout(yaxis_tickformat='.2%')
    
    # Convierte el gráfico a un formato HTML
    grafico_html = fig.to_html(full_html=False)

    return render_template('rent_graf.html', fecha=fecha_datepicker, runs=runs, grafico_html=grafico_html)


@app.route('/detalle-fondo/<run>', methods=['POST','GET'])
def detalle_fondo(run):
    print(run)
    return render_template('detalle-fondo.html', table_data=get_detalle_fondo(run), table_series=get_series(run))

# Funciones
def get_rentabilidades(df):
    df['Run Fondo'] = df["Run Fondo"].apply(crear_enlace)
    html_table = df.to_html(classes='table', index=False, escape=False)
    return html_table

def get_detalle_fondo(run):
    df = pd.read_csv('uploads/detalle_fondo.csv', sep=";", index_col=None)
    df['Run Fondo'] = df['Run Fondo'].astype(str)
    df = df[df['Run Fondo'] == run]
    html_table = df.to_html(classes='table', index=False, escape=False)
    return html_table

def get_series(run):
    df = pd.read_csv('uploads/series.csv', sep=";", index_col=None)
    df['Run Fondo'] = df['Run Fondo'].astype(str)
    df = df[df['Run Fondo'] == run]
    html_table = df.to_html(classes='table', index=False, escape=False)
    return html_table

def get_portafolio(run, tipo_cartera, fecha):
    df = pd.read_csv(f'uploads/portafolio_{tipo_cartera}.csv', sep=";", index_col=None)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
    df['Run Fondo'] = df['Run Fondo'].astype(str)
    df = df[df['Run Fondo'] == run]
    df = df[df['fecha'] == fecha]
    df['Run Fondo'] = df["Run Fondo"].apply(crear_enlace)

    if df.empty:
        html_table = '<p>No hay información para el periodo seleccionado</p>'
    else:
        html_table = df.to_html(classes='form-table', index=False, escape=False)
    return html_table

def crear_enlace(run):
    html = f'<a id="aunder" onclick="submitForm(\'{run}\')" name="{run}" value="{run}">{run}</a>'
    html += f'<input type="hidden" name="run" value="{run}">'
    return html

def ultimo_dia_del_mes(fecha):
    # Obtener el último día del mes
    ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]

    # Crear una nueva fecha con el último día del mes
    fecha_cierre_mes = datetime(fecha.year, fecha.month, ultimo_dia)

    return fecha_cierre_mes

if __name__ == '__main__':
    app.run(debug=True)
