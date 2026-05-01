from django.utils.timezone import localtime
from django.utils.translation import gettext as _  # ייבוא פונקציית התרגום
from .models import Telemetry, Device, ServerHealth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# Time
from django.utils import timezone
from datetime import timedelta
from django.contrib.humanize.templatetags.humanize import naturaltime
# To communicate with server
import platform
import subprocess
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .hardware import read_ads1115

def get_chart_data(request, device_id, metric):
    allowed_metrics = ['power', 'voltage', 'current', 'battery_level']
    if metric not in allowed_metrics:
        return JsonResponse({'error': _('Invalid metric')}, status=400)

    time_range = request.GET.get('range', 'day')
    now = localtime(timezone.now())

    if time_range == 'week':
        start_date = now - timedelta(days=7)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # סינון הנתונים
    telemetry_qs = Telemetry.objects.filter(
        device_id=device_id,
        timestamp__gte=start_date
    )

    # סידור הנתונים והגבלת כמות (שלא יתקע את הדפדפן)
    if telemetry_qs.count() > 300:
        telemetry_qs = telemetry_qs.order_by('-timestamp')[:300]
        telemetry_list = list(telemetry_qs)
        telemetry_list.reverse() # חזרה כרונולוגית (משמאל לימין)
    else:
        telemetry_qs = telemetry_qs.order_by('timestamp')
        telemetry_list = list(telemetry_qs)

    labels = []
    values = []

    for item in telemetry_list:
        local_time = localtime(item.timestamp)
        labels.append(local_time.isoformat())
        values.append(float(getattr(item, metric)))

    return JsonResponse({
        'labels': labels,
        'values': values
    })

@csrf_exempt
def api_receive_server(request):
    if request.method == 'POST':
        try:
            
            data = json.loads(request.body)
            battery_level = data.get('battery_level')
            ServerHealth.objects.create(battery_level=battery_level)
            return JsonResponse({'status': 'success', 'message': 'Data saved correctly'}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)
@csrf_exempt
def api_receive_telemetry(request):
    # אנחנו מוכנים לקבל רק בקשות מטיפוס POST ששולחות נתונים
    if request.method == 'POST':
        try:
            # פריסת ה-JSON שהגיע מהמכשיר
            data = json.loads(request.body)
            
            # שליפת כתובת ה-MAC מתוך הנתונים
            mac_address = data.get('mac_address')
            
            # 1. אימות המכשיר: האם הוא בכלל קיים במערכת שלנו?
            try:
                device = Device.objects.get(mac_address=mac_address)
            except Device.DoesNotExist:
                return JsonResponse({'error': 'Unauthorized device'}, status=403)
            
            # 2. שמירת הנתונים: המכשיר חוקי, בוא נשמור את הטלמטריה
            Telemetry.objects.create(
                device=device,
                voltage=data.get('voltage', 0.00),
                current=data.get('current', 0.0000),
                power=data.get('power', 0.000),
                battery_level=data.get('battery_level', 0)
            )
            
            # 3. החזרת תשובה חיובית למכשיר (כדי שידע שהכל עבר בשלום)
            return JsonResponse({'status': 'success', 'message': 'Data saved correctly'}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    # אם מישהו ניסה להיכנס לכתובת דרך הדפדפן (בקשת GET)
    return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)

@login_required()
def dashboard_view(request):
    # שולפים רק את המערכות ששייכות למשתמש שגולש כרגע
    user_devices = Device.objects.filter(owner=request.user)
    server = ServerHealth.objects.order_by('-timestamp').first()
    real_battery_level = server.battery_level if server is not None else None
    if platform.system() == 'Linux':
        # 2. דוגמים את החומרה האמיתית בזמן אמת! (ערוץ 0 של ה-I2C)
        try:
            real_battery_voltage = read_ads1115(channel=0)
        except Exception as e:
            real_battery_voltage = "Error"
            print(f"Hardware read error: {e}")
    timestamp = naturaltime(server.timestamp) if server is not None else None
    context = {
        'devices': user_devices,
        'server': real_battery_level,
        'timestamp': timestamp
    }
    
    return render(request, 'dashboard/index.html', context)

def api_get_all_latest(request):
    """
    API שמחזיר את נתוני הטלמטריה האחרונים של *כל* המכשירים במכה אחת.
    """
    latest_data = {}
    server = ServerHealth.objects.order_by('-timestamp').first()
    server_battery_level = server.battery_level if server is not None else None
    server_timestamp = naturaltime(server.timestamp) if server is not None else None
    # עוברים על כל המכשירים במסד הנתונים
    # (אם יש לך מערכת משתמשים, כדאי לסנן פה רק את המכשירים של המשתמש הנוכחי)
    devices = Device.objects.all()
    
    for device in devices:
        # שולפים רק את הרשומה האחרונה של המכשיר הספציפי הזה
        latest = Telemetry.objects.filter(device=device).order_by('-timestamp').first()
        
        if latest:
            latest_data[device.id] = {
                'voltage': latest.voltage,
                'current': latest.current,
                'power': latest.power,
                'battery_level': latest.battery_level,
                'timestamp': naturaltime(latest.timestamp)
            }
            
    return JsonResponse({
        'status': 'success',
        'devices': latest_data,
        'server_battery_level': server_battery_level,
        'server_timestamp': server_timestamp
    })
    
    
@csrf_exempt
def api_sync_time(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # מצפים לקבל זמן בפורמט: "YYYY-MM-DD HH:MM:SS"
            rtc_time = data.get('rtc_time')
            
            if not rtc_time:
                return JsonResponse({'error': 'No time provided'}, status=400)
            
            # בדיקה האם אנחנו רצים על ה-Raspberry Pi (Linux) או על מחשב הפיתוח שלך
            if platform.system() == 'Linux':
                # פקודת לינוקס שמשנה את זמן המערכת. דורשת הרשאות!
                # sudo date -s "2026-04-03 15:50:55"
                subprocess.run(['sudo', 'date', '-s', rtc_time], check=True)
                message = f"Raspberry Pi system time updated to {rtc_time}"
            else:
                message = f"[Simulation] OS is {platform.system()}. System time would be changed to {rtc_time}"
                print(f"⏰ {message}")

            return JsonResponse({'status': 'success', 'message': message}, status=200)
            
        except subprocess.CalledProcessError:
            return JsonResponse({'error': 'Permission denied. Django needs sudo access for the "date" command.'}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)