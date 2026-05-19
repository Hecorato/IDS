# IDS

# Dashboard IDS 📊

Dashboard interactivo para el análisis de tickets de soporte de fibra óptica, desarrollado con Python y Streamlit.

## 🚀 Demo

[Ver aplicación](https://lejuccupjb76btyal2dd37.streamlit.app)

## 📋 Descripción

Sistema de Business Intelligence que permite analizar el ingreso diario de tickets de soporte, identificar fallas por cluster y hacer drill-down por día para ver causas y soluciones.

## ✨ Funcionalidades

- 🔐 Login con usuario y contraseña por persona
- 📅 Filtros de calendario con agrupación por Día, Semana o Mes
- 📈 Gráfica histórica de tickets con curvas suaves
- 🖱️ Drill-down — click en un día navega al detalle
- 🏘️ Vista de detalle con tickets por cluster
- ⚠️ Gráficas de causas y soluciones
- ⚙️ Página de administración para carga de datos diaria
- 🔄 Pipeline automático que filtra clusters y fusiona datasets

## 🛠️ Stack tecnológico

- **Python** — lenguaje base
- **Pandas** — manipulación y análisis de datos
- **Plotly Express** — gráficas interactivas
- **Streamlit** — framework de la app web
- **GitHub** — control de versiones
- **Streamlit Cloud** — despliegue en la nube

## 📁 Arquitectura
IDS/
├── app.py                  ← punto de entrada
├── components/
│   ├── auth.py             ← autenticación
│   ├── filtros.py          ← filtros globales
│   └── tickets.py          ← gráfica histórica
├── data/
│   ├── loader.py           ← carga y filtra datos
│   └── merger.py           ← merge tickets + soluciones
├── pages/
│   ├── admin.py            ← carga de archivos diaria
│   └── detalle.py          ← vista drill-down
└── requirements.txt

## ⚙️ Instalación local

```bash
git clone https://github.com/Hecorato/IDS.git
cd IDS
pip install -r requirements.txt
streamlit run app.py
```

## 📦 Dependencias
pandas
plotly
streamlit
openpyxl
xlrd

## 🔄 Flujo de actualización de datos

1. Descargar reporte diario en formato `.xls`
2. Entrar a la página **Admin** del dashboard
3. Subir el archivo en la sección correspondiente
4. Click en **Actualizar dashboard**
5. El sistema filtra clusters, fusiona con histórico y actualiza automáticamente

## 👤 Autor

**Héctor Garnica** — [@Hecorato](https://github.com/Hecorato)
