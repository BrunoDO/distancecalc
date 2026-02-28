import tkinter as tk
from tkinter import messagebox
import openrouteservice
from geopy.geocoders import Nominatim
import re
import time

# --- Replace this with your OpenRouteService API key ---
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRlYTYzNjZhZDgzNzRhMmI4YmFiZTdkZDdjNmY0OGI2IiwiaCI6Im11cm11cjY0In0="

# Initialize clients
geolocator = Nominatim(user_agent="driving_distance_gui")
client = openrouteservice.Client(key=API_KEY)

# --- Helper functions ---
def smart_geocode(street, city, state, country, postal):
    """Try multiple fallback formats for geocoding"""
    attempts = []

    # Full address
    parts = [street, city, state, country, postal]
    attempts.append(", ".join([p for p in parts if p]))

    # Remove unit/apt numbers
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

def calculate_distance():
    # Clear previous results
    results_text.delete("1.0", tk.END)
    total_distance = 0

    # --- Home coordinates ---
    h_street = home_street_var.get()
    h_city = home_city_var.get()
    h_state = home_state_var.get()
    h_country = home_country_var.get()
    h_postal = home_postal_var.get()

    home_coords = smart_geocode(h_street, h_city, h_state, h_country, h_postal)
    if not home_coords:
        messagebox.showerror("Error", "Could not find Home location. Try simpler address.")
        return

    # --- Destinations ---
    destinations = []
    for dest in dest_frames:
        street = dest['street'].get()
        city = dest['city'].get()
        state = dest['state'].get()
        country = dest['country'].get()
        postal = dest['postal'].get()

        if street.strip() == "" and city.strip() == "" and state.strip() == "" and country.strip() == "" and postal.strip() == "":
            continue  # Skip empty destination

        destinations.append((street, city, state, country, postal))

    if not destinations:
        messagebox.showerror("Error", "Please enter at least one destination.")
        return

    for i, (street, city, state, country, postal) in enumerate(destinations, 1):
        dest_coords = smart_geocode(street, city, state, country, postal)
        if not dest_coords:
            results_text.insert(tk.END, f"Destination {i}: ❌ Could not find location\n")
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

            results_text.insert(tk.END, f"Destination {i}: {distance_km:.2f} km\n")
            time.sleep(1)
        except Exception:
            results_text.insert(tk.END, f"Destination {i}: ⚠️ Could not calculate route\n")

    results_text.insert(tk.END, f"\n🟢 Total distance: {total_distance:.2f} km\n")

def add_destination_fields():
    """Adds a new row of destination input fields"""
    frame = tk.Frame(dest_container)
    frame.pack(pady=2, fill="x")

    dest_vars = {
        'street': tk.StringVar(),
        'city': tk.StringVar(),
        'state': tk.StringVar(),
        'country': tk.StringVar(),
        'postal': tk.StringVar()
    }

    tk.Label(frame, text="Street:").grid(row=0, column=0)
    tk.Entry(frame, textvariable=dest_vars['street'], width=20).grid(row=0, column=1)
    tk.Label(frame, text="City:").grid(row=0, column=2)
    tk.Entry(frame, textvariable=dest_vars['city'], width=15).grid(row=0, column=3)
    tk.Label(frame, text="Province/State:").grid(row=0, column=4)
    tk.Entry(frame, textvariable=dest_vars['state'], width=10).grid(row=0, column=5)
    tk.Label(frame, text="Country:").grid(row=0, column=6)
    tk.Entry(frame, textvariable=dest_vars['country'], width=10).grid(row=0, column=7)
    tk.Label(frame, text="Postal:").grid(row=0, column=8)
    tk.Entry(frame, textvariable=dest_vars['postal'], width=8).grid(row=0, column=9)

    dest_frames.append(dest_vars)

# --- GUI Setup ---
root = tk.Tk()
root.title("Driving Distance Calculator")

# Home Address Frame
home_frame = tk.LabelFrame(root, text="Home Address", padx=10, pady=10)
home_frame.pack(padx=10, pady=5, fill="x")

home_street_var = tk.StringVar()
home_city_var = tk.StringVar()
home_state_var = tk.StringVar()
home_country_var = tk.StringVar()
home_postal_var = tk.StringVar()

tk.Label(home_frame, text="Street:").grid(row=0, column=0, sticky="e")
tk.Entry(home_frame, textvariable=home_street_var, width=50).grid(row=0, column=1)
tk.Label(home_frame, text="City:").grid(row=1, column=0, sticky="e")
tk.Entry(home_frame, textvariable=home_city_var, width=50).grid(row=1, column=1)
tk.Label(home_frame, text="Province/State:").grid(row=2, column=0, sticky="e")
tk.Entry(home_frame, textvariable=home_state_var, width=50).grid(row=2, column=1)
tk.Label(home_frame, text="Country:").grid(row=3, column=0, sticky="e")
tk.Entry(home_frame, textvariable=home_country_var, width=50).grid(row=3, column=1)
tk.Label(home_frame, text="Postal Code:").grid(row=4, column=0, sticky="e")
tk.Entry(home_frame, textvariable=home_postal_var, width=50).grid(row=4, column=1)

# Destination Frame
dest_frame = tk.LabelFrame(root, text="Destinations", padx=10, pady=10)
dest_frame.pack(padx=10, pady=5, fill="both")

dest_container = tk.Frame(dest_frame)
dest_container.pack()

dest_frames = []

# Add first destination field by default
add_destination_fields()

tk.Button(dest_frame, text="Add Another Destination", command=add_destination_fields).pack(pady=5)

# Calculate Button
tk.Button(root, text="Calculate Distances", command=calculate_distance, bg="lightgreen").pack(pady=10)

# Results
results_frame = tk.LabelFrame(root, text="Results", padx=10, pady=10)
results_frame.pack(padx=10, pady=5, fill="both", expand=True)

results_text = tk.Text(results_frame, height=10)
results_text.pack(fill="both", expand=True)

# Run the GUI
print("GUI starting...")
root.mainloop()
