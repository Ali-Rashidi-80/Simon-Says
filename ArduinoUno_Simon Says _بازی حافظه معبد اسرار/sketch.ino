// Ali Rashidi
// t.me/WriteYourWay
// Simon Says v2- بازی حافظه معبد اسرار 
// برعکس بودن عملکرد جوی استیک، در کامپایل واقعی روی برد برطرف میشود

#include <Wire.h>                        // وارد کردن کتابخانه Wire برای ارتباط I2C
#include <LiquidCrystal_I2C.h>           // وارد کردن کتابخانه LiquidCrystal_I2C برای کنترل LCD با I2C
#include <Keypad.h>                      // وارد کردن کتابخانه Keypad برای کنترل کیپد ماتریسی
#include <EEPROM.h>                      // وارد کردن کتابخانه EEPROM برای ذخیره‌سازی داده‌ها در حافظه EEPROM

// ------------------------------
// تعریف نت‌ها (فرکانس‌های صوتی) برای ملودی‌ها
// ------------------------------ 
#define NOTE_C4 262                      // تعریف فرکانس نُت C4 به مقدار 262 هرتز
#define NOTE_D4 294                      // تعریف فرکانس نُت D4 به مقدار 294 هرتز
#define NOTE_E4 330                      // تعریف فرکانس نُت E4 به مقدار 330 هرتز
#define NOTE_F4 349                      // تعریف فرکانس نُت F4 به مقدار 349 هرتز
#define NOTE_G4 392                      // تعریف فرکانس نُت G4 به مقدار 392 هرتز
#define NOTE_A4 440                      // تعریف فرکانس نُت A4 به مقدار 440 هرتز
#define NOTE_B4 494                      // تعریف فرکانس نُت B4 به مقدار 494 هرتز
#define NOTE_C5 523                      // تعریف فرکانس نُت C5 به مقدار 523 هرتز

#define NOTE_G3 196                      // تعریف فرکانس نُت G3 به مقدار 196 هرتز
#define NOTE_E3 165                      // تعریف فرکانس نُت E3 به مقدار 165 هرتز
#define NOTE_C3 131                      // تعریف فرکانس نُت C3 به مقدار 131 هرتز
#define NOTE_B3 247                      // تعریف فرکانس نُت B3 به مقدار 247 هرتز
#define NOTE_A3 220                      // تعریف فرکانس نُت A3 به مقدار 220 هرتز

// ================================
// تنظیمات ثابت و پیکربندی‌های اولیه
// ================================
#define MAX_SEQ 12                       // تعریف حداکثر تعداد سیگنال‌ها (برای کاهش مصرف حافظه)

// --- تنظیمات LCD I2C (آدرس 0x27، صفحه 16×2) ---
LiquidCrystal_I2C lcd(0x27, 16, 2);       // ایجاد شیء lcd با آدرس 0x27 و اندازه 16x2

// --- تنظیمات کیپد 4×4 ---
const byte ROWS = 4;                      // تعداد ردیف‌های کیپد 4
const byte COLS = 4;                      // تعداد ستون‌های کیپد 4
char keys[ROWS][COLS] = {                 // تعریف آرایه دوبعدی کلیدها برای کیپد
  {'1', '2', '3', 'A'},                  // ردیف اول
  {'4', '5', '6', 'B'},                  // ردیف دوم
  {'7', '8', '9', 'C'},                  // ردیف سوم
  {'*', '0', '#', 'D'}                   // ردیف چهارم
};
byte rowPins[ROWS] = {2, 3, 4, 5};         // پین‌های آردوینو متصل به ردیف‌های کیپد
byte colPins[COLS] = {6, 7, 8, 9};           // پین‌های آردوینو متصل به ستون‌های کیپد
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);  // ایجاد شیء keypad با تنظیمات فوق

// --- تنظیمات جوی‌استیک ---  
// محور X به A0، محور Y به A1 و دکمه CENTER به پین دیجیتال 10
#define JOY_BTN_PIN 10                    // تعریف پین دکمه CENTER جوی‌استیک به پین 10

// --- تنظیمات بوزر ---  
#define BUZZER_PIN 11                     // تعریف پین بوزر به پین 11

// ================================
// ساختار سیگنال (مشابه تاپل در پایتون)
// ================================
struct Signal {
  String type;    // نوع سیگنال ("KEY" یا "JOY")
  String value;   // مقدار سیگنال: برای KEY یک عدد/حرف و برای JOY جهت (مثلاً "UP")
  int tone;       // فرکانس صدای مربوط به سیگنال
};

// -------------------------------
// توابع کمکی برای ذخیره و بازیابی امتیاز از EEPROM
// -------------------------------
void saveScore(int score) {
  EEPROM.put(0, score);
}

int loadScore() {
  int score = 0;
  EEPROM.get(0, score);
  return score;
}

// -------------------------------
// تابع خواندن جوی‌استیک با دِبَنس (debounce)
// -------------------------------
String readJoystick() {
  static String lastDirection = "";
  static unsigned long lastChangeTime = 0;
  String currentDirection = "";
  unsigned long now = millis();

  // بررسی دکمه CENTER
  if (digitalRead(JOY_BTN_PIN) == LOW) {
    currentDirection = "CENTER";
  } else {
    int x = analogRead(A0);
    int y = analogRead(A1);
    // اصلاح جهت‌ها:
    // اگر x کمتر از 312 باشد → LEFT
    // اگر x بیشتر از 703 باشد → RIGHT
    // اگر y کمتر از 312 باشد → UP
    // اگر y بیشتر از 703 باشد → DOWN
    if (x < 312) currentDirection = "LEFT";
    else if (x > 703) currentDirection = "RIGHT";
    else if (y < 312) currentDirection = "UP";
    else if (y > 703) currentDirection = "DOWN";
    else currentDirection = "";
  }

  if (currentDirection != lastDirection) {
    lastDirection = currentDirection;
    lastChangeTime = now;
    return "";
  } else {
    if (now - lastChangeTime >= 50)
      return currentDirection;
  }
  return "";
}

// -------------------------------
// تابع پخش صدای بوزر (با استفاده از tone)
// -------------------------------
void playTone(int frequency, int duration) {
  tone(BUZZER_PIN, frequency, duration);
  delay(duration);
  noTone(BUZZER_PIN);
}

// -------------------------------
// تابع بوق کوتاه (beep)
// -------------------------------
void beep(int duration = 100) {
  playTone(1000, duration);
}

// -------------------------------
// تابع تولید یک سیگنال تصادفی (KEY یا JOY)
// -------------------------------
Signal addSignal() {
  Signal sig;
  int r = random(0, 2);
  if (r == 0) {
    sig.type = "KEY";
    char allowedKeys[] = {'1','2','3','A','4','5','6','B','7','8','9','C','0','D'};
    int n = sizeof(allowedKeys) / sizeof(allowedKeys[0]);
    int index = random(0, n);
    sig.value = String(allowedKeys[index]);
    sig.tone = random(400, 801);
  } else {
    sig.type = "JOY";
    String directions[5] = {"UP", "DOWN", "LEFT", "RIGHT", "CENTER"};
    int index = random(0, 5);
    sig.value = directions[index];
    sig.tone = random(600, 1001);
  }
  return sig;
}

// -------------------------------
// تابع پخش ملودی شروع بازی به‌صورت تصادفی (Random Start Tune)
// -------------------------------
void playRandomStartTune() {
  int tuneChoice = random(0, 3);
  switch(tuneChoice) {
    case 0: {
      int melody[] = {NOTE_C4, NOTE_D4, NOTE_E4, NOTE_F4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_C5};
      int durations[] = {150, 150, 150, 150, 150, 150, 150, 300};
      for (int i = 0; i < 8; i++) {
        playTone(melody[i], durations[i]);
        delay(50);
      }
      break;
    }
    case 1: {
      int melody[] = {NOTE_C5, NOTE_B4, NOTE_A4, NOTE_G4, NOTE_F4, NOTE_E4, NOTE_D4, NOTE_C4};
      int durations[] = {150, 150, 150, 150, 150, 150, 150, 300};
      for (int i = 0; i < 8; i++) {
        playTone(melody[i], durations[i]);
        delay(50);
      }
      break;
    }
    case 2: {
      int melody[] = {NOTE_C4, NOTE_E4, NOTE_G4, NOTE_C5, NOTE_G4, NOTE_E4, NOTE_C4};
      int durations[] = {200, 200, 200, 300, 200, 200, 300};
      for (int i = 0; i < 7; i++) {
        playTone(melody[i], durations[i]);
        delay(50);
      }
      break;
    }
  }
}

// -------------------------------
// تابع پخش ملودی پایان بازی به صورت تصادفی (Random Game Over Tune)
// -------------------------------
void playGameOverTune() {
  int tuneChoice = random(0, 3);
  switch(tuneChoice) {
    case 0: {
      // ملودی پایان بازی شماره 1 (نزولی کلاسیک)
      int melody[] = {NOTE_E4, NOTE_D4, NOTE_C4, NOTE_B3, NOTE_A3};
      int durations[] = {300, 300, 300, 300, 600};
      for (int i = 0; i < 5; i++) {
        playTone(melody[i], durations[i]);
        delay(50);
      }
      break;
    }
    case 1: {
      // ملودی پایان بازی شماره 2 (نزولی متفاوت)
      int melody[] = {NOTE_D4, NOTE_C4, NOTE_B3, NOTE_A3, NOTE_G3};
      int durations[] = {250, 250, 250, 250, 500};
      for (int i = 0; i < 5; i++) {
        playTone(melody[i], durations[i]);
        delay(50);
      }
      break;
    }
    case 2: {
      // ملودی پایان بازی شماره 3 (ریتمیک)
      int melody[] = {NOTE_E4, NOTE_E4, NOTE_D4, NOTE_C4, NOTE_C4, NOTE_B3};
      int durations[] = {200, 200, 200, 200, 200, 400};
      for (int i = 0; i < 6; i++) {
        playTone(melody[i], durations[i]);
        delay(50);
      }
      break;
    }
  }
}

// -------------------------------
// تابع بازپخش دنباله روی LCD (Replay Pattern)
// -------------------------------
void replayPattern(Signal seq[], int seqLen, int extraDelay) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(F("Replay Pattern"));
  delay(1000);
  for (int i = 0; i < seqLen; i++) {
    lcd.clear();
    if (seq[i].type == "KEY") {
      lcd.print(F("Key: "));
      lcd.print(seq[i].value);
      playTone(seq[i].tone, 150);
    } else {
      lcd.print(F("Joy: "));
      if (seq[i].value == "CENTER")
        lcd.print(F("Press"));
      else if (seq[i].value == "UP")
        lcd.print(F("Up"));
      else if (seq[i].value == "DOWN")
        lcd.print(F("Down"));
      else if (seq[i].value == "LEFT")
        lcd.print(F("Left"));
      else if (seq[i].value == "RIGHT")
        lcd.print(F("Right"));
      playTone(seq[i].tone, 150);
    }
    delay(500 + extraDelay);
  }
  lcd.clear();
  lcd.print(F("Now, input:"));
  delay(500);
}

// -------------------------------
// تابع دریافت ورودی کاربر برای دنباله داده‌شده  
// -------------------------------
// بازگرداندن مقادیر:
//   1  → ورودی صحیح
//   0  → ورودی اشتباه یا زمان به پایان رسیده (timeout)
//  -1  → فشردن "*" (ریست ورودی)
int getPlayerInput(Signal seq[], int seqLen, unsigned long time_limit, int &penalty) {
  for (int i = 0; i < seqLen; i++) {
    unsigned long startTime = millis();
    unsigned long lastInputTime = millis();
    bool inputReceived = false;
    while (millis() - startTime < time_limit) {
      
      if (millis() - lastInputTime >= 10000) {
         idleAnimationCycle();
         lastInputTime = millis();
      }
      
      char key = keypad.getKey();
      String joyVal = readJoystick();
      if (key != NO_KEY || joyVal != "") {
         lastInputTime = millis();
      }
      
      if (key != NO_KEY) {
        if (key == '*') {
          penalty += 5;
          replayPattern(seq, seqLen, penalty * 100);
          return -1;
        }
        if (key == '#') {
          lcd.clear();
          lcd.print(F("Now, input:"));
          delay(500);
          return 1;
        }
        if (seq[i].type == "KEY") {
          if (String(key) == seq[i].value) {
            playTone(seq[i].tone, 100);
            inputReceived = true;
            break;
          } else {
            return 0;
          }
        }
      }
      if (seq[i].type == "JOY") {
        if (joyVal != "") {
          if (joyVal == seq[i].value) {
            playTone(seq[i].tone, 100);
            inputReceived = true;
            break;
          } else {
            return 0;
          }
        }
      }
      delay(20);
    }
    if (!inputReceived) {
      return 0;
    }
  }
  return 1;
}

// -------------------------------
// تابع اجرای بازی (نمایش دنباله، دریافت ورودی و به‌روزرسانی وضعیت بازی)
// -------------------------------
void playSequence() {
  Signal sequence[MAX_SEQ];
  int seqLen = 0;
  int level = 1;
  int lives = 3;
  int score = 0;
  sequence[0] = addSignal();
  seqLen = 1;
  while (lives > 0) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("LVL:" + String(level) + "  LIVE:" + String(lives));
    lcd.setCursor(0, 1);
    lcd.print("SCORE:" + String(score));
    delay(1200);
    bool reverseMode = (level % 5 == 0);
    Signal ds[MAX_SEQ];
    int dsLen = seqLen;
    if (reverseMode) {
      lcd.clear();
      lcd.print(F("Reverse Mode!"));
      delay(800);
      for (int i = 0; i < seqLen; i++) {
        ds[i] = sequence[seqLen - 1 - i];
      }
    } else {
      lcd.clear();
      lcd.print("Watch LVL:" + String(level));
      delay(800);
      for (int i = 0; i < seqLen; i++) {
        ds[i] = sequence[i];
      }
    }
    for (int i = 0; i < dsLen; i++) {
      lcd.clear();
      if (ds[i].type == "KEY") {
        lcd.print(F("Key: "));
        lcd.print(ds[i].value);
        playTone(ds[i].tone, 150);
      } else {
        lcd.print(F("Joy: "));
        if (ds[i].value == "CENTER")
          lcd.print(F("Press"));
        else if (ds[i].value == "UP")
          lcd.print(F("Up"));
        else if (ds[i].value == "DOWN")
          lcd.print(F("Down"));
        else if (ds[i].value == "LEFT")
          lcd.print(F("Left"));
        else if (ds[i].value == "RIGHT")
          lcd.print(F("Right"));
        playTone(ds[i].tone, 150);
      }
      int dTime = 500 - level * 20;
      if (dTime < 200) dTime = 200;
      delay(dTime);
    }
    int time_limit = 5000 - (level - 1) * 100 + seqLen * 50;
    if (time_limit < 2000) time_limit = 2000;
    int inputResult;
    int penalty = 0;
    while (true) {
      lcd.clear();
      if (reverseMode)
        lcd.print(F("Input (Rev):"));
      else
        lcd.print(F("Input Pattern:"));
      delay(500);
      inputResult = getPlayerInput(ds, dsLen, time_limit, penalty);
      if (inputResult == -1) {
        continue;
      } else {
        break;
      }
    }
    if (inputResult == 1) {
      int pts = level * 10 - penalty;
      if (pts < 0) pts = 0;
      score += pts;
      lcd.clear();
      lcd.print(F("Correct!"));
      lcd.setCursor(0, 1);
      lcd.print("+" + String(pts) + " pts");
      playTone(1000, 200);
      delay(1000);
      level++;
      if (random(0, 100) < 60 && seqLen < MAX_SEQ) {
        sequence[seqLen] = addSignal();
        seqLen++;
      }
    } else {
      lives--;
      lcd.clear();
      lcd.print(F("Incorrect!"));
      lcd.setCursor(0, 1);
      lcd.print("Lives: " + String(lives));
      playTone(300, 500);
      delay(2000);
    }
  }
  playGameOverTune();
  lcd.clear();
  lcd.print(F("Game Over!"));
  lcd.setCursor(0, 1);
  lcd.print("Score: " + String(score));
  int prevScore = loadScore();
  if (score > prevScore) {
    saveScore(score);
  }
  delay(3000);
}

// -------------------------------
// تابع ماجراجویی (Game Adventure)
// -------------------------------
void gameAdventure() {
  lcd.clear();
  lcd.print(F("Temple Gate"));
  lcd.setCursor(0, 1);
  lcd.print(F("Will Open..."));
  playTone(800, 200);
  delay(2000);
  playRandomStartTune();
  lcd.clear();
  lcd.print(F("Press CENTER"));
  lcd.setCursor(0, 1);
  lcd.print(F("to Enter"));
  while (true) {
    if (readJoystick() == "CENTER")
      break;
    delay(100);
  }
  playSequence();
}

// -------------------------------
// حالت تست (Test Mode)
// -------------------------------
void testMode() {
  lcd.clear();
  lcd.print(F("TEST MODE:"));
  lcd.setCursor(0, 1);
  lcd.print(F("Press key/joy"));
  delay(1500);
  while (true) {
    char key = keypad.getKey();
    String jVal = readJoystick();
    if (jVal == "CENTER")
      break;
    if (key != NO_KEY) {
      lcd.clear();
      lcd.print(F("Key: "));
      lcd.print(key);
      beep(100);
      delay(300);
    } else if (jVal != "") {
      lcd.clear();
      lcd.print(F("Joy: "));
      lcd.print(jVal);
      beep(100);
      delay(300);
    } else {
      lcd.clear();
      lcd.print(F("TEST MODE:"));
      lcd.setCursor(0, 1);
      lcd.print(F("Press key/joy"));
    }
    delay(100);
  }
  lcd.clear();
  lcd.print(F("Exiting Test Mode..."));
  delay(1000);
}

// -------------------------------
// تابع افکت متحرک حالت بی‌عملی در منو (Idle Animation)
// -------------------------------
void idleAnimationCycle() {
  // این تابع افکت‌های متنوعی را به صورت مداوم نمایش می‌دهد تا زمانی که کاربر ورودی ارسال کند.
  while (readJoystick() == "") {
    // افکت حرکت متن "Simon Says" از چپ به راست
    for (int pos = 0; pos < 7; pos++) {
      if (readJoystick() != "") return;
      lcd.clear();
      lcd.setCursor(pos, 0);
      lcd.print("Simon Says");
      delay(420);
    }
    
    // افکت چرخشی (نمایش متن "Input Waiting...")
    String waitText = "Input Waiting...";
    for (int offset = 0; offset <= 16 - waitText.length(); offset++) {
      if (readJoystick() != "") return;
      lcd.clear();
      lcd.setCursor(offset, 1);
      lcd.print(waitText);
      delay(1200);
    }
  }
}

// -------------------------------
// منوی اصلی بازی
// -------------------------------
void mainMenu() {
  String menuOptions[4] = {"Start Adventure", "Instructions", "Test Mode", "Score"};
  int currentOption = 0;
  lcd.clear();
  lcd.print(F("Journey of the"));
  lcd.setCursor(0, 1);
  lcd.print(F("Memory Hero"));
  delay(2000);
  randomSeed(analogRead(A2));

  unsigned long idleStart = millis();

  while (true) {
    lcd.clear();
    lcd.print(F("MENU:"));
    lcd.setCursor(0, 1);
    lcd.print(menuOptions[currentOption]);

    String direction = "";
    while (direction == "") {
      direction = readJoystick();
      if (millis() - idleStart >= 10000) {
         idleAnimationCycle();
         idleStart = millis();
         direction = readJoystick();
         if (direction != "") break;
      }
      delay(100);
    }
    
    if (direction == "UP") {
      currentOption = (currentOption - 1 + 4) % 4;
    } else if (direction == "DOWN") {
      currentOption = (currentOption + 1) % 4;
    } else if (direction == "CENTER") {
      break;
    }
    
    idleStart = millis();
    delay(200);
  }
  
  String selected = menuOptions[currentOption];
  if (selected == "Instructions") {
    lcd.clear();
    lcd.print(F("Repeat the pattern"));
    lcd.setCursor(0, 1);
    lcd.print(F("within time."));
    delay(3000);
    return;
  } else if (selected == "Score") {
    lcd.clear();
    int saved = loadScore();
    if (saved != 0) {
      lcd.print(F("Last Score:"));
      lcd.setCursor(0, 1);
      lcd.print(String(saved));
    } else {
      lcd.print(F("No score saved!"));
    }
    delay(3000);
    return;
  } else if (selected == "Test Mode") {
    testMode();
    return;
  } else {
    gameAdventure();
    return;
  }
}

// -------------------------------
// setup و loop اصلی
// -------------------------------
void setup() {
  pinMode(JOY_BTN_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  lcd.init();
  lcd.backlight();
}

void loop() {
  mainMenu();
  // پس از پایان هر انتخاب، دوباره به منوی اصلی باز می‌گردد
}
