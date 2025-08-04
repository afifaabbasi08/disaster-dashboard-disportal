# disaster_data/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json, re, psycopg2, requests
from django.contrib import messages


# ------------------ OLLAMA CONFIG ------------------
OLLAMA_URL = "http://localhost:11434/api/generate"

# ------------------ DATABASE CONFIG ----------------
DB_CONFIG = {
    "dbname": "disaster_db ",  # 🚨 removed space
    "user": "postgres",
    "password": "abbasi08",
    "host": "localhost",
    "port": "5432"
}

def ask_ollama(prompt):
    payload = {"model": "llama3.1", "prompt": prompt, "stream": False}
    res = requests.post(OLLAMA_URL, json=payload)
    return res.json()["response"]

def run_postgis_query(sql):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

from django.shortcuts import render

def chatbot_page(request):
    return render(request, "chatbot.html")

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        user_question = data.get("message", "").strip()
        if not user_question:
            return JsonResponse({"reply": "⚠️ Please enter a question."}, status=400)
    except Exception:
        return JsonResponse({"reply": "⚠️ Invalid JSON format."}, status=400)

    # Build LLM prompt
    llm_prompt = f"""
You are a GIS database assistant. Return ONLY a valid SQL query for my PostGIS database.
No explanations, no comments, no markdown.

Database tables:

earthquake_data(
    time INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    mag DOUBLE PRECISION,
    place TEXT,
    id TEXT
)

disaster_landslide(
    event_id INTEGER,
    event_title TEXT,
    event_description TEXT,
    location_description TEXT,
    location_accuracy TEXT,
    landslide_category TEXT,
    landslide_trigger TEXT,
    landslide_size TEXT,
    fatality_count INTEGER,
    injury_count INTEGER,
    event_import_id TEXT,
    country_name TEXT
)

hurricane_data(
    sid VARCHAR,
    number INTEGER,
    basin VARCHAR,
    subbasin VARCHAR,
    iso_time TIMESTAMP WITHOUT TIME ZONE,
    nature VARCHAR,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION
)

Rules:
- Only query ONE table unless the user explicitly requests combining multiple datasets.
- For earthquakes, use to_timestamp(time) for date filtering.
- Always use date format 'YYYY-MM-DD' in SQL.   <-- ✅ Added here
- For spatial queries, use ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) for earthquakes.
- Use ILIKE for text matches.
- Use BETWEEN for date ranges.
- Return only the SQL.

Question: {user_question}
"""

    # Step 1: Get SQL from Ollama
    raw_sql = ask_ollama(llm_prompt).strip()
    match = re.search(r"(SELECT|WITH).*", raw_sql, re.S | re.I)
    sql_query = match.group(0).strip() if match else raw_sql
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    try:
        # Step 2: Run SQL
        results = run_postgis_query(sql_query)

        # Step 3: Make a friendly answer
        friendly_prompt = f"""
The user asked: "{user_question}"
The database returned these rows: {results}

Write a short, clear answer in plain English.
"""
        friendly_answer = ask_ollama(friendly_prompt)

        return JsonResponse({"reply": friendly_answer, "sql": sql_query})

    except Exception as e:
        return JsonResponse({"reply": f"⚠️ SQL Error: {str(e)}"}, status=400)



# 🔐 Authentication Views
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home-ui')
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'signup.html')

        User.objects.create_user(username=username, email=email, password=password1)
        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def get_all_disaster_types(request):
    """Get all disaster types including custom ones"""
    
    # Base disaster types
    disaster_types = [
        {
            "display_name": "Earthquake",
            "description": "Sudden ground shaking caused by tectonic movements.",
            "url": "/earthquakes/",
            "icon": "🌍",
            "color": "#00cccc",
            "is_new": False,
            "type": "builtin"
        },
        {
            "display_name": "Landslide",
            "description": "Mass movement of rock or soil down a slope.",
            "url": "/landslide-ui/",
            "icon": "⛰️",
            "color": "#00cccc",
            "is_new": False,
            "type": "builtin"
        },
        {
            "display_name": "Hurricane",
            "description": "Powerful storm systems with strong winds and rain.",
            "url": "/hurricane-ui/",
            "icon": "🌀",
            "color": "#00cccc",
            "is_new": False,
            "type": "builtin"
        }
    ]
    
    # Add custom disaster types (safely)
    try:
        from .models import CustomDisasterType
        from django.db import connection
        custom_disasters = CustomDisasterType.objects.filter(is_active=True)
        print(f"DEBUG: Found {custom_disasters.count()} custom disaster types")
        for disaster in custom_disasters:
            # Only show if the custom table exists and has data
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {disaster.table_name}")
                    count = cursor.fetchone()[0]
                if count > 0:
                    print(f"DEBUG: Adding custom disaster: {disaster.name} -> {disaster.display_name} (count={count})")
                    disaster_types.append({
                        "display_name": disaster.display_name,
                        "description": disaster.description or f"Custom {disaster.name} data",
                        "url": f"/view-table/{disaster.name.lower()}/",
                        "icon": disaster.icon,
                        "color": disaster.color,
                        "is_new": True,
                        "type": "custom",
                        "table_name": disaster.table_name
                    })
                else:
                    print(f"DEBUG: Skipping custom disaster {disaster.name} (no data)")
            except Exception as e:
                print(f"Warning: Could not check data for custom disaster {disaster.name}: {e}")
                continue
    except Exception as e:
        print(f"Warning: Could not load custom disaster types: {e}")
        # Continue without custom types if there's an error
    
    return JsonResponse(disaster_types, safe=False)


# 🖥️ UI Views
def home_ui(request):
    context = {
        'total_earthquakes': 123,
        'total_landslides': 45,
        'last_updated': '2025-07-27'
    }
    return render(request, 'home_ui.html', context)


def earthquake_ui(request):
    return render(request, 'earthquake_ui.html')

def landslide_ui(request):
    return render(request, 'landslide_ui.html')

def hurricane_ui(request):
    return render(request, 'hurricane_ui.html')

def risk_landslide_future(request):
    return render(request, 'risk_landslide_future.html')

def map_view(request):
    return render(request, 'map_view.html')

def map_preview(request):
    return render(request, 'map_preview.html')

def my_uploads(request):
    datasets = UploadedDataset.objects.all()
    return render(request, 'my_uploads.html', {'datasets': datasets})

from django.http import JsonResponse
from django.db.models.functions import ExtractYear
from django.db.models import DateTimeField
from django.db.models.functions import Cast
from .models import EarthquakeData
import datetime
def available_earthquake_years(request):
    years = (
        EarthquakeData.objects
        .values_list('time', flat=True)
        .distinct()
        .order_by('-time')
    )
    return JsonResponse(list(years), safe=False)


from django.http import JsonResponse
from .models import EarthquakeData

import datetime

from django.http import JsonResponse
from .models import EarthquakeData
import datetime

from django.http import JsonResponse
from .models import EarthquakeData

def earthquake_data_api(request):
    try:
        year = request.GET.get('year')  # read from query string
        earthquakes = EarthquakeData.objects.all()

        if year:
            earthquakes = earthquakes.filter(time=int(year))  # since time stores the year

        earthquakes = earthquakes[:5000]  # limit for performance


        data = []
        for eq in earthquakes:
            if eq.latitude is not None and eq.longitude is not None:
                data.append({
                    "id": eq.id,
                    "time": eq.time,
                    "latitude": float(eq.latitude),
                    "longitude": float(eq.longitude),
                    "mag": float(eq.mag) if eq.mag is not None else 0,
                    "place": eq.place or "Unknown"
                })

        return JsonResponse(data, safe=False)

    except Exception as e:
        print(f"❌ ERROR in earthquake_data_api: {e}")
        return JsonResponse([], safe=False)


def latest_earthquake_news(request):
    data = list(EarthquakeData.objects.order_by('-time')[:5].values())
    return JsonResponse(data, safe=False)

def download_earthquake_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="earthquakes.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'time', 'latitude', 'longitude', 'mag', 'place'])
    for e in EarthquakeData.objects.all():
        writer.writerow([e.id, e.time, e.latitude, e.longitude, e.mag, e.place])
    return response

from django.http import JsonResponse
from .models import LandslideEvent
from django.core.serializers import serialize
from django.db.models.functions import ExtractYear
import json


# 🏔️ Landslide APIs
def landslide_data_api(request):
    """Get landslide data in GeoJSON format"""
    # Get filter parameters
    year = request.GET.get('year')
    trigger = request.GET.get('trigger')
    
    # Start with all landslides
    landslides = LandslideEvent.objects.all()
    
    # Apply filters
    if year and year != 'all':
        landslides = landslides.filter(event_date__year=int(year))
    if trigger and trigger != 'all':
        landslides = landslides.filter(landslide_trigger__iexact=trigger)
    
    # Convert to GeoJSON
    features = []
    for landslide in landslides:
        # Skip if coordinates are None or invalid
        if landslide.latitude is None or landslide.longitude is None:
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(landslide.longitude), float(landslide.latitude)]
            },
            "properties": {
                "event_id": landslide.event_id,
                "event_title": landslide.event_title or "Unknown",
                "event_date": landslide.event_date.strftime('%Y-%m-%d') if landslide.event_date else "N/A",
                "landslide_trigger": landslide.landslide_trigger or "Unknown",
                "landslide_category": landslide.landslide_category or "Unknown",
                "country_name": landslide.country_name or "Unknown",
                "fatality_count": landslide.fatality_count or 0,
                "injury_count": landslide.injury_count or 0
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return JsonResponse(geojson)


def landslide_triggers_api(request):
    """Get available trigger types for landslides"""
    triggers = LandslideEvent.objects.exclude(
        landslide_trigger__isnull=True
    ).exclude(
        landslide_trigger__exact=''
    ).values_list('landslide_trigger', flat=True).distinct()
    
    trigger_list = list(triggers)
    return JsonResponse(trigger_list, safe=False)


def landslide_risk_score_api(request):
    """Calculate landslide risk scores using machine learning"""
    try:
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        
        # Get all landslide data
        landslides = LandslideEvent.objects.all()
        
        # Prepare data for clustering
        data = []
        valid_landslides = []
        
        for landslide in landslides:
            if (landslide.latitude is not None and 
                landslide.longitude is not None and 
                landslide.latitude != 0 and 
                landslide.longitude != 0):
                
                data.append([
                    float(landslide.latitude),
                    float(landslide.longitude)
                ])
                valid_landslides.append(landslide)
        
        if len(data) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Insufficient data for risk analysis'
            })
        
        # Convert to numpy array
        X = np.array(data)
        
        # Scale the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform DBSCAN clustering
        dbscan = DBSCAN(eps=0.1, min_samples=3)
        clusters = dbscan.fit_predict(X_scaled)
        
        # Calculate risk scores based on cluster density
        unique_clusters = set(clusters)
        risk_scores = {}
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Noise points
                continue
                
            cluster_points = X[clusters == cluster_id]
            cluster_landslides = [valid_landslides[i] for i, c in enumerate(clusters) if c == cluster_id]
            
            # Calculate risk factors
            density = len(cluster_points)
            avg_fatalities = np.mean([ls.fatality_count or 0 for ls in cluster_landslides])
            avg_injuries = np.mean([ls.injury_count or 0 for ls in cluster_landslides])
            
            # Risk score based on density and casualties
            risk_score = (density * 0.4 + avg_fatalities * 0.3 + avg_injuries * 0.3) / 10
            
            # Store cluster center and risk score
            center_lat = np.mean(cluster_points[:, 0])
            center_lng = np.mean(cluster_points[:, 1])
            
            risk_scores[f"cluster_{cluster_id}"] = {
                "center": [center_lng, center_lat],
                "risk_score": round(risk_score, 2),
                "density": density,
                "avg_fatalities": round(avg_fatalities, 1),
                "avg_injuries": round(avg_injuries, 1)
            }
        
        return JsonResponse({
            'success': True,
            'risk_scores': risk_scores,
            'total_clusters': len(risk_scores),
            'total_points': len(valid_landslides)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error calculating risk scores: {str(e)}'
        })


def landslide_api(request):
    year = request.GET.get('year')
    landslides = LandslideEvent.objects.all()
    if year:
        landslides = landslides.filter(event_date__year=year)

    triggers = list(
        landslides.values_list('landslide_trigger', flat=True).distinct()
    )

    geojson = serialize('geojson', landslides)
    geojson_dict = json.loads(geojson)
    geojson_dict['triggers'] = triggers
    return JsonResponse(geojson_dict)


def triggers_api(request):
    year = request.GET.get('year')
    landslides = LandslideEvent.objects.all()
    if year:
        landslides = landslides.filter(event_date__year=year)

    triggers = list(landslides.values_list('landslide_trigger', flat=True).distinct())
    return JsonResponse(triggers, safe=False)


def available_years_by_trigger(request):
    """Get available years for landslides filtered by trigger type"""
    trigger = request.GET.get('trigger')
    if trigger:
        years = LandslideEvent.objects.filter(landslide_trigger=trigger).dates('event_date', 'year')
    else:
        years = LandslideEvent.objects.dates('event_date', 'year')
    
    year_list = [y.year for y in years]
    return JsonResponse(year_list, safe=False)


def landslide_yearly_counts(request):
    data = LandslideEvent.objects.annotate(
        year=ExtractYear('event_date')
    ).values('year').annotate(count=Count('event_id')).order_by('year')
    return JsonResponse(list(data), safe=False)

def download_landslide_csv(request):
    return download_csv_response(LandslideEvent, "landslides.csv")

# 🌪️ Hurricane APIs
from django.http import JsonResponse
from .models import HurricaneData

def hurricane_data_api(request):
    try:
        basin_filter = request.GET.get('basin')  # ✅ Get basin from query string

        hurricanes = HurricaneData.objects.all()

        if basin_filter:
            hurricanes = hurricanes.filter(basin=basin_filter)  # ✅ Filter by basin

        count = hurricanes.count()
        print(f"DEBUG: Found {count} hurricane records after filtering")

        if count == 0:
            return JsonResponse([], safe=False)

        data = []
        for h in hurricanes:
            if h.lat is not None and h.lon is not None:
                year = h.iso_time.year if h.iso_time else None
                data.append({
                    "id": h.sid,
                    "year": year,
                    "latitude": float(h.lat),
                    "longitude": float(h.lon),
                    "basin": h.basin or "Unknown",
                    "subbasin": h.subbasin or "Unknown",
                    "nature": h.nature or "Unknown",
                    "iso_time": h.iso_time.isoformat() if h.iso_time else None
                })

        print(f"DEBUG: Returning {len(data)} hurricane points to map")
        return JsonResponse(data, safe=False)

    except Exception as e:
        print(f"DEBUG: Error in hurricane_data_api: {e}")
        return JsonResponse([], safe=False)


def download_hurricane_csv(request):
    return download_csv_response(HurricaneData, "hurricanes.csv")


import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect
from .models import LocationPoint

# 🔧 Safe conversion helpers for CSV upload
def safe_int(val):
    """Safely convert value to integer, handling floats and empty values"""
    try:
        if val is None or val == '':
            return None
        return int(float(val))
    except (ValueError, TypeError):
        return None

def safe_float(val):
    """Safely convert value to float, handling empty values"""
    try:
        if val is None or val == '':
            return None
        return float(val)
    except (ValueError, TypeError):
        return None

def safe_date(val):
    """Safely parse date from various formats"""
    if not val:
        return None
    date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
    for fmt in date_formats:
        try:
            return datetime.strptime(str(val), fmt)
        except ValueError:
            continue
    return None

def upload_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        if not csv_file:
            return render(request, 'upload_csv.html', {'error': 'No file selected.'})

        decoded = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded)
        reader = csv.DictReader(io_string)

        # Only check required columns, since you have 33 columns
        required_columns = {'event_title', 'longitude', 'latitude'}
        if not required_columns.issubset(set(reader.fieldnames)):
            return render(request, 'upload_csv.html', {
                'error': f"❌ Required columns missing. Must include: {required_columns}"
            })

        success_count = 0
        skipped_count = 0

        for row in reader:
            try:
                name = row.get('event_title') or None

                # Use the last "date" column (not event_date)
                date_str = row.get('date', '').strip()
                date = None
                if date_str:
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        print(f"⚠️ Invalid date format: {date_str}")
                        date = None

                latitude = float(row['latitude'])
                longitude = float(row['longitude'])

                LocationPoint.objects.create(
                    name=name,
                    date=date,
                    latitude=latitude,
                    longitude=longitude
                )
                success_count += 1
            except Exception as e:
                print(f"❌ Skipped row due to error: {e}")
                skipped_count += 1
                continue

        # ✅ Save this upload in UploadedDataset for "My Uploads"
        from .models import UploadedDataset
        UploadedDataset.objects.create(
            name=csv_file.name,
            category='custom'  # you can change this label if you want
        )

        return render(request, 'upload_csv.html', {
            'message': f"✅ Uploaded {success_count} points. ❌ Skipped {skipped_count} rows."
        })

    return render(request, 'upload_csv.html')


def upload_any_csv(request):
    """Flexible upload function that handles any CSV and saves to a model or table"""
    from .models import LandslideEvent, UploadedDataset, CustomDisasterType
    from django.db import connection
    import json

    if request.method == 'POST':
        try:
            csv_file = request.FILES['file']
            disaster_type = request.POST.get('disaster_type', 'other')
            custom_name = request.POST.get('custom_name', '').strip()
            custom_display_name = request.POST.get('custom_display_name', '').strip()
            custom_description = request.POST.get('custom_description', '').strip()
            custom_icon = request.POST.get('custom_icon', '🌋')
            custom_color = request.POST.get('custom_color', '#ff6600')

            decoded = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded)
            reader = csv.DictReader(io_string)
            fieldnames = reader.fieldnames
            
            print(f"DEBUG: CSV columns found: {fieldnames}")
            print(f"DEBUG: Number of columns: {len(fieldnames)}")
            
            # Print first row to see the data structure
            first_row = next(reader)
            print(f"DEBUG: First row data: {dict(first_row)}")
            
            # Reset reader to start from beginning
            io_string.seek(0)
            reader = csv.DictReader(io_string)

            uploaded_count = 0
            skipped_count = 0
            error_details = []
            collected_years = set()

            # Determine the target table
            if disaster_type == 'other':
                if not custom_name:
                    return JsonResponse({'success': False, 'message': 'Please provide a name for the new disaster type'})

                # Use the correct table naming convention for Django
                table_name = f"disaster_data_customdisastertype_{custom_name.lower().replace(' ', '_')}"
                display_name = custom_display_name or f"{custom_name.title()} Events"

                # Create CustomDisasterType
                custom_disaster, created = CustomDisasterType.objects.get_or_create(
                    name=custom_name,
                    defaults={
                        'display_name': display_name,
                        'description': custom_description,
                        'table_name': table_name,
                        'icon': custom_icon,
                        'color': custom_color,
                        'is_active': True
                    }
                )
                
                print(f"DEBUG: CustomDisasterType created: {created}")
                print(f"DEBUG: CustomDisasterType name: {custom_disaster.name}")
                print(f"DEBUG: CustomDisasterType display_name: {custom_disaster.display_name}")
                print(f"DEBUG: CustomDisasterType is_active: {custom_disaster.is_active}")

                # Create the table with proper Django naming
                with connection.cursor() as cursor:
                    columns = []
                    for col in fieldnames:
                        col_clean = col.lower().replace(' ', '_').replace('-', '_')
                        if 'date' in col_clean:
                            columns.append(f"{col_clean} TIMESTAMP")
                        elif 'lat' in col_clean or 'lon' in col_clean:
                            columns.append(f"{col_clean} DOUBLE PRECISION")
                        elif any(k in col_clean for k in ['id', 'count', 'number']):
                            columns.append(f"{col_clean} INTEGER")
                        else:
                            columns.append(f"{col_clean} TEXT")

                    create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        {', '.join(columns)}
                    )
                    """
                    print(f"DEBUG: Creating table with SQL: {create_table_sql}")
                    cursor.execute(create_table_sql)
                    connection.commit()
                    print(f"DEBUG: Table {table_name} created successfully")
                
                target_table = table_name
                use_model = False

            else:
                use_model = True
                target_table = 'disaster_landslide'

            # Begin upload
            with connection.cursor() as cursor:
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Debug: Print first few rows to see what we're getting
                        if row_num <= 5:
                            print(f"DEBUG: Row {row_num} - First 3 columns: {list(row.items())[:3]}")
                        
                        # Parse event_date
                        raw_date = row.get('event_date') or row.get('date') or row.get('Date')
                        parsed_date = None
                        if raw_date:
                         for fmt in [
                           '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%d',
                            '%m/%d/%Y %H:%M',  # your format
                            '%d/%m/%Y %H:%M',
                            '%m/%d/%Y',
                            '%d/%m/%Y',
                            '%Y/%m/%d',
                            '%d-%m-%Y',
                            '%m-%d-%Y'
                        ]:
                            try:
                              parsed_date = datetime.strptime(raw_date, fmt)
                              break
                            except (ValueError, TypeError):
                              continue


                        # For custom tables, we'll handle coordinates differently
                        if use_model:
                            # For built-in disaster types, check coordinates
                            latitude = row.get('latitude') or row.get('lat')
                            longitude = row.get('longitude') or row.get('lng') or row.get('long')

                            if not latitude or not longitude:
                                print(f"DEBUG: Row {row_num} skipped - no coordinates. lat={latitude}, lng={longitude}")
                                skipped_count += 1
                                error_details.append(f"Row {row_num}: Missing lat/lng")
                                continue

                            lat = float(latitude)
                            lng = float(longitude)
                            if abs(lat) > 90 or abs(lng) > 180:
                                print(f"DEBUG: Row {row_num} skipped - invalid coordinates. lat={lat}, lng={lng}")
                                skipped_count += 1
                                error_details.append(f"Row {row_num}: Invalid coordinate range")
                                continue
                        else:
                            # For custom tables, we'll check coordinates during processing
                            pass

                        if use_model: # This branch is for LandslideEvent
                            # Map CSV columns to actual database columns
                            column_mapping = {
                                'event_id': 'event_import_id',
                                'event_title': 'event_title', 
                                'event_description': 'event_description',
                                'location_description': 'location_description',
                                'landslide_category': 'landslide_category',
                                'landslide_trigger': 'landslide_trigger',
                                'landslide_size': 'landslide_size',
                                'fatality_count': 'fatality_count',
                                'injury_count': 'injury_count',
                                'country_name': 'country_name',
                                'country_code': 'country_code',
                                'latitude': 'latitude',
                                'longitude': 'longitude',
                                'event_date': 'event_date'
                            }
                            
                            # Build the SQL insert with correct column names
                            columns = []
                            values = []
                            placeholders = []
                            
                            for csv_col, db_col in column_mapping.items():
                                if csv_col in row:
                                    columns.append(db_col)
                                    val = row[csv_col]
                                    if csv_col in ['fatality_count', 'injury_count']:
                                        val = safe_int(val)
                                    elif csv_col in ['latitude', 'longitude']:
                                        val = safe_float(val)
                                    elif csv_col == 'event_date':
                                        val = parsed_date
                                    values.append(val)
                                    placeholders.append('%s')
                            
                            if columns:  # Only insert if we have valid columns
                                sql = f"INSERT INTO disaster_landslide ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                                cursor.execute(sql, values)
                        else: # This branch is for custom tables
                            # Generic insert into dynamic table
                            columns = []
                            values = []
                            placeholders = []
                            
                            print(f"DEBUG: Processing custom table row {row_num}")
                            print(f"DEBUG: Fieldnames: {fieldnames}")
                            print(f"DEBUG: Row data: {dict(row)}")
                            
                            # Check if we have any coordinate columns
                            has_coordinates = False
                            lat_col = None
                            lon_col = None
                            
                            for col in fieldnames:
                                clean_col = col.lower().replace(' ', '_').replace('-', '_')
                                if 'lat' in clean_col:
                                    lat_col = col
                                elif 'lon' in clean_col or 'lng' in clean_col:
                                    lon_col = col
                            
                            if lat_col and lon_col:
                                lat_val = row.get(lat_col)
                                lon_val = row.get(lon_col)
                                if lat_val and lon_val:
                                    try:
                                        lat_float = float(lat_val)
                                        lon_float = float(lon_val)
                                        if abs(lat_float) <= 90 and abs(lon_float) <= 180:
                                            has_coordinates = True
                                        else:
                                            print(f"DEBUG: Row {row_num} skipped - invalid coordinates")
                                            skipped_count += 1
                                            error_details.append(f"Row {row_num}: Invalid coordinate range")
                                            continue
                                    except ValueError:
                                        print(f"DEBUG: Row {row_num} skipped - non-numeric coordinates")
                                        skipped_count += 1
                                        error_details.append(f"Row {row_num}: Non-numeric coordinates")
                                        continue
                            
                            for col in fieldnames:
                                clean_col = col.lower().replace(' ', '_').replace('-', '_')
                                val = row.get(col, '')
                                
                                # Handle different data types
                                if 'date' in clean_col and val:
                                    # Try to parse date
                                    try:
                                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                                            try:
                                                parsed_date = datetime.strptime(val, fmt)
                                                val = parsed_date.strftime('%Y-%m-%d')
                                                break
                                            except ValueError:
                                                continue
                                    except:
                                        pass
                                elif any(k in clean_col for k in ['lat', 'lon', 'lng']) and val:
                                    try:
                                        val = float(val)
                                    except ValueError:
                                        val = None
                                elif any(k in clean_col for k in ['id', 'count', 'number']) and val:
                                    try:
                                        val = int(val)
                                    except ValueError:
                                        val = None
                                
                                columns.append(clean_col)
                                placeholders.append('%s')
                                values.append(val if val != '' else None)

                            if columns:  # Only insert if we have valid columns
                                sql = f"INSERT INTO {target_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                                print(f"DEBUG: Custom table insert SQL: {sql}")
                                print(f"DEBUG: Values: {values}")
                                cursor.execute(sql, values)
                            else:
                                print(f"DEBUG: No valid columns found for row {row_num}")
                                skipped_count += 1
                                error_details.append(f"Row {row_num}: No valid columns")
                                continue

                        if parsed_date:
                            collected_years.add(parsed_date.year)

                        uploaded_count += 1

                    except Exception as e:
                        skipped_count += 1
                        error_details.append(f"Row {row_num}: {str(e)}")
                        continue

                connection.commit()

            # Save uploaded dataset
            if disaster_type == 'other':
                # Use the custom disaster name for the category
                UploadedDataset.objects.create(name=csv_file.name, category=custom_name)
            else:
                UploadedDataset.objects.create(name=csv_file.name, category=disaster_type)

            # Add new years to dropdown model (if any) - REMOVED LandslideYear reference
            # from .models import LandslideYear
            # for year in collected_years:
            #     LandslideYear.objects.get_or_create(year=year)

            message = f"Uploaded {uploaded_count} records. Skipped {skipped_count}."
            if uploaded_count > 0:
                if disaster_type == 'other':
                    # For custom disaster types, link to the view-table with the custom name
                    message += f' <a href="/view-table/{custom_name.lower()}/" target="_blank" style="color: #00ffff;">View on Map</a>'
                    message += f' <br><small style="color: #00ff00;">✅ New "{display_name}" card added to homepage!</small>'
                    message += f' <br><small style="color: #00ffff;">💡 <a href="/home/" onclick="loadDynamicDisasterCards(); return false;">Refresh Homepage</a> to see the new card!</small>'
                else:
                    # Create a unique identifier for this upload session
                    upload_session_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    message += f' <a href="/view-uploaded-data/{disaster_type}/{upload_session_id}/" target="_blank" style="color: #00ffff;">View on Map</a>'

            return JsonResponse({
                'success': True,
                'message': message,
                'uploaded_count': uploaded_count,
                'skipped_count': skipped_count,
                'errors': error_details[:10]
            })

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'message': f'Upload failed: {str(e)}'}, status=500)

    return render(request, 'upload_any_csv.html')

def download_csv_response(model, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    fields = [field.name for field in model._meta.fields]
    writer.writerow(fields)
    for obj in model.objects.all():
        writer.writerow([getattr(obj, f) for f in fields])
    return response

def preview_csv_api(request):
    if request.method == 'POST':
        csv_file = request.FILES['file']
        decoded = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded)
        reader = csv.reader(io_string)
        data = list(reader)
        return JsonResponse({'preview': data[:5]})

def location_data_api(request):
    data = list(LocationPoint.objects.values())
    return JsonResponse(data, safe=False)

def save_table(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        UploadedDataset.objects.create(name=name, category=category)
        return JsonResponse({'message': 'Saved successfully'})

def view_table(request, table_name):
    """View uploaded dataset on a map based on the dataset name"""
    try:
        # First check if this is a custom disaster type
        from .models import UploadedDataset, CustomDisasterType
        
        # Check if table_name matches a custom disaster type
        custom_disaster = CustomDisasterType.objects.filter(name__iexact=table_name).first()
        
        if custom_disaster:
            # This is a custom disaster type
            disaster_type = custom_disaster.name.lower()
            dataset = {
                'name': custom_disaster.display_name,
                'category': custom_disaster.name,
                'upload_date': datetime.now()
            }
        else:
            # Get the dataset record to determine the category
            dataset = UploadedDataset.objects.filter(name=table_name).first()
            
            if not dataset:
                return JsonResponse({'error': f'Dataset "{table_name}" not found'}, status=404)
            
            disaster_type = dataset.category.lower()
        
        # Map dataset to the correct database table and show on map
        if disaster_type == 'landslide':
            # Get landslide data from the disaster_landslide table
            landslides = LandslideEvent.objects.all().order_by('-event_id')[:1000]
            
            # Convert to GeoJSON format
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for landslide in landslides:
                if landslide.latitude and landslide.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(landslide.longitude), float(landslide.latitude)]
                        },
                        "properties": {
                            "event_title": landslide.event_title or "Unknown",
                            "event_date": str(landslide.event_date) if landslide.event_date else "Unknown",
                            "location": landslide.location_accuracy or "Unknown",
                            "country": landslide.country_name or "Unknown",
                            "landslide_trigger": landslide.landslide_trigger or "Unknown",
                            "fatality_count": landslide.fatality_count or 0,
                            "injury_count": landslide.injury_count or 0
                        }
                    }
                    geojson_data["features"].append(feature)
            
            context = {
                'dataset': {
                    'name': dataset.name,
                    'category': dataset.category,
                    'upload_date': dataset.upload_date
                },
                'point_count': len(geojson_data["features"]),
                'geojson_data': json.dumps(geojson_data)
            }
            
            return render(request, 'view_dataset_map.html', context)
        
        elif custom_disaster:
            # Handle custom disaster types
            try:
                from django.db import connection
                
                # Get data from the custom table
                table_name = custom_disaster.table_name
                cursor = connection.cursor()
                
                # Get column names from the table
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
                columns = [row[0] for row in cursor.fetchall()]
                
                # Find latitude and longitude columns
                lat_col = None
                lon_col = None
                for col in columns:
                    col_lower = col.lower()
                    if 'lat' in col_lower:
                        lat_col = col
                    elif 'lon' in col_lower or 'lng' in col_lower:
                        lon_col = col
                
                if not lat_col or not lon_col:
                    return JsonResponse({'error': f'No latitude/longitude columns found in {table_name}'}, status=400)
                
                # Get data from the custom table
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")
                rows = cursor.fetchall()
                
                # Convert to GeoJSON format
                geojson_data = {
                    "type": "FeatureCollection",
                    "features": []
                }
                
                for row in rows:
                    try:
                        lat = float(row[columns.index(lat_col)])
                        lon = float(row[columns.index(lon_col)])
                        
                        if abs(lat) <= 90 and abs(lon) <= 180:
                            feature = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [lon, lat]
                                },
                                "properties": {col: str(row[columns.index(col)]) if row[columns.index(col)] is not None else "Unknown" 
                                             for col in columns}
                            }
                            geojson_data["features"].append(feature)
                    except (ValueError, TypeError, IndexError):
                        continue
                
                context = {
                    'dataset': {
                        'name': custom_disaster.display_name,
                        'category': custom_disaster.name,
                        'upload_date': datetime.now()
                    },
                    'point_count': len(geojson_data["features"]),
                    'geojson_data': json.dumps(geojson_data)
                }
                
                return render(request, 'view_dataset_map.html', context)
                
            except Exception as e:
                return JsonResponse({'error': f'Could not load custom disaster data: {str(e)}'}, status=400)
        
        elif disaster_type == 'earthquake':
            # Get earthquake data from the earthquake_data table
            earthquakes = EarthquakeData.objects.all().order_by('-id')[:1000]
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for earthquake in earthquakes:
                if earthquake.latitude and earthquake.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(earthquake.longitude), float(earthquake.latitude)]
                        },
                        "properties": {
                            "place": earthquake.place or "Unknown",
                            "time": str(earthquake.time) if earthquake.time else "Unknown",
                            "mag": earthquake.mag or 0,
                            "depth": earthquake.depth or 0
                        }
                    }
                    geojson_data["features"].append(feature)
            
            context = {
                'dataset': {
                    'name': dataset.name,
                    'category': dataset.category,
                    'upload_date': dataset.upload_date
                },
                'point_count': len(geojson_data["features"]),
                'geojson_data': json.dumps(geojson_data)
            }
            
            return render(request, 'view_dataset_map.html', context)
        
        elif disaster_type == 'hurricane':
            # Get hurricane data from the hurricane_data table
            hurricanes = HurricaneData.objects.all().order_by('-id')[:1000]
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for hurricane in hurricanes:
                if hurricane.lat and hurricane.lon:  # Note: HurricaneData uses lat/lon
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(hurricane.lon), float(hurricane.lat)]
                        },
                        "properties": {
                            "storm_name": hurricane.sid or "Unknown",
                            "iso_time": str(hurricane.iso_time) if hurricane.iso_time else "Unknown",
                            "nature": hurricane.nature or "Unknown",
                            "basin": hurricane.basin or "Unknown"
                        }
                    }
                    geojson_data["features"].append(feature)
            
            context = {
                'dataset': {
                    'name': dataset.name,
                    'category': dataset.category,
                    'upload_date': dataset.upload_date
                },
                'point_count': len(geojson_data["features"]),
                'geojson_data': json.dumps(geojson_data)
            }
            
            return render(request, 'view_dataset_map.html', context)
        
        else:
            # For custom disaster types, try to query the custom table
            from django.db import connection
            cursor = connection.cursor()
            
            try:
                # Try to get data from the custom table
                custom_table_name = f"disaster_data_customdisastertype_{disaster_type}"
                cursor.execute(f"SELECT * FROM {custom_table_name} LIMIT 1000")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to GeoJSON (assuming latitude/longitude columns exist)
                geojson_data = {
                    "type": "FeatureCollection",
                    "features": []
                }
                
                lat_col_idx = None
                lon_col_idx = None
                
                # Find latitude and longitude columns
                for i, col in enumerate(columns):
                    if 'lat' in col.lower():
                        lat_col_idx = i
                    elif 'lon' in col.lower() or 'lng' in col.lower():
                        lon_col_idx = i
                
                if lat_col_idx is not None and lon_col_idx is not None:
                    for row in rows:
                        try:
                            lat = float(row[lat_col_idx]) if row[lat_col_idx] else None
                            lon = float(row[lon_col_idx]) if row[lon_col_idx] else None
                            
                            if lat and lon:
                                feature = {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": [lon, lat]
                                    },
                                    "properties": {col: str(row[i]) if row[i] is not None else "Unknown" 
                                                 for i, col in enumerate(columns)}
                                }
                                geojson_data["features"].append(feature)
                        except (ValueError, TypeError):
                            continue
                
                context = {
                    'dataset': {
                        'name': dataset.name,
                        'category': dataset.category,
                        'upload_date': dataset.upload_date
                    },
                    'point_count': len(geojson_data["features"]),
                    'geojson_data': json.dumps(geojson_data)
                }
                
                return render(request, 'view_dataset_map.html', context)
                
            except Exception as e:
                return JsonResponse({'error': f'Could not load data for {disaster_type}: {str(e)}'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': f'Error loading dataset: {str(e)}'}, status=500)

def view_uploaded_data(request, disaster_type, session_id):
    """View uploaded data on a map"""
    try:
        if disaster_type == 'landslide':
            # Get the most recent landslide data (assuming it's the uploaded data)
            landslides = LandslideEvent.objects.all().order_by('-event_id')[:1000]  # Limit to 1000 for performance
            
            # Convert to GeoJSON format
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for landslide in landslides:
                if landslide.latitude and landslide.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(landslide.longitude), float(landslide.latitude)]
                        },
                        "properties": {
                            "event_title": landslide.event_title or "Unknown",
                            "event_date": str(landslide.event_date) if landslide.event_date else "Unknown",
                            "location": landslide.location_accuracy or "Unknown",
                            "country": landslide.country_name or "Unknown",
                            "landslide_trigger": landslide.landslide_trigger or "Unknown",
                            "fatality_count": landslide.fatality_count or 0,
                            "injury_count": landslide.injury_count or 0
                        }
                    }
                    geojson_data["features"].append(feature)
            
            context = {
                'dataset': {
                    'name': f'Uploaded {disaster_type.title()} Data',
                    'category': disaster_type,
                    'upload_date': datetime.now()
                },
                'point_count': len(geojson_data["features"]),
                'geojson_data': json.dumps(geojson_data)
            }
            
            return render(request, 'view_dataset_map.html', context)
        
        elif disaster_type == 'earthquake':
            # Handle earthquake data similarly
            earthquakes = EarthquakeData.objects.all().order_by('-id')[:1000]
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for earthquake in earthquakes:
                if earthquake.latitude and earthquake.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(earthquake.longitude), float(earthquake.latitude)]
                        },
                        "properties": {
                            "place": earthquake.place or "Unknown",
                            "time": str(earthquake.time) if earthquake.time else "Unknown",
                            "mag": earthquake.mag or 0,
                            "depth": earthquake.depth or 0
                        }
                    }
                    geojson_data["features"].append(feature)
            
            context = {
                'dataset': {
                    'name': f'Uploaded {disaster_type.title()} Data',
                    'category': disaster_type,
                    'upload_date': datetime.now()
                },
                'point_count': len(geojson_data["features"]),
                'geojson_data': json.dumps(geojson_data)
            }
            
            return render(request, 'view_dataset_map.html', context)
        
        elif disaster_type == 'hurricane':
            # Handle hurricane data similarly
            hurricanes = HurricaneData.objects.all().order_by('-id')[:1000]
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for hurricane in hurricanes:
                if hurricane.latitude and hurricane.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(hurricane.longitude), float(hurricane.latitude)]
                        },
                        "properties": {
                            "storm_name": hurricane.storm_name or "Unknown",
                            "iso_time": str(hurricane.iso_time) if hurricane.iso_time else "Unknown",
                            "nature": hurricane.nature or "Unknown",
                            "basin": hurricane.basin or "Unknown"
                        }
                    }
                    geojson_data["features"].append(feature)
            
            context = {
                'dataset': {
                    'name': f'Uploaded {disaster_type.title()} Data',
                    'category': disaster_type,
                    'upload_date': datetime.now()
                },
                'point_count': len(geojson_data["features"]),
                'geojson_data': json.dumps(geojson_data)
            }
            
            return render(request, 'view_dataset_map.html', context)
        
        else:
            # For custom disaster types, try to query the custom table
            from django.db import connection
            cursor = connection.cursor()
            
            # Try to get data from the custom table
            try:
                table_name = f"disaster_data_customdisastertype_{disaster_type}"
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to GeoJSON (assuming latitude/longitude columns exist)
                geojson_data = {
                    "type": "FeatureCollection",
                    "features": []
                }
                
                lat_col_idx = None
                lon_col_idx = None
                
                # Find latitude and longitude columns
                for i, col in enumerate(columns):
                    if 'lat' in col.lower():
                        lat_col_idx = i
                    elif 'lon' in col.lower() or 'lng' in col.lower():
                        lon_col_idx = i
                
                if lat_col_idx is not None and lon_col_idx is not None:
                    for row in rows:
                        try:
                            lat = float(row[lat_col_idx]) if row[lat_col_idx] else None
                            lon = float(row[lon_col_idx]) if row[lon_col_idx] else None
                            
                            if lat and lon:
                                feature = {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": [lon, lat]
                                    },
                                    "properties": {col: str(row[i]) if row[i] is not None else "Unknown" 
                                                 for i, col in enumerate(columns)}
                                }
                                geojson_data["features"].append(feature)
                        except (ValueError, TypeError):
                            continue
                
                context = {
                    'dataset': {
                        'name': f'Uploaded {disaster_type.title()} Data',
                        'category': disaster_type,
                        'upload_date': datetime.now()
                    },
                    'point_count': len(geojson_data["features"]),
                    'geojson_data': json.dumps(geojson_data)
                }
                
                return render(request, 'view_dataset_map.html', context)
                
            except Exception as e:
                return JsonResponse({'error': f'Could not load data for {disaster_type}: {str(e)}'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': f'Error loading uploaded data: {str(e)}'}, status=500)

# 🌐 Dynamic Disaster API
def dynamic_disaster_view(request, disaster_type):
    reports = DisasterReport.objects.filter(disaster_type=disaster_type)
    return render(request, 'dynamic_disaster_view.html', {'reports': reports})

def dynamic_disaster_api(request, disaster_type):
    data = list(DisasterReport.objects.filter(disaster_type=disaster_type).values())
    return JsonResponse(data, safe=False)

# Custom Disaster Views
def custom_disaster_view(request, disaster_type):
    """Handle custom disaster type views"""
    try:
        from .models import CustomDisasterType
        custom_disaster = CustomDisasterType.objects.get(name=disaster_type, is_active=True)
        
        # Get data from the custom table
        from django.db import connection
        cursor = connection.cursor()
        
        # Get column information
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{custom_disaster.table_name}' ORDER BY ordinal_position")
        columns = [row[0] for row in cursor.fetchall()]
        
        # Get sample data (first 100 rows)
        cursor.execute(f"SELECT * FROM {custom_disaster.table_name} LIMIT 100")
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        context = {
            'custom_disaster': custom_disaster,
            'data': data,
            'columns': columns,
            'disaster_type': disaster_type,
            'disaster_name': custom_disaster.display_name,
            'disaster_icon': custom_disaster.icon,
            'disaster_color': custom_disaster.color,
            'disaster_description': custom_disaster.description,
            'table_name': custom_disaster.table_name
        }
        
        return render(request, 'custom_disaster_view.html', context)
    except CustomDisasterType.DoesNotExist:
        # If custom disaster type doesn't exist, redirect to dynamic view
        return redirect('dynamic_disaster_view', disaster_type=disaster_type)
    except Exception as e:
        print(f"Error in custom_disaster_view: {e}")
        # Return empty context if there's an error
        context = {
            'custom_disaster': custom_disaster if 'custom_disaster' in locals() else None,
            'data': [],
            'columns': [],
            'disaster_type': disaster_type,
            'disaster_name': disaster_type.title(),
            'disaster_icon': '❓',
            'disaster_color': '#007BFF',
            'disaster_description': f'View {disaster_type.title()} data',
            'table_name': disaster_type
        }
        return render(request, 'custom_disaster_view.html', context)

def custom_disaster_data_api(request, disaster_name):
    """API endpoint for custom disaster data"""
    try:
        from .models import CustomDisasterType
        custom_disaster = CustomDisasterType.objects.get(name=disaster_name, is_active=True)
        
        # Query the custom table dynamically
        from django.db import connection
        cursor = connection.cursor()
        
        # Get data from the custom table
        cursor.execute(f"SELECT * FROM {custom_disaster.table_name} LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_available_disaster_types(request):
    """Get available disaster types for dropdown selection"""
    
    disaster_types = [
        {"value": "earthquake", "label": "🌍 Earthquake"},
        {"value": "landslide", "label": "⛰️ Landslide"},
        {"value": "hurricane", "label": "🌀 Hurricane"},
        {"value": "other", "label": "➕ Other (Create New)"}
    ]
    
    # Add custom disaster types (safely)
    try:
        from .models import CustomDisasterType
        custom_disasters = CustomDisasterType.objects.filter(is_active=True)
        for disaster in custom_disasters:
            disaster_types.append({
                "value": disaster.name.lower(),
                "label": f"{disaster.icon} {disaster.display_name}"
            })
    except Exception as e:
        print(f"Warning: Could not load custom disaster types for dropdown: {e}")
        # Continue without custom types if there's an error
    
    return JsonResponse(disaster_types, safe=False)

def get_disaster_image_url(disaster_type):
    image_urls = {
        'earthquake': 'https://img.icons8.com/ios-filled/50/ffffff/earthquakes.png',
        'landslide': 'https://img.icons8.com/ios-filled/50/ffffff/landslide.png',
        'hurricane': 'https://img.icons8.com/ios-filled/50/ffffff/hurricane.png',
        'volcano': 'https://img.icons8.com/ios-filled/50/ffffff/volcano.png',
        'tornado': 'https://img.icons8.com/ios-filled/50/ffffff/tornado.png',
        'flood': 'https://img.icons8.com/ios-filled/50/ffffff/floods.png',
        'wildfire': 'https://img.icons8.com/ios-filled/50/ffffff/fire-element.png',
        'tsunami': 'https://img.icons8.com/ios-filled/50/ffffff/tsunami.png',
        'drought': 'https://img.icons8.com/ios-filled/50/ffffff/drought.png',
        'avalanche': 'https://img.icons8.com/ios-filled/50/ffffff/avalanche.png'
    }
    return image_urls.get(disaster_type, 'https://img.icons8.com/ios-filled/50/ffffff/warning-shield.png')

# 🧪 Debugging
def debug_tables(request):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in cursor.fetchall()]
    return JsonResponse({'tables': tables})

from django.shortcuts import render, get_object_or_404, redirect
from .models import UploadedDataset

def delete_dataset(request, id):
    # Ensure the user is authorized to delete this dataset (optional but recommended)
    dataset = get_object_or_404(UploadedDataset, id=id)
    
    # Only allow deletion with a POST request for security
    if request.method == 'POST':
        dataset.delete()
        messages.success(request, f"Dataset '{dataset.name}' deleted successfully.")
        return redirect('my_uploads')  # Redirect back to the uploads page
    
    # If not a POST request, render confirmation page (optional)
    return render(request, 'delete_confirmation.html', {'dataset': dataset})

from django.shortcuts import render

def risk_landslide_future(request):
    return render(request, "risk_landslide_future.html")


from django.http import JsonResponse
from django.db.models import Avg, Count
from .models import LandslideEvent

def landslide_heatmap_api(request):
    year = request.GET.get('year', 'all')
    trigger = request.GET.get('trigger', 'all')

    qs = LandslideEvent.objects.all()

    if year != 'all':
        qs = qs.filter(event_date__year=year)
    if trigger != 'all':
        qs = qs.filter(landslide_trigger=trigger)

    # Filter out null coordinates
    qs = qs.filter(latitude__isnull=False, longitude__isnull=False)

    # Build JSON response
    data = []
    for l in qs:
        # Example: risk score = fatalities + injuries * 0.5
        risk_score = (l.fatality_count or 0) + (l.injury_count or 0) * 0.5
        data.append({
            "lat": float(l.latitude),
            "lon": float(l.longitude),
            "risk": float(risk_score)
        })

    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from .models import EarthquakeData
from django.db.models import Count

def earthquake_charts_api(request):
    # Example: Bar chart → Earthquakes per year
    yearly_data = (
        EarthquakeData.objects
        .values('time')  # Assuming `time` is the year field
        .annotate(count=Count('id'))
        .order_by('time')
    )
    bar_labels = [str(row['time']) for row in yearly_data]
    bar_values = [row['count'] for row in yearly_data]

    # Example: Pie chart → Magnitude categories
    pie_categories = {
        "Minor (<4.0)": EarthquakeData.objects.filter(mag__lt=4.0).count(),
        "Moderate (4-6)": EarthquakeData.objects.filter(mag__gte=4.0, mag__lt=6.0).count(),
        "Strong (6-8)": EarthquakeData.objects.filter(mag__gte=6.0, mag__lt=8.0).count(),
        "Major (>=8.0)": EarthquakeData.objects.filter(mag__gte=8.0).count(),
    }
    pie_labels = list(pie_categories.keys())
    pie_values = list(pie_categories.values())

    return JsonResponse({
        "bar": {"labels": bar_labels, "values": bar_values},
        "pie": {"labels": pie_labels, "values": pie_values}
    })

import io
import csv
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Known disasters + emojis
ICON_MAP = {
    "earthquake": "🌍",
    "landslide": "⛰️",
    "hurricane": "🌀",
    "tsunami": "🌊",
    "wildfire": "🔥",
    "volcano": "🌋",
    "flood": "🌊",
    "storm": "⛈️",
    "tornado": "🌪️",
    "glof": "💧"
}

@csrf_exempt
def upload_csv_generic(request, disaster_type):
    """Generic CSV uploader for all disasters."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Only POST allowed"}, status=405)

    csv_file = request.FILES.get('file')
    if not csv_file:
        return JsonResponse({"success": False, "message": "No CSV file provided"}, status=400)

    # Normalize table name
    disaster_type = disaster_type.lower().replace(" ", "_")

    # Read CSV
    data = csv_file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(data))

    # Check if table exists
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, [disaster_type])
        table_exists = cursor.fetchone()[0]

    # Create table if it doesn't exist
    if not table_exists:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE {disaster_type} (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    date DATE,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION
                );
            """)

    # Insert rows
    inserted_count = 0
    with connection.cursor() as cursor:
        for row in csv_reader:
            cursor.execute(f"""
                INSERT INTO {disaster_type} (name, date, latitude, longitude)
                VALUES (%s, %s, %s, %s)
            """, [
                row.get('name'),
                row.get('date'),
                row.get('latitude'),
                row.get('longitude')
            ])
            inserted_count += 1

    return JsonResponse({
        "success": True,
        "message": f"Inserted {inserted_count} rows into table '{disaster_type}'."
    })

def api_disaster_types(request):
    """Fetch specific disaster tables with icons, display names, and descriptions."""
    
    # Define the specific disaster tables we want to show
    disaster_table_configs = {
        'earthquake_data': {
            'icon': '🌍',
            'display_name': 'Earthquake Data',
            'description': 'View earthquake data dashboard'
        },
        'disaster_landslide': {
            'icon': '⛰️',
            'display_name': 'Landslide Data',
            'description': 'View landslide data dashboard'
        },
        'hurricane_data': {
            'icon': '🌀',
            'display_name': 'Hurricane Data',
            'description': 'View hurricane data dashboard'
        }
    }
    
    # Check which tables actually exist in the database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name IN ('earthquake_data', 'disaster_landslide', 'hurricane_data')
            ORDER BY table_name;
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]

    disaster_types = []
    for table_name in existing_tables:
        if table_name in disaster_table_configs:
            config = disaster_table_configs[table_name]
            disaster_types.append({
                "value": table_name,
                "icon": config['icon'],
                "display_name": config['display_name'],
                "description": config['description']
            })

    # Add custom disaster types from the database
    try:
        from .models import CustomDisasterType
        custom_disasters = CustomDisasterType.objects.filter(is_active=True)
        for disaster in custom_disasters:
            # Check if the custom table exists
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """, [disaster.table_name])
                table_exists = cursor.fetchone()[0]
            
            if table_exists:
                disaster_types.append({
                    "value": disaster.name,
                    "icon": disaster.icon or "🌋",
                    "display_name": disaster.display_name,
                    "description": disaster.description or f"View {disaster.display_name} data"
                })
    except Exception as e:
        print(f"Warning: Could not load custom disaster types: {e}")

    # Add "Other" option for dropdown requests
    if request.GET.get("for") == "dropdown":
        disaster_types.append({
            "value": "other",
            "icon": "➕",
            "display_name": "Other (Create New)",
            "description": "Upload a new disaster dataset"
        })

    return JsonResponse(disaster_types, safe=False)