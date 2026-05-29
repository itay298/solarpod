import requests
import time
import random

# הכתובת של ה-API שבנינו (בהנחה שאתה מריץ את שרת הפיתוח על פורט 8000)
API_URL_TELEMETRY = "http://127.0.0.1:8000/api/telemetry/receive/"
API_URL_SERVER = "http://127.0.0.1:8000/api/server/receive/"
# ⚠️ קריטי: שנה את זה לכתובת ה-MAC שמוגדרת לך ב-Admin של ג'אנגו!
MAC_ADDRESS = "123456"

def generate_fake_data():
    """
    מייצר נתוני טלמטריה הגיוניים למערכת סולארית, 
    כולל חישוב אחוז סוללה מציאותי המבוסס על המתח (סוללת 6V).
    """
    # זיוף מתח לסוללת 6V (5.25V נחשב ריק, 6.37V נחשב מלא)
    voltage = round(random.uniform(5.25, 6.37), 2)
    
    # חישוב אחוז הסוללה לפי המתח (מיפוי מתמטי מ-0% עד 100%)
    battery_level = round(((voltage - 5.25) / (6.37 - 5.25)) * 100, 1)
    # מוודאים שהאחוז לא יחרוג מגבולות ה-0-100 במקרה של סטייה
    battery_level = max(0.0, min(100.0, battery_level))
    
    # זיוף זרם והספק (מותאם לסוללה קטנה 1.3Ah)
    current = round(random.uniform(0.05, 0.5), 4)
    power = round(voltage * current, 3)
    
    return {
        "mac_address": MAC_ADDRESS,
        "voltage": voltage,
        "current": current,
        "power": power,
        "battery_level": battery_level
    }

print("☀️ Starting SolarPod Hardware Simulator...")
print(f"📡 Targeting: {API_URL_TELEMETRY}")
print("-" * 40)

# לולאה אינסופית שתרוץ עד שתעצור אותה עם Ctrl+C
while True:
    data = generate_fake_data()
    server_data = {
        'battery_level': random.randint(10, 100)
    }
    print(f"📤 Sending: Voltage={data['voltage']}V | Current={data['current']}A | Power={data['power']}W")
    
    try:
        # שליחת הנתונים לשרת בפורמט JSON
        response1 = requests.post(API_URL_TELEMETRY, json=data)
        response2 = requests.post(API_URL_SERVER, json=server_data)
        # בדיקת התשובה מהשרת
        if response1.status_code == 201 and response2.status_code == 201:
            print("✅ Success! Data saved in Django.")
        elif response1.status_code == 403:
            print(f"❌ Rejected: The MAC address '{MAC_ADDRESS}' is not in the Django database!")
        else:
            print(f"⚠️ Server returned status {response1.status_code}: {response1.text}")
            print(f"⚠️ Server returned status {response2.status_code}: {response2.text}")
            
    except requests.exceptions.ConnectionError:
        print("🚨 Connection Error: Is your Django server (runserver) running?")
        
    print("-" * 40)
    # המתנה של 10 שניות לפני השליחה הבאה (אפשר לשנות ל-5 אם רוצים לראות גרף מהיר יותר)
    time.sleep(60)