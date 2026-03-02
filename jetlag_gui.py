import math
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from tkcalendar import DateEntry

geolocator = Nominatim(user_agent="modern_jetlag_app")
tf = TimezoneFinder()

ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

def get_city_data(city_name):
    try:
        location = geolocator.geocode(city_name)
        if not location: return None
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        if not tz_name: return None
        return {"name": location.address.split(',')[0], "tz": tz_name, "lat": lat, "lon": lon}
    except Exception:
        return None

def estimate_flight_duration(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(((R * c) / 800) + 0.75, 1)

def generate_schedule():
    dep_city_input = dep_city_entry.get()
    dest_city_input = dest_city_entry.get()
    
    selected_date = date_picker.get()
    selected_hour = hour_menu.get()
    selected_minute = minute_menu.get()
    departure_time_str = f"{selected_date} {selected_hour}:{selected_minute}"

    output_text.configure(state="normal")
    output_text.delete("1.0", "end")
    output_text.insert("end", "Searching the globe... Please wait 🌍\n")
    app.update() 

    dep_data = get_city_data(dep_city_input)
    # Check for destination data
    dest_data = get_city_data(dest_city_input)

    if not dep_data or not dest_data:
        messagebox.showerror("Error", "Could not find one of the cities. Check your spelling.")
        output_text.delete("1.0", "end")
        return

    dep_tz = pytz.timezone(dep_data["tz"])
    dest_tz = pytz.timezone(dest_data["tz"])

    try:
        unaware_time = datetime.strptime(departure_time_str, "%d-%m-%Y %H:%M")
        dep_time = dep_tz.localize(unaware_time)
    except ValueError:
        messagebox.showerror("Error", "Time format issue.")
        output_text.delete("1.0", "end")
        return

    flight_duration_hours = estimate_flight_duration(dep_data["lat"], dep_data["lon"], dest_data["lat"], dest_data["lon"])
    flight_duration = timedelta(hours=flight_duration_hours)
    arrival_time_dest_tz = (dep_time + flight_duration).astimezone(dest_tz)
    
    now_utc = datetime.utcnow()
    time_diff = (dest_tz.utcoffset(now_utc).total_seconds() - dep_tz.utcoffset(now_utc).total_seconds()) / 3600
    sleep_duration = timedelta(hours=flight_duration_hours / 2)

    result =  f"🛫 DEPART:  {dep_time.strftime('%d-%m-%Y, %I:%M %p')} | {dep_data['name']} ({dep_data['tz']})\n"
    result += f"🛬 ARRIVE:  {arrival_time_dest_tz.strftime('%d-%m-%Y, %I:%M %p')} | {dest_data['name']} ({dest_data['tz']})\n"
    result += f"✈️ FLIGHT:  ~{flight_duration_hours} hours\n"
    result += "━" * 55 + "\n\n"

    if time_diff > 0:
        sleep_start = dep_time
        sleep_end = dep_time + sleep_duration
        result += "DIRECTION: EAST ➡️ (Losing time - Advance Body Clock)\n\n"
        result += f"😴 SLEEP WINDOW:\n"
        result += f"   Watch:       {sleep_start.strftime('%I:%M %p')} to {sleep_end.strftime('%I:%M %p')}\n"
        result += f"   Destination: {sleep_start.astimezone(dest_tz).strftime('%I:%M %p')} to {sleep_end.astimezone(dest_tz).strftime('%I:%M %p')}\n\n"
        result += "💡 LIGHT: Avoid light early. Seek bright light when you wake up.\n"
        result += "☕ CAFFEINE: No caffeine before boarding. Drink coffee when you wake up."
        
    elif time_diff < 0:
        sleep_start = dep_time + sleep_duration
        result += "DIRECTION: WEST ⬅️ (Gaining time - Delay Body Clock)\n\n"
        result += f"😴 SLEEP WINDOW:\n"
        result += f"   Watch:       {sleep_start.strftime('%I:%M %p')} until landing\n"
        result += f"   Destination: {sleep_start.astimezone(dest_tz).strftime('%I:%M %p')} until landing\n\n"
        result += "💡 LIGHT: Keep screens bright early on. Use an eye mask for the second half.\n"
        result += "☕ CAFFEINE: Caffeine is okay early. Avoid it strictly during the second half."
    else:
        result += "DIRECTION: North/South ⬆️⬇️ (No major time shift)\n"
        result += "Action: Sleep normally as you would on a standard day."

    output_text.delete("1.0", "end")
    output_text.insert("end", result)
    output_text.configure(state="disabled")

app = ctk.CTk()
app.title("Jet Lag Optimizer")
app.geometry("835x615")

title_label = ctk.CTkLabel(app, text="Jet Lag Optimizer ✈️", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=(20, 10))

frame = ctk.CTkFrame(app, corner_radius=15)
frame.pack(pady=10, padx=20, fill="both", expand=True)

input_frame = ctk.CTkFrame(frame, fg_color="transparent")
input_frame.pack(pady=20, padx=20)

ctk.CTkLabel(input_frame, text="Departure City:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=10, padx=10)
dep_city_entry = ctk.CTkEntry(input_frame, width=250, placeholder_text="e.g., Tokyo")
dep_city_entry.grid(row=0, column=1, pady=10, padx=10)

ctk.CTkLabel(input_frame, text="Destination City:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=10, padx=10)
dest_city_entry = ctk.CTkEntry(input_frame, width=250, placeholder_text="e.g., London")
dest_city_entry.grid(row=1, column=1, pady=10, padx=10)

ctk.CTkLabel(input_frame, text="Date & Time:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", pady=10, padx=10)

time_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
time_frame.grid(row=2, column=1, sticky="w", padx=10)

date_picker = DateEntry(time_frame, width=12, background='#1f538d', foreground='white', borderwidth=0, date_pattern='dd-mm-yyyy')
date_picker.pack(side="left", padx=(0, 10))

hours = [f"{i:02d}" for i in range(24)]
minutes = [f"{i:02d}" for i in range(60)]

hour_menu = ctk.CTkOptionMenu(time_frame, values=hours, width=60)
hour_menu.pack(side="left", padx=2)
hour_menu.set("12") 

ctk.CTkLabel(time_frame, text=":").pack(side="left", padx=2)

minute_menu = ctk.CTkOptionMenu(time_frame, values=minutes, width=60)
minute_menu.pack(side="left", padx=2)
minute_menu.set("00") 

calc_button = ctk.CTkButton(frame, text="Calculate Sleep Schedule", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=generate_schedule)
calc_button.pack(pady=10)

output_text = ctk.CTkTextbox(frame, width=680, height=200, corner_radius=10, font=ctk.CTkFont(family="Courier", size=13), wrap="word")
output_text.pack(pady=15, padx=20, fill="both", expand=True)
output_text.insert("end", "Enter your flight details above to generate a strategy.")
output_text.configure(state="disabled")

app.mainloop()