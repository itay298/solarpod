from django.contrib import admin
from .models import Device, Telemetry, ServerHealth

admin.site.register(ServerHealth)

# 1. הגדרת ה-Inline עבור נתוני הטלמטריה
class TelemetryInline(admin.TabularInline):
    model = Telemetry
    extra = 0  # מונע הופעת שורות ריקות ומיותרות בסוף הטבלה
    
    # השדות האלו מחושבים או נוצרים אוטומטית, לכן נציג אותם לקריאה בלבד באדמין
    readonly_fields = ('timestamp', 'power')
    # נסדר כך שהקריאה האחרונה ביותר (הכי חדשה) תופיע ראשונה למעלה
    ordering = ('-timestamp',)
    
    # אופציונלי: מגביל את מספר השורות שיוצגו כדי שהעמוד לא יקרוס כשיהיו אלפי קריאות
    max_num = 50 
    
    # שדות שיוצגו בטבלה
    fields = ('timestamp', 'voltage', 'current', 'power', 'battery_level', 'tracker_angle_x', 'tracker_angle_y')

# 2. רישום מודל המכשיר (Device) ושילוב ה-Inline בתוכו
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'mac_address', 'owner')
    search_fields = ('name', 'mac_address')
    list_filter = ('owner',)
    inlines = [TelemetryInline] # כאן אנחנו משלבים את הטלמטריה לתוך דף המכשיר

# 3. רישום טבלת הטלמטריה גם בנפרד (מומלץ מאוד)
@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    # תצוגה נוחה כשרוצים לראות את כל הקריאות של כל המכשירים יחד
    list_display = ('device', 'timestamp', 'voltage', 'current', 'power', 'battery_level')
    search_fields = ('device__name', 'device__owner__username', 'device__mac_address',)
    # סננים בצד ימין - יעזור לך מאוד למצוא נתונים לפי מכשיר או תאריך ספציפי
    list_filter = ('device', 'timestamp')
    readonly_fields = ('timestamp', 'power')