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
    """ מקבל שם רשת וסיסמה, ומחבר את ה-Raspberry Pi לאינטרנט """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ssid = data.get('ssid')
            password = data.get('password')
            
            if not ssid:
                return JsonResponse({'error': 'SSID is required'}, status=400)

            # פקודת ההתחברות בלינוקס:
            # sudo nmcli dev wifi connect "SSID_NAME" password "PASSWORD" ifname wlan1
            command = ['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid]
            if password:
                command.extend(['password', password])
            command.extend(['ifname', 'wlan1'])
            
            subprocess.run(command, capture_output=True, text=True, check=True)
            
            return JsonResponse({'status': 'success', 'message': f'Successfully connected to {ssid}'})
            
        except subprocess.CalledProcessError as e:
            return JsonResponse({'error': f'Failed to connect. Check password. Details: {e.stderr}'}, status=400)
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