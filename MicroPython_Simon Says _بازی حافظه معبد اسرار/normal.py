# Ali Rashidi
# t.me/WriteYourWay

import machine, utime, random, uasyncio as asyncio  # وارد کردن ماژول‌های مورد نیاز: 
                                                   # machine برای کنترل سخت‌افزار، utime برای مدیریت زمان،
                                                   # random برای تولید اعداد تصادفی و uasyncio برای برنامه‌نویسی غیرهمزمان.
from i2c_lcd import I2cLcd  # وارد کردن کلاس I2cLcd از کتابخانه i2c_lcd جهت کنترل LCD از طریق I2C

# -------------------------------------------
# تابع save_score: ذخیره امتیاز بازی در فایل
# -------------------------------------------
def save_score(score):
    try:  # تلاش برای ذخیره امتیاز در فایل
        with open("score.txt", "w") as f:  # باز کردن فایل "score.txt" در حالت نوشتن
            f.write(str(score))  # تبدیل امتیاز به رشته و نوشتن آن در فایل
    except Exception as e:  # در صورت بروز هرگونه خطا
        pass  # خطا نادیده گرفته می‌شود

# -------------------------------------------
# تابع load_score: بارگذاری امتیاز ذخیره‌شده از فایل
# -------------------------------------------
def load_score():
    try:  # تلاش برای خواندن امتیاز از فایل
        with open("score.txt", "r") as f:  # باز کردن فایل "score.txt" در حالت خواندن
            return f.read().strip()  # خواندن محتویات فایل، حذف فاصله‌های اضافی و بازگرداندن نتیجه
    except Exception as e:  # در صورت بروز خطا (مثلاً فایل موجود نباشد)
        return None  # بازگرداندن None

# ============================================================
# کلاس Keypad: کنترل کیپد 4×4 (ماتریسی) جهت دریافت ورودی از کاربر
# ============================================================
class Keypad:
    def __init__(self, row_pins, col_pins, keys):
        # ایجاد اشیاء پین برای ردیف‌ها به عنوان خروجی
        self.rows = [machine.Pin(pin, machine.Pin.OUT) for pin in row_pins]
        # ایجاد اشیاء پین برای ستون‌ها به عنوان ورودی با تنظیم مقاومت pull-down
        self.cols = [machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_DOWN) for pin in col_pins]
        # ذخیره ماتریس کلیدها جهت دسترسی به مقدار هر کلید
        self.keys = keys

    async def scan(self):
        """
        تابع غیرهمزمان scan: بررسی و تشخیص کلید فشرده شده از کیپد
        """
        # پیمایش هر ردیف به همراه اندیس i
        for i, row in enumerate(self.rows):
            row.value(1)  # تنظیم ردیف فعلی به HIGH (فعال کردن آن)
            # پیمایش هر ستون در ردیف فعلی با اندیس j
            for j, col in enumerate(self.cols):
                if col.value() == 1:  # اگر ستون به دلیل فشرده شدن کلید مقدار HIGH دارد
                    await asyncio.sleep_ms(50)  # تأخیر 50 میلی‌ثانیه جهت کاهش نویز
                    if col.value() == 1:  # بررسی مجدد وضعیت ستون پس از تأخیر
                        key = self.keys[i][j]  # دریافت کلید فشرده شده از ماتریس کلیدها
                        start_release = utime.ticks_ms()  # ثبت زمان شروع آزادسازی کلید
                        # حلقه تا زمانی که کلید همچنان فشرده است یا زمان بیش از 500 میلی‌ثانیه گذشته باشد
                        while col.value() == 1:
                            await asyncio.sleep_ms(10)  # تأخیر 10 میلی‌ثانیه جهت بررسی مجدد وضعیت کلید
                            if utime.ticks_diff(utime.ticks_ms(), start_release) > 500:
                                break  # در صورت طولانی بودن فشرده بودن، خروج از حلقه
                        row.value(0)  # تنظیم ردیف فعلی به LOW پس از دریافت کلید
                        return key  # بازگرداندن کلید فشرده شده
            row.value(0)  # تنظیم ردیف به LOW پس از بررسی تمام ستون‌ها
        return None  # اگر هیچ کلیدی فشرده نشده باشد، بازگرداندن None

# ============================================================
# کلاس Joystick: کنترل جوی‌استیک جهت دریافت جهت حرکت یا فشردن CENTER
# ============================================================
class Joystick:
    def __init__(self, vrx_pin, vry_pin, sw_pin):
        # ایجاد ADC برای خواندن مقدار آنالوگ محور X
        self.vrx = machine.ADC(machine.Pin(vrx_pin))
        # ایجاد ADC برای خواندن مقدار آنالوگ محور Y
        self.vry = machine.ADC(machine.Pin(vry_pin))
        # تعریف پین دکمه CENTER به عنوان ورودی با مقاومت pull-up
        self.sw = machine.Pin(sw_pin, machine.Pin.IN, machine.Pin.PULL_UP)

    async def read(self):
        """
        تابع غیرهمزمان read: خواندن وضعیت جوی‌استیک
          - اگر دکمه CENTER فشرده شده باشد، "CENTER" بازگردانده می‌شود.
          - در غیر این صورت بر اساس مقادیر آنالوگ محورهای X و Y جهت مربوطه بازگردانده می‌شود.
        """
        if not self.sw.value():  # اگر دکمه CENTER فشرده شده (مقدار LOW)
            await asyncio.sleep_ms(150)  # تأخیر 150 میلی‌ثانیه جهت تثبیت وضعیت
            return "CENTER"  # بازگرداندن "CENTER"
        # خواندن مقادیر آنالوگ از محورهای X و Y
        x = self.vrx.read_u16()
        y = self.vry.read_u16()
        if x < 20000:
            return "RIGHT"  # اگر مقدار X کمتر از 20000، بازگرداندن "RIGHT"
        elif x > 45000:
            return "LEFT"   # اگر مقدار X بیشتر از 45000، بازگرداندن "LEFT"
        elif y < 20000:
            return "DOWN"   # اگر مقدار Y کمتر از 20000، بازگرداندن "DOWN"
        elif y > 45000:
            return "UP"     # اگر مقدار Y بیشتر از 45000، بازگرداندن "UP"
        return None  # در صورت عدم تشخیص جهت، بازگرداندن None

# ============================================================
# کلاس Buzzer: کنترل بوزر با استفاده از PWM جهت پخش صدا
# ============================================================
class Buzzer:
    def __init__(self, pin_num):
        # ایجاد شیء پین برای بوزر
        self.pin = machine.Pin(pin_num)
        # ایجاد شیء PWM بر روی پین بوزر
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(1000)  # تنظیم فرکانس اولیه PWM به 1000 هرتز
        self.pwm.duty_u16(0)  # خاموش کردن بوزر با duty 0

    async def play_tone(self, frequency, duration):
        """
        تابع play_tone: پخش صدای با فرکانس مشخص به مدت معین
        """
        self.pwm.freq(frequency)  # تنظیم فرکانس PWM به مقدار داده شده
        self.pwm.duty_u16(32768)  # تنظیم duty cycle به 50% (32768 از 65535)
        await asyncio.sleep_ms(duration)  # صبر به مدت زمان مشخص (duration)
        self.pwm.duty_u16(0)  # خاموش کردن بوزر

    async def beep(self, duration=100):
        # بوق زدن با فرکانس 1000 هرتز به مدت پیش‌فرض 100 میلی‌ثانیه
        await self.play_tone(1000, duration)

# ============================================================
# تابع replay_pattern: بازپخش دنباله فعلی روی LCD با تأخیر افزایشی
# ============================================================
async def replay_pattern(seq, lcd, buzzer, extra_delay):
    lcd.clear()  # پاکسازی LCD
    lcd.putstr("Replay Pattern")  # نمایش متن "Replay Pattern" روی LCD
    await asyncio.sleep_ms(1000)  # صبر به مدت 1000 میلی‌ثانیه
    # پیمایش هر سیگنال در دنباله
    for sig in seq:
        lcd.clear()  # پاکسازی LCD برای نمایش سیگنال جدید
        if sig[0] == "KEY":  # اگر سیگنال از نوع KEY است
            display_key = sig[1] if sig[1] else "?"  # تعیین کلید برای نمایش (در صورت عدم وجود، "?" نمایش داده شود)
            lcd.putstr("Key: {}".format(display_key))  # نمایش کلید روی LCD
            await buzzer.play_tone(sig[2], 150)  # پخش صدای مربوط به سیگنال به مدت 150 میلی‌ثانیه
        else:  # اگر سیگنال از نوع JOY است
            label = {"UP": "Up", "DOWN": "Down", "LEFT": "Left", "RIGHT": "Right", "CENTER": "Press"}[sig[1]]
            lcd.putstr("Joy: {}".format(label))  # نمایش جهت جوی‌استیک روی LCD
            await buzzer.play_tone(sig[2], 150)  # پخش صدای مربوط به سیگنال به مدت 150 میلی‌ثانیه
        await asyncio.sleep_ms(500 + extra_delay)  # صبر به مدت 500 + extra_delay میلی‌ثانیه
    lcd.clear()  # پاکسازی LCD
    lcd.putstr("Now, input:")  # نمایش پیام "Now, input:" جهت درخواست ورودی از کاربر
    await asyncio.sleep_ms(500)  # صبر به مدت 500 میلی‌ثانیه

# ============================================================
# تابع get_player_input: دریافت ورودی کاربر برای الگوی نمایش داده شده
# تغییر: در صورت فشردن "*" همه ورودی‌های قبلی پاک شده و از ابتدا آغاز می‌شود.
# ============================================================
async def get_player_input(expected_seq, lcd, keypad, joystick, buzzer, time_limit):
    penalty = 0  # مقدار اولیه penalty برابر 0
    # حلقه بیرونی: تا زمانی که کاربر بتواند الگو را به طور کامل وارد کند
    while True:
        success = True  # فرض اولیه این است که ورودی کاربر صحیح است
        # پیمایش هر سیگنال موجود در الگو
        for sig in expected_seq:
            start_time = utime.ticks_ms()  # ثبت زمان شروع دریافت ورودی برای سیگنال فعلی
            input_received = False  # تعیین عدم دریافت ورودی صحیح برای این سیگنال
            # حلقه داخلی: دریافت ورودی برای سیگنال فعلی تا پایان زمان محدود
            while utime.ticks_diff(utime.ticks_ms(), start_time) < time_limit:
                key = await keypad.scan()  # اسکن کیپد جهت دریافت کلید فشرده شده
                if key is not None:  # اگر یک کلید دریافت شد
                    if key == "*":  # در صورت فشردن کلید "*"
                        penalty += 5  # افزایش penalty به میزان 5
                        # بازپخش الگو با تأخیر متناسب با penalty
                        await replay_pattern(expected_seq, lcd, buzzer, penalty * 100)
                        success = False  # علامت‌گذاری عدم موفقیت جهت پاکسازی ورودی‌های قبلی
                        break  # خروج از حلقه داخلی برای این سیگنال
                    if key == "#":  # اگر کلید "#" فشرده شد
                        return (True, penalty)  # بازگرداندن نتیجه موفق همراه با penalty (عبور از سطح)
                    if sig[0] == "KEY":  # اگر سیگنال فعلی از نوع KEY است
                        if key == sig[1]:  # در صورت مطابقت کلید دریافت شده با کلید مورد انتظار
                            await buzzer.play_tone(sig[2], 100)  # پخش صدای مربوط به سیگنال به مدت 100 میلی‌ثانیه
                            input_received = True  # علامت‌گذاری دریافت ورودی صحیح
                            break  # خروج از حلقه داخلی برای این سیگنال
                        else:
                            return (False, penalty)  # در صورت عدم تطابق، بازگرداندن نتیجه اشتباه همراه با penalty
                if sig[0] == "JOY":  # اگر سیگنال فعلی از نوع JOY است
                    joy_val = await joystick.read()  # خواندن وضعیت جوی‌استیک
                    if joy_val is not None:  # اگر مقدار دریافت شد
                        if joy_val == sig[1]:  # در صورت مطابقت جهت دریافت شده با جهت مورد انتظار
                            await buzzer.play_tone(sig[2], 100)  # پخش صدای مربوط به سیگنال به مدت 100 میلی‌ثانیه
                            input_received = True  # علامت‌گذاری دریافت ورودی صحیح
                            break  # خروج از حلقه داخلی
                        else:
                            return (False, penalty)  # در صورت عدم تطابق، بازگرداندن نتیجه اشتباه همراه با penalty
                await asyncio.sleep_ms(20)  # تأخیر 20 میلی‌ثانیه جهت کاهش مصرف CPU
            # در صورت عدم دریافت ورودی صحیح برای سیگنال فعلی
            if not input_received:
                success = False
                break  # خروج از پیمایش سیگنال‌های الگو
        if success:  # اگر تمامی ورودی‌های مورد انتظار به درستی دریافت شده باشند
            return (True, penalty)  # بازگرداندن نتیجه موفق همراه با penalty
        # در صورت عدم موفقیت (مثلاً به دلیل فشردن "*" در میانه ورودی)، حلقه بیرونی از ابتدا آغاز می‌شود

# ============================================================
# تابع play_sequence: اجرای بازی شامل نمایش دنباله، دریافت ورودی و به‌روزرسانی وضعیت بازی
# ============================================================
async def play_sequence(lcd, keypad, joystick, buzzer):
    sequence = []      # تعریف لیستی برای ذخیره دنباله سیگنال‌ها؛ هر عنصر شامل (نوع، مقدار و tone) است
    level = 1          # سطح اولیه بازی برابر با 1
    lives = 3          # تعداد زندگی‌های اولیه برابر با 3
    score = 0          # امتیاز اولیه برابر با 0

    # تابع کمکی add_signal: تولید یک سیگنال تصادفی (KEY یا JOY) همراه با tone تصادفی
    def add_signal():
        signal_type = random.choice(["KEY", "JOY"])  # انتخاب تصادفی نوع سیگنال
        if signal_type == "KEY":
            # ایجاد لیست کلیدهای مجاز (بدون "*" و "#")
            keys_flat = [k for row in [["1", "2", "3", "A"],
                                        ["4", "5", "6", "B"],
                                        ["7", "8", "9", "C"],
                                        ["*", "0", "#", "D"]]
                         for k in row if k not in ["*", "#"]]
            key = random.choice(keys_flat)  # انتخاب تصادفی یک کلید از لیست
            tone = random.randint(400, 800)  # تولید tone تصادفی در محدوده 400 تا 800
            return (signal_type, key, tone)  # بازگرداندن تاپل (نوع، کلید، tone)
        else:
            # برای نوع JOY، تولید جهت تصادفی
            joy_signal = random.choice(["UP", "DOWN", "LEFT", "RIGHT", "CENTER"])
            tone = random.randint(600, 1000)  # تولید tone تصادفی در محدوده 600 تا 1000
            return (signal_type, joy_signal, tone)  # بازگرداندن تاپل (نوع، جهت، tone)

    sequence.append(add_signal())  # افزودن اولین سیگنال به دنباله (طول اولیه 1)

    # حلقه اصلی بازی: ادامه تا زمانی که تعداد زندگی‌ها بیشتر از 0 باشد
    while lives > 0:
        lcd.clear()  # پاکسازی LCD
        # نمایش وضعیت فعلی بازی: سطح، تعداد زندگی‌ها و امتیاز
        lcd.putstr("LVL:{}  LIVE:{}   SCORE:{}".format(level, lives, score))
        await asyncio.sleep_ms(1200)  # صبر به مدت 1200 میلی‌ثانیه جهت نمایش وضعیت

        # تعیین حالت معکوس (Reverse Mode) برای هر 5 سطح
        reverse_mode = (level % 5 == 0)
        if reverse_mode:
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("Reverse Mode!")  # نمایش پیام "Reverse Mode!"
            await asyncio.sleep_ms(800)  # تأخیر 800 میلی‌ثانیه
            ds = list(reversed(sequence))  # ایجاد لیست ds به صورت معکوس از دنباله
        else:
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("Watch LVL:{}".format(level))  # نمایش پیام "Watch LVL:" همراه با شماره سطح
            await asyncio.sleep_ms(800)  # تأخیر 800 میلی‌ثانیه
            ds = sequence  # استفاده از دنباله اصلی

        # نمایش تک تک سیگنال‌های دنباله به کاربر جهت مشاهده
        for sig in ds:
            lcd.clear()  # پاکسازی LCD
            if sig[0] == "KEY":  # اگر سیگنال از نوع KEY است
                display_key = sig[1] if sig[1] else "?"  # تعیین کلید برای نمایش
                lcd.putstr("Key: {}".format(display_key))  # نمایش کلید روی LCD
                await buzzer.play_tone(sig[2], 150)  # پخش صدای مربوط به سیگنال به مدت 150 میلی‌ثانیه
            else:  # اگر سیگنال از نوع JOY است
                label = {"UP": "Up", "DOWN": "Down", "LEFT": "Left", "RIGHT": "Right", "CENTER": "Press"}[sig[1]]
                lcd.putstr("Joy: {}".format(label))  # نمایش جهت روی LCD
                await buzzer.play_tone(sig[2], 150)  # پخش صدای مربوط به سیگنال به مدت 150 میلی‌ثانیه
            delay = max(500 - level * 20, 200)  # محاسبه تأخیر بین نمایش سیگنال‌ها (حداقل 200 میلی‌ثانیه)
            await asyncio.sleep_ms(delay)  # صبر به مدت محاسبه شده

        # تعیین زمان محدود برای دریافت ورودی کاربر بر اساس سطح و طول دنباله
        time_limit = max(5000 - (level - 1) * 100 + len(sequence) * 50, 2000)
        lcd.clear()  # پاکسازی LCD
        # نمایش پیام ورودی: در حالت معکوس "Input (Rev):" و در حالت عادی "Input Pattern:"
        if reverse_mode:
            lcd.putstr("Input (Rev):")
        else:
            lcd.putstr("Input Pattern:")

        # دریافت ورودی کاربر برای دنباله نمایش داده شده
        result, replay_penalty = await get_player_input(ds, lcd, keypad, joystick, buzzer, time_limit)
        if result:  # اگر ورودی کاربر صحیح بود
            pts = level * 10 - replay_penalty  # محاسبه امتیاز کسب شده بر اساس سطح و penalty
            if pts < 0:
                pts = 0  # در صورت منفی شدن امتیاز، مقدار آن صفر می‌شود
            score += pts  # افزودن امتیاز کسب شده به امتیاز کل
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("Correct!\n+{} pts".format(pts))  # نمایش پیام موفقیت همراه با امتیاز کسب شده
            await buzzer.play_tone(1000, 200)  # پخش صدای صحیح به مدت 200 میلی‌ثانیه
            await asyncio.sleep_ms(1000)  # تأخیر 1000 میلی‌ثانیه جهت نمایش پیام
            level += 1  # افزایش سطح بازی
            if random.random() < 0.6:  # با احتمال 60 درصد
                sequence.append(add_signal())  # افزودن یک سیگنال جدید به دنباله
        else:  # اگر ورودی کاربر اشتباه بود
            lives -= 1  # کاهش یک زندگی
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("Incorrect!\nLives: {}".format(lives))  # نمایش پیام خطا همراه با تعداد زندگی‌های باقی مانده
            await buzzer.play_tone(300, 500)  # پخش صدای خطا به مدت 500 میلی‌ثانیه
            await asyncio.sleep_ms(2000)  # تأخیر 2000 میلی‌ثانیه

    # پس از اتمام زندگی‌ها (بازی به پایان می‌رسد)
    lcd.clear()  # پاکسازی LCD
    lcd.putstr("Game Over!\nScore: {}".format(score))  # نمایش پیام "Game Over!" همراه با امتیاز نهایی
    save_score(score)  # ذخیره امتیاز نهایی در فایل
    await asyncio.sleep_ms(3000)  # تأخیر 3000 میلی‌ثانیه جهت نمایش پیام پایان بازی
    return  # پایان تابع play_sequence

# ============================================================
# تابع test_mode: حالت تست جهت بررسی عملکرد ورودی‌های کیپد و جوی‌استیک
# ============================================================
async def test_mode(lcd, keypad, joystick, buzzer):
    lcd.clear()  # پاکسازی LCD
    lcd.putstr("TEST MODE:\nPress key/joy\nCENTER to exit")  # نمایش پیام حالت تست روی LCD
    await asyncio.sleep_ms(1500)  # تأخیر 1500 میلی‌ثانیه جهت نمایش پیام
    while True:  # حلقه دریافت ورودی در حالت تست
        key = await keypad.scan()  # دریافت ورودی از کیپد
        j_val = await joystick.read()  # دریافت ورودی از جوی‌استیک
        if j_val == "CENTER":  # اگر دکمه CENTER فشرده شد
            break  # خروج از حالت تست
        if key is not None:  # اگر ورودی از کیپد دریافت شد
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("Key: {}".format(key))  # نمایش کلید دریافت شده
            await buzzer.beep(100)  # بوق زدن به مدت 100 میلی‌ثانیه
            await asyncio.sleep_ms(300)  # تأخیر 300 میلی‌ثانیه
        elif j_val is not None:  # اگر ورودی از جوی‌استیک دریافت شد
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("Joy: {}".format(j_val))  # نمایش جهت دریافت شده
            await buzzer.beep(100)  # بوق زدن به مدت 100 میلی‌ثانیه
            await asyncio.sleep_ms(300)  # تأخیر 300 میلی‌ثانیه
        else:  # در صورت عدم دریافت ورودی
            lcd.clear()  # پاکسازی LCD
            lcd.putstr("TEST MODE:\nPress key/joy")  # نمایش پیام درخواست ورودی
        await asyncio.sleep_ms(100)  # تأخیر 100 میلی‌ثانیه جهت کاهش مصرف CPU
    lcd.clear()  # پاکسازی LCD پس از پایان حالت تست
    lcd.putstr("Exiting Test Mode...")  # نمایش پیام خروج از حالت تست
    await asyncio.sleep_ms(1000)  # تأخیر 1000 میلی‌ثانیه

# ============================================================
# تابع game_adventure: اجرای ماجراجویی بازی شامل دروازه معبد و نمایش دنباله بازی
# ============================================================
async def game_adventure(lcd, keypad, joystick, buzzer):
    lcd.clear()  # پاکسازی LCD
    lcd.putstr("Temple Gate\nWill Open...")  # نمایش پیام آغازین "Temple Gate Will Open..."
    await buzzer.play_tone(800, 200)  # پخش صدای 800 هرتز به مدت 200 میلی‌ثانیه
    await asyncio.sleep_ms(2000)  # تأخیر 2000 میلی‌ثانیه جهت نمایش پیام
    lcd.clear()  # پاکسازی LCD
    lcd.putstr("Press CENTER\nto Enter")  # نمایش پیام "Press CENTER to Enter"
    while True:  # حلقه انتظار برای دریافت ورودی جهت ورود به بازی
        if (await joystick.read()) == "CENTER":  # اگر دکمه CENTER از طریق جوی‌استیک فشرده شد
            break  # خروج از حلقه و ادامه بازی
        await asyncio.sleep_ms(100)  # تأخیر 100 میلی‌ثانیه
    await play_sequence(lcd, keypad, joystick, buzzer)  # آغاز اجرای دنباله بازی (تابع play_sequence)

# ============================================================
# تابع main_menu: نمایش منوی اصلی بازی و انتخاب گزینه‌ها
# (حالت خروج حذف شده است؛ گزینه "Exit" از منو حذف شده)
# ============================================================
async def main_menu():
    # تعیین پین‌های مربوط به ردیف‌ها و ستون‌های کیپد
    keypad_rows = [2, 3, 4, 5]
    keypad_cols = [6, 7, 8, 9]
    # تعریف ماتریس کلیدهای کیپد
    keypad_keys = [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"]
    ]
    # ایجاد شیء Keypad با پین‌های مشخص و ماتریس کلیدها
    keypad_inst = Keypad(keypad_rows, keypad_cols, keypad_keys)
    # ایجاد شیء Joystick با پین‌های مشخص (برای محورهای X، Y و دکمه CENTER)
    joystick_inst = Joystick(vrx_pin=26, vry_pin=27, sw_pin=22)
    # ایجاد شیء Buzzer برای کنترل بوزر (روی پین 15)
    buzzer_inst = Buzzer(15)
    # ایجاد شیء I2C با پین‌های 17 (SCL) و 16 (SDA) و فرکانس 400000
    i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16), freq=400000)
    # ایجاد شیء LCD از طریق I2C با آدرس 0x27 و ابعاد 2×16
    lcd_inst = I2cLcd(i2c, 0x27, 2, 16)

    lcd_inst.clear()  # پاکسازی LCD
    lcd_inst.putstr("Journey of the\nMemory Hero")  # نمایش پیام آغازین بازی روی LCD
    await asyncio.sleep_ms(2000)  # تأخیر 2000 میلی‌ثانیه جهت نمایش پیام آغازین

    random.seed(utime.ticks_cpu())  # تنظیم بذر تصادفی بر اساس ticks_cpu
    # تعریف لیست گزینه‌های منوی اصلی (حالت "Exit" حذف شده است)
    menu_options = ["Start Adventure", "Instructions", "Test Mode", "Score"]
    current_option = 0  # تعیین گزینه فعلی منو (اندیس 0)
    while True:  # حلقه نمایش منو تا زمانی که کاربر گزینه‌ای را انتخاب کند
        lcd_inst.clear()  # پاکسازی LCD
        lcd_inst.putstr("MENU:\n{}".format(menu_options[current_option]))  # نمایش گزینه فعلی منو روی LCD
        direction = None  # مقداردهی اولیه متغیر جهت (direction) به None
        while direction is None:  # تا زمانی که جهت دریافت نشده است
            direction = await joystick_inst.read()  # خواندن جهت جوی‌استیک
            await asyncio.sleep_ms(50)  # تأخیر 50 میلی‌ثانیه جهت کاهش مصرف CPU
        # بررسی جهت دریافت شده جهت تغییر گزینه منو
        if direction == "UP":
            current_option = (current_option - 1) % len(menu_options)  # حرکت به گزینه قبلی (چرخشی)
        elif direction == "DOWN":
            current_option = (current_option + 1) % len(menu_options)  # حرکت به گزینه بعدی (چرخشی)
        elif direction == "CENTER":
            break  # در صورت فشردن CENTER، انتخاب گزینه فعلی و خروج از حلقه منو
        await asyncio.sleep_ms(200)  # تأخیر 200 میلی‌ثانیه جهت جلوگیری از چندبار خواندن ورودی

    selected = menu_options[current_option]  # تعیین گزینه انتخاب شده بر اساس اندیس current_option
    if selected == "Instructions":  # اگر گزینه "Instructions" انتخاب شده باشد
        lcd_inst.clear()  # پاکسازی LCD
        lcd_inst.putstr("Repeat the pattern\nwithin time.")  # نمایش دستورالعمل بازی
        await asyncio.sleep_ms(3000)  # تأخیر 3000 میلی‌ثانیه جهت نمایش پیام
        return True  # بازگرداندن True جهت ادامه نمایش منو
    elif selected == "Score":  # اگر گزینه "Score" انتخاب شده باشد
        lcd_inst.clear()  # پاکسازی LCD
        saved = load_score()  # بارگذاری امتیاز ذخیره شده
        if saved is not None:
            lcd_inst.putstr("Last Score:\n{}".format(saved))  # نمایش امتیاز ذخیره شده
        else:
            lcd_inst.putstr("No score saved!")  # در صورت عدم وجود امتیاز
        await asyncio.sleep_ms(3000)  # تأخیر 3000 میلی‌ثانیه جهت نمایش پیام
        return True  # بازگرداندن True جهت ادامه نمایش منو
    elif selected == "Test Mode":  # اگر گزینه "Test Mode" انتخاب شده باشد
        await test_mode(lcd_inst, keypad_inst, joystick_inst, buzzer_inst)  # ورود به حالت تست
        return True  # بازگرداندن True جهت ادامه نمایش منو
    else:  # در غیر این صورت (گزینه "Start Adventure")
        await game_adventure(lcd_inst, keypad_inst, joystick_inst, buzzer_inst)  # آغاز ماجراجویی بازی
        return True  # بازگرداندن True جهت ادامه نمایش منو

# ============================================================
# تابع main: حلقه اصلی منوی بازی جهت اجرای مداوم منو
# ============================================================
async def main():
    while True:  # اجرای مداوم منو در یک حلقه بی‌نهایت
        cont = await main_menu()  # فراخوانی تابع main_menu و دریافت نتیجه (همیشه True از آن دریافت می‌شود)
        if not cont:  # اگر به هر دلیلی نتیجه False دریافت شود (در این نسخه این حالت وجود ندارد)
            break  # خروج از حلقه و پایان برنامه

# اجرای تابع main به صورت غیرهمزمان
asyncio.run(main())
