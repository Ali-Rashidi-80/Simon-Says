# Ali Rashidi
# t.me/WriteYourWay

import machine,utime,random,uasyncio as asyncio  # وارد کردن ماژول‌های machine، utime، random و uasyncio (با نام مستعار asyncio)
from i2c_lcd import I2cLcd  # وارد کردن کلاس I2cLcd از کتابخانه i2c_lcd برای کنترل LCD از طریق I2C

def save_score(s):  # تعریف تابع save_score برای ذخیره امتیاز s در فایل
 try:  # شروع بلاک try برای جلوگیری از خطاهای احتمالی
  with open("score.txt","w") as f: f.write(str(s))  # باز کردن فایل score.txt در حالت نوشتن و نوشتن امتیاز به صورت رشته
 except Exception: pass  # در صورت بروز هر خطا، ادامه بده (هیچ عملی انجام نده)

def load_score():  # تعریف تابع load_score برای بارگذاری امتیاز از فایل
 try:  # شروع بلاک try
  with open("score.txt","r") as f: return f.read().strip()  # باز کردن فایل score.txt در حالت خواندن، خواندن محتوا و حذف فاصله‌های اضافی و بازگرداندن آن
 except Exception: return None  # در صورت بروز خطا، بازگرداندن None

class Keypad:  # تعریف کلاس Keypad برای کنترل کیپد 4×4
 def __init__(self,r,c,keys):  # سازنده دریافت لیست پین‌های ردیف (r)، ستون (c) و ماتریس کلیدها (keys)
  self.rows=[machine.Pin(p,machine.Pin.OUT) for p in r]  # ایجاد لیستی از پین‌ها برای ردیف‌ها به عنوان خروجی
  self.cols=[machine.Pin(p,machine.Pin.IN,machine.Pin.PULL_DOWN) for p in c]  # ایجاد لیستی از پین‌ها برای ستون‌ها به عنوان ورودی با pull-down
  self.keys=keys  # ذخیره ماتریس کلیدها در متغیر self.keys
 async def scan(self):  # تعریف متد اسکن به صورت غیرهمزمان برای بررسی فشرده شدن کلید
  for i,row in enumerate(self.rows):  # پیمایش ردیف‌ها به همراه اندیس i
   row.value(1)  # تنظیم خروجی ردیف به HIGH
   for j,col in enumerate(self.cols):  # پیمایش ستون‌ها به همراه اندیس j
    if col.value()==1:  # اگر ورودی ستون برابر با 1 (کلید فشرده شده) است
     await asyncio.sleep_ms(50)  # تأخیر 50 میلی‌ثانیه برای جلوگیری از نویز
     if col.value()==1:  # بررسی دوباره وضعیت ستون پس از تأخیر
      k=self.keys[i][j]; st=utime.ticks_ms()  # تعیین کلید فشرده شده و ثبت زمان شروع آزادسازی
      while col.value()==1:  # تا زمانی که کلید همچنان فشرده است
       await asyncio.sleep_ms(10)  # تأخیر 10 میلی‌ثانیه
       if utime.ticks_diff(utime.ticks_ms(),st)>500: break  # اگر فشرده بودن بیش از 500 میلی‌ثانیه طول بکشد، خروج از حلقه
      row.value(0); return k  # بازگرداندن کلید و تنظیم ردیف به LOW
   row.value(0)  # پس از بررسی تمام ستون‌ها، تنظیم ردیف به LOW
  return None  # اگر هیچ کلیدی فشرده نشده باشد، بازگرداندن None

class Joystick:  # تعریف کلاس Joystick برای کنترل جوی‌استیک
 def __init__(self,vrx,vry,sw):  # سازنده دریافت پین‌های محور X (vrx)، محور Y (vry) و دکمه (sw)
  self.vrx=machine.ADC(machine.Pin(vrx)); self.vry=machine.ADC(machine.Pin(vry))  # ایجاد ADC برای خواندن مقادیر آنالوگ محورهای X و Y
  self.sw=machine.Pin(sw,machine.Pin.IN,machine.Pin.PULL_UP)  # تعریف پین دکمه به عنوان ورودی با pull-up
 async def read(self):  # تعریف متد خواندن وضعیت جوی‌استیک به صورت غیرهمزمان
  if not self.sw.value():  # اگر دکمه فشرده شده (LOW) است
   await asyncio.sleep_ms(150); return "CENTER"  # تأخیر 150 میلی‌ثانیه و بازگرداندن "CENTER"
  x,y=self.vrx.read_u16(),self.vry.read_u16()  # خواندن مقادیر آنالوگ از محورهای X و Y
  if x<20000: return "RIGHT"  # اگر مقدار X کمتر از 20000 است، بازگرداندن "RIGHT"
  elif x>45000: return "LEFT"  # اگر مقدار X بیشتر از 45000 است، بازگرداندن "LEFT"
  elif y<20000: return "DOWN"  # اگر مقدار Y کمتر از 20000 است، بازگرداندن "DOWN"
  elif y>45000: return "UP"  # اگر مقدار Y بیشتر از 45000 است، بازگرداندن "UP"
  return None  # در غیر این صورت، بازگرداندن None

class Buzzer:  # تعریف کلاس Buzzer برای کنترل بوزر با استفاده از PWM
 def __init__(self,pin):  # سازنده دریافت شماره پین بوزر
  self.pin=machine.Pin(pin); self.pwm=machine.PWM(self.pin)  # تعریف پین بوزر و ایجاد PWM روی آن
  self.pwm.freq(1000); self.pwm.duty_u16(0)  # تنظیم فرکانس اولیه به 1000 هرتز و خاموش کردن بوزر (duty 0)
 async def play_tone(self,f,d):  # تعریف متد play_tone به صورت غیرهمزمان با دریافت فرکانس (f) و مدت زمان (d)
  self.pwm.freq(f); self.pwm.duty_u16(32768)  # تنظیم فرکانس به f و روشن کردن بوزر با duty 50%
  await asyncio.sleep_ms(d); self.pwm.duty_u16(0)  # صبر به مدت d میلی‌ثانیه و سپس خاموش کردن بوزر
 async def beep(self,d=100): await self.play_tone(1000,d)  # تعریف متد beep با فرکانس 1000 و مدت زمان پیش‌فرض 100 میلی‌ثانیه

async def replay_pattern(seq,lcd,bz,ed):  # تعریف تابع replay_pattern برای بازپخش الگو با تأخیر اضافی ed
 lcd.clear(); lcd.putstr("Replay Pattern"); await asyncio.sleep_ms(1000)  # پاکسازی LCD، نمایش "Replay Pattern" و صبر 1000 میلی‌ثانیه
 for s in seq:  # پیمایش هر سیگنال در الگو
  lcd.clear()  # پاکسازی LCD
  if s[0]=="KEY":  # اگر سیگنال از نوع KEY است
   k=s[1] if s[1] else "?"  # تعیین کلید (در صورت نبود، "?" استفاده شود)
   lcd.putstr("Key: {}".format(k)); await bz.play_tone(s[2],150)  # نمایش کلید و پخش صدای مربوطه به مدت 150 میلی‌ثانیه
  else:  # در غیر این صورت (سیگنال جوی‌استیک)
   lab={"UP":"Up","DOWN":"Down","LEFT":"Left","RIGHT":"Right","CENTER":"Press"}[s[1]]  # تعیین برچسب جهت بر اساس مقدار
   lcd.putstr("Joy: {}".format(lab)); await bz.play_tone(s[2],150)  # نمایش جهت و پخش صدای مربوطه به مدت 150 میلی‌ثانیه
  await asyncio.sleep_ms(500+ed)  # صبر به مدت 500+ed میلی‌ثانیه
 lcd.clear(); lcd.putstr("Now, input:"); await asyncio.sleep_ms(500)  # پاکسازی LCD، نمایش "Now, input:" و صبر 500 میلی‌ثانیه

# تغییر: در صورت فشردن "*" همه ورودی‌ها ریست شوند
async def get_player_input(exp,lcd,kp,joy,bz,tl):  # تعریف تابع دریافت ورودی کاربر با پارامترهای الگو (exp)، LCD، کیپد (kp)، جوی‌استیک (joy)، بوزر (bz) و زمان محدود (tl)
 pen=0  # مقدار اولیه penalty برابر صفر است
 while True:  # حلقه بیرونی تا زمانی که ورودی کامل دریافت شود
  success=True  # فرض می‌کنیم ورودی موفق است
  for s in exp:  # پیمایش هر سیگنال در الگو
   st=utime.ticks_ms(); inp=False  # ثبت زمان شروع و تعیین دریافت نشدن ورودی برای این سیگنال (inp=False)
   while utime.ticks_diff(utime.ticks_ms(),st)<tl:  # تا زمانی که زمان سپری نشده است
    k=await kp.scan()  # اسکن کیپد برای دریافت کلید
    if k is not None:  # اگر کلیدی دریافت شد
     if k=="*":  # اگر کلید "*" فشرده شد
      pen+=5; await replay_pattern(exp,lcd,bz,pen*100)  # افزایش penalty به اندازه 5 و بازپخش الگو با تأخیر متناسب
      success=False; break  # تعیین عدم موفقیت (ریست ورودی) و خروج از حلقه داخلی
     if k=="#": return (True,pen)  # اگر کلید "#" فشرده شد، مرحله رد شده و ورودی درست فرض می‌شود
     if s[0]=="KEY":  # اگر سیگنال فعلی از نوع KEY است
      if k==s[1]:  # اگر کلید دریافت شده با سیگنال مطابقت دارد
       await bz.play_tone(s[2],100); inp=True; break  # پخش صدای مربوطه، علامت زدن دریافت ورودی و خروج از حلقه
      else: return (False,pen)  # در غیر این صورت، ورودی اشتباه است؛ بازگرداندن False به همراه penalty
    if s[0]=="JOY":  # اگر سیگنال فعلی از نوع JOY است
     j=await joy.read()  # خواندن وضعیت جوی‌استیک
     if j is not None:  # اگر مقدار دریافت شد
      if j==s[1]:  # اگر جهت مطابقت دارد
       await bz.play_tone(s[2],100); inp=True; break  # پخش صدای مربوطه، علامت زدن دریافت ورودی و خروج از حلقه
      else: return (False,pen)  # در غیر این صورت، ورودی اشتباه است؛ بازگرداندن False به همراه penalty
    await asyncio.sleep_ms(20)  # تأخیر 20 میلی‌ثانیه برای کاهش مصرف CPU
   if not inp:  # اگر برای این سیگنال ورودی دریافت نشده است
    success=False; break  # تعیین عدم موفقیت و خروج از حلقه
  if success:  # اگر ورودی کامل موفق بود
   return (True,pen)  # بازگرداندن True به همراه penalty
async def play_sequence(lcd,kp,joy,bz):  # تعریف تابع اصلی نمایش دنباله‌های بازی
 seq=[]; lvl=1; lives=3; score=0  # تعریف متغیرهای اولیه: الگو (seq)، سطح (lvl)، تعداد زندگی (lives) و امتیاز (score)
 def add_sig():  # تعریف تابع کمکی برای افزودن سیگنال جدید به الگو
  t=random.choice(["KEY","JOY"])  # انتخاب تصادفی نوع سیگنال (KEY یا JOY)
  if t=="KEY":  # اگر نوع سیگنال KEY است
   flat=[k for row in [["1","2","3","A"],["4","5","6","B"],["7","8","9","C"],["*","0","#","D"]] for k in row if k not in ["*","#"]]  # ایجاد لیستی از کلیدهای مجاز (بدون "*" و "#")
   return (t,random.choice(flat),random.randint(400,800))  # بازگرداندن سیگنال شامل نوع، یک کلید تصادفی و tone تصادفی بین 400 تا 800
  else: return (t,random.choice(["UP","DOWN","LEFT","RIGHT","CENTER"]),random.randint(600,1000))  # اگر نوع سیگنال JOY است، بازگرداندن جهت تصادفی و tone بین 600 تا 1000
 seq.append(add_sig())  # افزودن اولین سیگنال به الگو
 while lives>0:  # حلقه تا زمانی که تعداد زندگی باقی است
  lcd.clear(); lcd.putstr("LVL:{}  LIVE:{}   SCORE:{}".format(lvl,lives,score))  # نمایش سطح، تعداد زندگی و امتیاز روی LCD
  await asyncio.sleep_ms(1200)  # تأخیر 1200 میلی‌ثانیه
  rev=(lvl%5==0)  # تعیین حالت معکوس (reverse mode) در هر 5 سطح
  if rev:
   lcd.clear(); lcd.putstr("Reverse Mode!"); await asyncio.sleep_ms(800); ds=list(reversed(seq))  # در حالت معکوس، نمایش پیام و تعیین الگو به صورت معکوس
  else:
   lcd.clear(); lcd.putstr("Watch LVL:{}".format(lvl)); await asyncio.sleep_ms(800); ds=seq  # در حالت عادی، نمایش سطح و تعیین الگو به صورت معمول
  for s in ds:  # پیمایش هر سیگنال در الگو
   lcd.clear()  # پاکسازی LCD
   if s[0]=="KEY":  # اگر سیگنال از نوع KEY است
    k=s[1] if s[1] else "?"  # تعیین کلید (یا "?" در صورت عدم وجود)
    lcd.putstr("Key: {}".format(k)); await bz.play_tone(s[2],150)  # نمایش کلید و پخش تن مربوطه به مدت 150 میلی‌ثانیه
   else:
    lab={"UP":"Up","DOWN":"Down","LEFT":"Left","RIGHT":"Right","CENTER":"Press"}[s[1]]  # تعیین برچسب جهت برای سیگنال JOY
    lcd.putstr("Joy: {}".format(lab)); await bz.play_tone(s[2],150)  # نمایش جهت و پخش تن مربوطه به مدت 150 میلی‌ثانیه
   await asyncio.sleep_ms(max(500-lvl*20,200))  # تأخیر متناسب با سطح (حداقل 200 میلی‌ثانیه)
  tl=max(5000-(lvl-1)*100+len(seq)*50,2000)  # محاسبه زمان محدود ورودی بر اساس سطح و طول الگو
  lcd.clear(); lcd.putstr("Input (Rev):" if rev else "Input Pattern:")  # نمایش پیام ورودی (با توجه به حالت معکوس یا عادی)
  res,pen=await get_player_input(ds,lcd,kp,joy,bz,tl)  # دریافت ورودی کاربر و penalty مرتبط
  if res:  # اگر ورودی صحیح بود
   pts=max(lvl*10-pen,0); score+=pts; lcd.clear(); lcd.putstr("Correct!\n+{} pts".format(pts))  # محاسبه امتیاز، اضافه کردن آن به score و نمایش پیام موفقیت
   await bz.play_tone(1000,200); await asyncio.sleep_ms(1000); lvl+=1  # پخش صدای صحیح، تأخیر و افزایش سطح
   if random.random()<0.6: seq.append(add_sig())  # با احتمال 60٪، افزودن سیگنال جدید به الگو
  else:
   lives-=1; lcd.clear(); lcd.putstr("Incorrect!\nLives: {}".format(lives))  # در صورت ورودی اشتباه، کاهش یک زندگی و نمایش پیام
   await bz.play_tone(300,500); await asyncio.sleep_ms(2000)  # پخش صدای خطا و تأخیر
  # در صورت موفقیت در یک سطح، ورودی‌های کاربر پاک شده و سطح بعدی آغاز می‌شود
 lcd.clear(); lcd.putstr("Game Over!\nScore: {}".format(score))  # پس از پایان بازی (تمام شدن زندگی)، نمایش پیام Game Over و امتیاز نهایی
 save_score(score); await asyncio.sleep_ms(3000)  # ذخیره امتیاز در فایل و تأخیر 3000 میلی‌ثانیه

async def test_mode(lcd,kp,joy,bz):  # تعریف تابع test_mode برای حالت تست جهت بررسی ورودی‌ها
 lcd.clear(); lcd.putstr("TEST MODE:\nPress key/joy\nCENTER to exit")  # نمایش پیام حالت تست
 await asyncio.sleep_ms(1500)  # تأخیر 1500 میلی‌ثانیه
 while True:  # حلقه برای دریافت ورودی در حالت تست
  k=await kp.scan(); j=await joy.read()  # اسکن کیپد و خواندن وضعیت جوی‌استیک
  if j=="CENTER": break  # اگر دکمه CENTER فشرده شد، خروج از حالت تست
  if k is not None:
   lcd.clear(); lcd.putstr("Key: {}".format(k)); await bz.beep(100); await asyncio.sleep_ms(300)  # نمایش کلید دریافت‌شده، بوق زدن و تأخیر
  elif j is not None:
   lcd.clear(); lcd.putstr("Joy: {}".format(j)); await bz.beep(100); await asyncio.sleep_ms(300)  # نمایش جهت دریافت‌شده، بوق زدن و تأخیر
  else:
   lcd.clear(); lcd.putstr("TEST MODE:\nPress key/joy")  # در صورت عدم دریافت ورودی، نمایش پیام تست
  await asyncio.sleep_ms(100)  # تأخیر 100 میلی‌ثانیه
 lcd.clear(); lcd.putstr("Exiting Test Mode..."); await asyncio.sleep_ms(1000)  # نمایش پیام خروج از حالت تست و تأخیر

async def game_adventure(lcd,kp,joy,bz):  # تعریف تابع game_adventure برای اجرای ماجراجویی بازی
 lcd.clear(); lcd.putstr("Temple Gate\nWill Open...")  # نمایش پیام اولیه "Temple Gate Will Open..."
 await bz.play_tone(800,200); await asyncio.sleep_ms(2000)  # پخش تن 800 هرتز به مدت 200 میلی‌ثانیه و تأخیر 2000 میلی‌ثانیه
 lcd.clear(); lcd.putstr("Press CENTER\nto Enter")  # نمایش پیام "Press CENTER to Enter"
 while True:
  if (await joy.read())=="CENTER": break; await asyncio.sleep_ms(100)  # انتظار تا فشرده شدن CENTER توسط جوی‌استیک و سپس خروج از حلقه
 await play_sequence(lcd,kp,joy,bz)  # آغاز تابع play_sequence برای شروع بازی

async def main_menu():  # تعریف تابع main_menu برای نمایش منوی اصلی بازی
 kp_rows=[2,3,4,5]; kp_cols=[6,7,8,9]  # تعیین پین‌های ردیف و ستون کیپد
 kp_keys=[["1","2","3","A"],["4","5","6","B"],["7","8","9","C"],["*","0","#","D"]]  # تعیین ماتریس کلیدهای کیپد
 kp=Keypad(kp_rows,kp_cols,kp_keys); js=Joystick(26,27,22); bz=Buzzer(15)  # ایجاد اشیاء Keypad، Joystick و Buzzer
 i2c=machine.I2C(0,scl=machine.Pin(17),sda=machine.Pin(16),freq=400000)  # ایجاد شیء I2C با پین‌های مشخص
 lcd=I2cLcd(i2c,0x27,2,16)  # ایجاد شیء LCD با آدرس 0x27 و ابعاد 2×16
 lcd.clear(); lcd.putstr("Journey of the\nMemory Hero"); await asyncio.sleep_ms(2000)  # نمایش پیام آغازین بازی و تأخیر 2000 میلی‌ثانیه
 random.seed(utime.ticks_cpu()); opts=["Start Adventure","Instructions","Test Mode","Score"]  # تنظیم بذر تصادفی و تعریف گزینه‌های منو
 cur=0  # تعیین گزینه فعلی منو به عنوان اولین گزینه
 while True:  # حلقه نمایش منو تا انتخاب گزینه
  lcd.clear(); lcd.putstr("MENU:\n{}".format(opts[cur])); d=None  # نمایش گزینه فعلی منو و مقداردهی اولیه d به None
  while d is None:
   d=await js.read(); await asyncio.sleep_ms(50)  # خواندن ورودی جوی‌استیک با تأخیر 50 میلی‌ثانیه برای کاهش مصرف CPU
  if d=="UP": cur=(cur-1)%len(opts)  # اگر جهت UP دریافت شد، تغییر گزینه منو به بالا
  elif d=="DOWN": cur=(cur+1)%len(opts)  # اگر جهت DOWN دریافت شد، تغییر گزینه منو به پایین
  elif d=="CENTER": break  # اگر CENTER دریافت شد، انتخاب گزینه و خروج از حلقه
  await asyncio.sleep_ms(200)  # تأخیر 200 میلی‌ثانیه
 sel=opts[cur]  # تعیین گزینه انتخاب شده بر اساس مقدار cur
 if sel=="Instructions":  # اگر گزینه Instructions انتخاب شده باشد
  lcd.clear(); lcd.putstr("Repeat the pattern\nwithin time."); await asyncio.sleep_ms(3000)  # نمایش دستورالعمل و تأخیر 3000 میلی‌ثانیه
 elif sel=="Score":  # اگر گزینه Score انتخاب شده باشد
  lcd.clear(); s=load_score(); lcd.putstr("Last Score:\n{}".format(s) if s is not None else "No score saved!")  # نمایش امتیاز ذخیره شده یا پیام عدم وجود امتیاز
  await asyncio.sleep_ms(3000)
 elif sel=="Test Mode": await test_mode(lcd,kp,js,bz)  # اگر گزینه Test Mode انتخاب شد، ورود به حالت تست
 else: await game_adventure(lcd,kp,js,bz)  # در غیر این صورت (Start Adventure) آغاز ماجراجویی بازی
 return True  # بازگرداندن True برای ادامه نمایش منو

async def main():  # تعریف تابع اصلی برنامه
 while True: await main_menu()  # اجرای مداوم منوی اصلی
asyncio.run(main())  # اجرای تابع main به صورت غیرهمزمان
