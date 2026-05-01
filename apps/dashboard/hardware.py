import platform
if platform.system() == 'Linux':
    import smbus
    import time

    # ==========================================
    # הגדרות מודול ה-ADS1115
    # ==========================================

    # כתובת ברירת המחדל של ה-ADS1115 על אפיק ה-I2C (0x48)
    I2C_ADDRESS = 0x48

    # יצירת מופע של אפיק ה-I2C (בדרך כלל ערוץ 1 ברספברי פיי)
    bus = smbus.SMBus(1)

    # ==========================================
    # פונקציות עזר לקריאת נתונים
    # ==========================================

    def read_ads1115(channel=0):
        """
        קוראת מתח אנלוגי מערוץ ספציפי של ה-ADS1115 (A0-A3).
        
        פרמטרים:
            channel (int): מספר הערוץ (0 עד 3). ברירת המחדל היא 0 (A0).
            
        מחזירה:
            float: המתח הנמדד בווולטים.
        """
        
        if channel < 0 or channel > 3:
            raise ValueError("Channel must be between 0 and 3")

        # קונפיגורציה של האוגר (Register):
        # - 0x4000: תחילת קריאה (OS = 1)
        # - (channel + 4) << 12: בחירת הערוץ (MUX) לקריאה בודדת (Single-Ended)
        # - 0x0200: הגדרת טווח מתח למקסימום (+/- 4.096V)
        # - 0x0100: מצב קריאה רציף או בודד (Continuous / Single-shot)
        # - 0x0080: קצב דגימה (Data Rate) של 128SPS
        config = 0x4000 | ((channel + 4) << 12) | 0x0200 | 0x0100 | 0x0080
        
        # פיצול הערך ל-2 בייטים כדי לשלוח לאפיק ה-I2C
        config_bytes = [(config >> 8) & 0xFF, config & 0xFF]

        try:
            # כתיבת תצורת האוגר ל-ADS1115 כדי להתחיל המרה
            bus.write_i2c_block_data(I2C_ADDRESS, 0x01, config_bytes)
            
            # המתנה קצרה שההמרה תסתיים (כ-8 מילישניות לפי ה-Datasheet)
            time.sleep(0.01)
            
            # קריאת 2 בייטים (16 סיביות) של התוצאה מאוגר ההמרה (Conversion Register - 0x00)
            data = bus.read_i2c_block_data(I2C_ADDRESS, 0x00, 2)
            
            # חיבור שני הבייטים לקבלת ערך שלם מ-16 סיביות (Raw ADC Value)
            raw_val = (data[0] << 8) | data[1]
            
            # מכיוון שה-ADS1115 יכול למדוד מתח שלילי (Two's Complement), 
            # עלינו לטפל בערכים שליליים אם במקרה המדידה עוברת את 32767
            if raw_val > 32767:
                raw_val -= 65536
                
            # המרה מנתון גולמי לערך מתח (וולטים).
            # טווח המתח המקסימלי שהגדרנו (PGA) הוא 4.096V על פני 15 סיביות חיוביות (32767).
            voltage = raw_val * (4.096 / 32767.0)
            
            return round(voltage, 3)

        except IOError:
            print(f"Error reading I2C device at address {hex(I2C_ADDRESS)}")
            return 0.0

    # ==========================================
    # קוד הרצה לדוגמה (לבדיקת החיישן בעצמו)
    # ==========================================

    if __name__ == "__main__":
        try:
            print("Reading ADS1115 Data. Press Ctrl+C to stop.")
            while True:
                # קורא מהערוץ הראשון - מחבר A0 של החיישן
                v0 = read_ads1115(0)
                print(f"Voltage on A0: {v0} V")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Stopped by user.")