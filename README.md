# Disaster Dashboard – DisoPortal 🌍

An interactive disaster monitoring dashboard built with **Django**, **Leaflet.js**, and **Chart.js** that visualizes real-time and historical data for various natural disasters, including **earthquakes**, **landslides**, and more.

---

## 🚀 Features

- **Interactive Maps**: View disaster events on an interactive Leaflet map.
- **Dynamic Charts**: Visualize disaster statistics with bar charts, pie charts, and trend graphs.
- **Year-Based Filtering**: Filter earthquake and landslide events by year for focused analysis.
- **Metadata Summary**: Quick statistics and key insights about displayed disasters.
- **Custom CSV Upload**: Upload your own spatial dataset to visualize points on the map.
- **Trigger-Based Analysis**: Understand disaster triggers through pie chart breakdowns.
- **Responsive Design**: Works across desktops and tablets.

---

## 🛠️ Technologies Used

- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL with PostGIS
- **Frontend**: HTML, CSS, JavaScript, Leaflet.js, Chart.js
- **Data Processing**: Python (Pandas, GeoPandas)
- **Visualization**: Leaflet maps, Chart.js graphs
- **Others**: GDAL, GeoDjango

---

## 📂 Project Structure

disaster-dashboard-disportal/  
│  
├── disaster/ # Main Django app  
│   ├── templates/ # HTML templates  
│   ├── static/ # Static files (CSS, JS, images)  
│   ├── views.py # API & page logic  
│   ├── models.py # Database models  
│  
├── .gitignore # Ignored files and folders  
├── README.md # Project documentation  

---

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/afifaabbasi08/disaster-dashboard-disportal.git
cd disaster-dashboard-disportal




