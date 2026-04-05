import polib
import re
import time
import sys
from deep_translator import GoogleTranslator

def apply_professional_glossary(text):
    """
    מילון מונחים מקצועי: מתקן את הטעויות הנפוצות של גוגל טרנסלייט 
    בהקשר של מערכות סולאריות וחשמל, כדי שהמערכת תיראה מקצועית.
    """
    if not text:
        return text
        
    glossary = {
        "נוכחי ב-[A]": "זרם ב-[A]",
        "נוכחי": "זרם",
        "כּוֹחַ": "הספק",
        "כוח ב-[W]": "הספק ב-[W]",
        "כוח נכנס": "כוח ב",
        "מתח נכנס": "מתח ב",
        "זרם נכנס": "זרם ב",
        "בטריה נכנסת": "סוללה ב",
        "כוח": "הספק",
        "הֶתקֵן": "מכשיר",
        "התקן": "מכשיר",
        "טלמטריות": "נתוני טלמטריה",
        "אחוז הסוללה העיקרי": "אחוז הסוללה הראשית"
    }
    
    for wrong_term, correct_term in glossary.items():
        text = text.replace(wrong_term, correct_term)
        
    return text

def safe_translate(text, translator):
    """
    מנגנון ההגנה על הפלייסחולדרים:
    מוציא את המשתנים של ג'אנגו לפני התרגום ומחזיר אותם בסוף,
    כדי למנוע שגיאות קריסה בקומפילציה.
    """
    if not text:
        return text

    # 1. איתור המשתנים של ג'אנגו (למשל: %(server)s, %s, {name})
    pattern = r'(%\([a-zA-Z0-9_]+\)[sSdDiIfF]|%[sSdDiIfF]|\{[a-zA-Z0-9_]+\})'
    variables = re.findall(pattern, text)
    
    # 2. החלפת המשתנים בטוקנים זמניים
    temp_text = text
    for i, var in enumerate(variables):
        temp_text = temp_text.replace(var, f'__VAR{i}__')
        
    # 3. תרגום נקי בגוגל
    translated_text = translator.translate(temp_text)
    
    # 4. החזרת המשתנים פנימה (כולל טיפול ברווחים שגוגל עלול להוסיף)
    for i, var in enumerate(variables):
        # תופס מצבים כמו __VAR0__, __ VAR 0 __ וכו'
        regex_var = r'__\s*VAR\s*' + str(i) + r'\s*__'
        translated_text = re.sub(regex_var, var, translated_text)
        
    return translated_text

def translate_po_file(po_file_path, dest_lang='he'):
    print(f"Loading PO file: {po_file_path}...")
    try:
        po = polib.pofile(po_file_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    translator = GoogleTranslator(source='auto', target=dest_lang)
    
    # אוספים את כל השורות שחסר להן תרגום, או שסומנו כ-fuzzy (דורשות אימות)
    entries_to_translate = [entry for entry in po if not entry.msgstr or 'fuzzy' in entry.flags]
    total_entries = len(entries_to_translate)
    
    if total_entries == 0:
        print("All entries are perfectly translated and ready! Nothing to do.")
        return

    print(f"Found {total_entries} entries to translate/fix. Starting...\n")

    for i, entry in enumerate(entries_to_translate, 1):
        original_text = entry.msgid
        
        if not original_text.strip():
            continue

        try:
            # 1. תרגום בטוח (שומר על המשתנים)
            safe_translation = safe_translate(original_text, translator)
            
            # 2. החלת מילון המונחים שלנו
            final_translation = apply_professional_glossary(safe_translation)
            
            # 3. שמירת התוצאה
            entry.msgstr = final_translation
            
            # 4. מחיקת דגל ה-fuzzy המעצבן כדי שג'אנגו יציג את התרגום
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            
            print(f"[{i}/{total_entries}] {original_text}  -->  {final_translation}")
            
            # חצי שנייה המתנה כדי למנוע חסימה מגוגל
            time.sleep(0.5)
            
        except Exception as e:
            print(f"\n[{i}/{total_entries}] ERROR translating '{original_text}': {e}")
            print("Saving progress and stopping. You can run the script again later.")
            break

    # שמירה לדיסק בסיום
    po.save(po_file_path)
    print("\n✅ Translation completed and saved successfully!")
    print("👉 Now run: python manage.py compilemessages")

if __name__ == "__main__":
    # ודא שהנתיב הזה תואם לנתיב המדויק של קובץ ה-PO שלך בפרויקט
    PO_FILE_PATH = f'../locale/{sys.argv[1]}/LC_MESSAGES/django.po'
    TARGET_LANGUAGE = sys.argv[2] 
    
    translate_po_file(PO_FILE_PATH, TARGET_LANGUAGE)