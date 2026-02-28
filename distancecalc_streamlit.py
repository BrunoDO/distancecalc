
import streamlit as st
import openrouteservice
from geopy.geocoders import Nominatim
import re
import time

# --- Streamlit secrets for API key ---
# In Streamlit Cloud, add your key in Secrets: API_KEY="YOUR_KEY_HERE"
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRlYTYzNjZhZDgzNzRhMmI4YmFiZTdkZDdjNmY0OGI2IiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=API_KEY)
geolocator = Nominatim(user_agent="distancecalc_streamlit")

# --- Helper function for geocoding ---
def smart_geocode(street, city, state, country, postal):
    attempts = []
    attempts.append(", ".join([p for p in [street, city, state, country, postal] if p]))
    clean_street = re.sub(r'\b(apt|unit|suite|#)\s*\w+\b', '', street, flags=re.I)
    no_number = re.sub(r'^\s*\d+\s*', '', clean_street)
    attempts.append(", ".join([p for p in [clean_street, city, state, country] if p]))
    attempts.append(", ".join([p for p in [no_number, city, state, country] if p]))
    attempts.append(", ".join([p for p in [city, state, country] if p]))

    for addr in attempts:
        location = geolocator.geocode(addr)
        if location:
            return (location.longitude, location.latitude)
    return None

# --- Streamlit App ---
st.title("🚗 Driving Distance Calculator")

# Home Address
st.header("Home Address")
home_street = st.text_input("Street")
home_city = st.text_input("City")
home_state = st.text_input("Province/State")
home_country = st.text_input("Country")
home_postal = st.text_input("Postal Code (optional)")

# Destinations
st.header("Destinations")
st.write("Enter each destination on a new line in the format:")
st.write("Street, City, Province/State, Country, Postal (optional)")
destinations_input = st.text_area("Destinations (one per line)")

# Calculate distances
if st.button("Calculate Distances"):
    if not home_street or not home_city or not home_country:
        st.error("Please enter at least Street, City, and Country for Home.")
    else:
        home_coords = smart_geocode(home_street, home_city, home_state, home_country, home_postal)
        if not home_coords:
            st.error("Could not find Home location. Try simpler address.")
        else:
            total_distance = 0
            st.write("### Results:")
            destinations = [line.strip() for line in destinations_input.split("\n") if line.strip()]
            if not destinations:
                st.warning("No destinations entered.")
            for i, line in enumerate(destinations, 1):
                parts = [p.strip() for p in line.split(",")]
                while len(parts) < 5:
                    parts.append("")  # fill missing fields
                street, city, state, country, postal = parts
                dest_coords = smart_geocode(street, city, state, country, postal)
                if not dest_coords:
                    st.write(f"Destination {i}: ❌ Could not find location")
                    continue
                try:
                    route = client.directions(
                        coordinates=[home_coords, dest_coords],
                        profile='driving-car',
                        format='geojson'
                    )
                    distance_m = route['features'][0]['properties']['segments'][0]['distance']
                    distance_km = distance_m / 1000
                    total_distance += distance_km
                    st.write(f"Destination {i}: {distance_km:.2f} km")
                    time.sleep(1)  # prevent API throttling
                except Exception as e:
                    st.write(f"Destination {i}: ⚠️ Could not calculate route ({e})")
            st.write(f"### 🟢 Total distance: {total_distance:.2f} km")
