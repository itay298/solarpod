import subprocess
from django.http import JsonResponse
import platform
from django.views.decorators.csrf import csrf_exempt
import json

def api_scan_wifi(request):
    """ סורק רשתות Wi-Fi זמינות בעזרת המתאם החיצוני (wlan1) """
    try:
        # פקודת הלינוקס: סרוק והדפס רק שם, עוצמת אות ואבטחה
        # nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list ifname wlan1
        result = subprocess.run(
            ['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list', 'ifname', 'wlan1'],
            capture_output=True, text=True, check=True
        )
        
        networks = []
        # עוברים שורה-שורה על התשובה של לינוקס
        for line in result.stdout.split('\n'):
            if line and ':' in line:
                parts = line.split(':')
                ssid = parts[0]
                # מסננים החוצה רשתות מוסתרות שאין להן שם
                if ssid: 
                    networks.append({
                        'ssid': ssid,
                        'signal': parts[1],
                        'security': parts[2]
                    })
        
        # מסננים כפילויות (לפעמים רשת מופיעה פעמיים בגלל תדרים שונים 2.4/5GHz)
        unique_networks = list({v['ssid']:v for v in networks}.values())
        
        return JsonResponse({'status': 'success', 'networks': unique_networks})
        
    except Exception as e:
        # במקרה שאתה בודק את זה על Windows, נחזיר נתונים פיקטיביים רק כדי שהאתר לא יקרוס
        return JsonResponse({
            'status': 'mock', 
            'networks': [{'ssid': 'MyHomeWifi', 'signal': '80'}, {'ssid': 'Guest_Network', 'signal': '50'}]
        })
        
@csrf_exempt
def api_connect_wifi(request):
    """ מקבל שם רשת וסיסמה, ובונה פרופיל חיבור קשיח כדי לעקוף שגיאות זיהוי """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ssid = data.get('ssid')
            password = data.get('password')
            
            if not ssid:
                return JsonResponse({'error': 'SSID is required'}, status=400)

            if platform.system() == 'Linux':
                # 1. מחיקת פרופיל ישן כדי למנוע התנגשויות
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], capture_output=True)
                
                if password:
                    # בניית פרופיל ידני לרשת עם סיסמה (שיטת הפטיש שעבדה לנו)
                    subprocess.run(['sudo', 'nmcli', 'connection', 'add', 'type', 'wifi', 'ifname', 'wlan1', 'con-name', ssid, 'ssid', ssid], check=True)
                    subprocess.run(['sudo', 'nmcli', 'connection', 'modify', ssid, 'wifi-sec.key-mgmt', 'wpa-psk'], check=True)
                    subprocess.run(['sudo', 'nmcli', 'connection', 'modify', ssid, 'wifi-sec.psk', password], check=True)
                    # הפעלת החיבור
                    subprocess.run(['sudo', 'nmcli', 'connection', 'up', ssid], capture_output=True, text=True, check=True)
                else:
                    # חיבור לרשת פתוחה (ללא סיסמה) - כאן לינוקס בדרך כלל לא מסתבך
                    subprocess.run(['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid, 'ifname', 'wlan1'], capture_output=True, text=True, check=True)
                
                return JsonResponse({'status': 'success', 'message': f'Successfully connected to {ssid}'})
            else:
                return JsonResponse({'status': 'success', 'message': 'Simulated connection on Windows'})
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else e.stdout
            return JsonResponse({'error': f'Failed to connect. Details: {error_msg}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_wifi_status(request):
    """ בודק האם הרספברי מחובר כרגע לרשת Wi-Fi דרך המתאם (wlan1) """
    if platform.system() == 'Linux':
        try:
            # הפקודה הזו מחזירה רשימה של כל ההתקנים, המצב שלהם, ושם הרשת (אם יש)
            # הפורמט שחוזר: DEVICE:STATE:CONNECTION
            result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,STATE,CONNECTION', 'dev', 'status'], capture_output=True, text=True)
            
            # נעבור שורה-שורה ונחפש את המתאם החיצוני שלנו
            for line in result.stdout.split('\n'):
                if line.startswith('wlan1:'):
                    parts = line.split(':')
                    state = parts[1] # המצב (connected / disconnected)
                    ssid = parts[2]  # שם הרשת
                    
                    # אם המצב הוא "מחובר" ויש שם לרשת
                    if state == 'connected' and ssid:
                        return JsonResponse({'status': 'connected', 'ssid': ssid})
                    else:
                        return JsonResponse({'status': 'disconnected'})
            
            # אם משום מה wlan1 לא הופיע ברשימה בכלל
            return JsonResponse({'status': 'disconnected'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        # מצב סימולציה כשאתה מפתח על חלונות/מאק
        return JsonResponse({'status': 'connected', 'ssid': 'My_Smart_Home_Simulated'})

@csrf_exempt
def api_wifi_disconnect(request):
    """ מנתק את הרספברי מהרשת הנוכחית """
    if request.method == 'POST':
        if platform.system() == 'Linux':
            try:
                # פקודת ההתנתקות של לינוקס
                subprocess.run(['sudo', 'nmcli', 'dev', 'disconnect', 'wlan1'], check=True)
                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'status': 'success', 'message': 'Simulated disconnect'})
    return JsonResponse({'error': 'POST required'}, status=405)