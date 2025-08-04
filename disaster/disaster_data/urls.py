from django.urls import path
from . import views

urlpatterns = [
    # 🔐 Login as main page
    path('', views.login_view, name='login'),

    # ✅ Dashboard/Home page (moved from root)
    path('home/', views.home_ui, name='home-ui'),
    path('api/disaster-types/', views.api_disaster_types, name='api_disaster_types'),

    # 🌍 Earthquake routes
    path('earthquake-ui/', views.earthquake_ui, name='earthquake-ui'),
    path('earthquakes/download/', views.download_earthquake_csv, name='download_earthquake_csv'),
    path('api/earthquakes/', views.earthquake_data_api, name='earthquake-data-api'),
    path('api/earthquakes/available_years/', views.available_earthquake_years, name='available_earthquake_years'),
    path('api/earthquake_charts/', views.earthquake_charts_api, name='earthquake_charts_api'),

    # 🏔️ Landslide routes
    path('landslide-ui/', views.landslide_ui, name='landslide-ui'),
    path('landslide-ui/download/', views.download_landslide_csv, name='download_landslide_csv'),
    path('api/landslides/', views.landslide_data_api, name='landslide-data-api'),
    path('api/landslides/yearly_counts/', views.landslide_yearly_counts, name='landslide-yearly-counts'),
    path('api/landslides/available_years/', views.available_years_by_trigger, name='available_years_by_trigger'),
    path('landslide-risk-map/', views.risk_landslide_future, name='risk_landslide_future'),
    path('api/landslides/triggers/', views.landslide_triggers_api, name='triggers_api'),
    path("api/landslide-heatmap/", views.landslide_heatmap_api, name="landslide_heatmap_api"),
    path("risk-landslide-future/", views.risk_landslide_future, name="risk_landslide_future"),

    # 🌪️ Hurricane routes
    path('hurricane-ui/', views.hurricane_ui, name='hurricane-ui'),  
    path('hurricane-ui/download/', views.download_hurricane_csv, name='download_hurricane_csv'),
    path('api/hurricanes/', views.hurricane_data_api, name='hurricane_data_api'),

    # 📤 CSV Upload & Map View
    path('upload/', views.upload_csv, name='upload_csv'),
    path('map/', views.map_view, name='map_view'), # ✅ correct
    path('api/points/', views.location_data_api, name='location_data_api'),
    path('my-uploads/', views.my_uploads, name='my_uploads'),
    path('view-table/<str:table_name>/', views.view_table, name='view_table'),
    path('delete_dataset/<int:id>/', views.delete_dataset, name='delete_dataset'),
    path('upload/<str:disaster_type>/', views.upload_csv_generic, name='upload_csv_generic'),

    # 🔐 Authentication (keeping login route for explicit access)
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    path('map-preview/', views.map_preview, name='map_preview'),
    path('api/preview-csv/', views.preview_csv_api, name='preview_csv_api'),
    path('save-table/', views.save_table, name='save_table'),
    path('api/latest-earthquakes/', views.latest_earthquake_news, name='latest_earthquake_news'),
    

    # 🌐 Dynamic Disaster Types API
    path('api/available-disaster-types/', views.get_available_disaster_types, name='available_disaster_types_api'),
    
    # 🗺️ Dynamic Disaster Views
    path('disaster-view/<str:disaster_type>/', views.dynamic_disaster_view, name='dynamic_disaster_view'),
    path('api/disaster-data/<str:disaster_type>/', views.dynamic_disaster_api, name='dynamic_disaster_api'),
    
    # Custom Disaster Type Views
    path('custom-<str:disaster_type>-ui/', views.custom_disaster_view, name='custom_disaster_view'),
    path('api/custom-disaster-data/<str:disaster_name>/', views.custom_disaster_data_api, name='custom_disaster_data_api'),
    
    # 🐛 Debug endpoint
    path('debug/tables/', views.debug_tables, name='debug_tables'),
    path('upload/any/', views.upload_any_csv, name='upload_any_csv'),
    path('view-uploaded-data/<str:disaster_type>/<str:session_id>/', views.view_uploaded_data, name='view_uploaded_data'),

    #chatbot
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),

]




