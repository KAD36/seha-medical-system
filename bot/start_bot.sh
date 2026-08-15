#!/bin/bash

# سكريبت تشغيل بوت تيليجرام للإجازات المرضية
# Seha Sick Leave Bot Startup Script

echo "🚀 بدء تشغيل بوت صحة للإجازات المرضية..."
echo "🚀 Starting Seha Sick Leave Bot..."

# التحقق من وجود Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 غير مثبت. يرجى تثبيت Python3 أولاً."
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# التحقق من وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 غير مثبت. يرجى تثبيت pip3 أولاً."
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# الانتقال إلى مجلد البوت
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 مجلد العمل: $SCRIPT_DIR"
echo "📁 Working directory: $SCRIPT_DIR"

# إنشاء البيئة الافتراضية إذا لم تكن موجودة
if [ ! -d "venv" ]; then
    echo "🔧 إنشاء البيئة الافتراضية..."
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# تفعيل البيئة الافتراضية
echo "🔧 تفعيل البيئة الافتراضية..."
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# تثبيت المتطلبات
echo "📦 تثبيت المتطلبات..."
echo "📦 Installing requirements..."
pip install -r requirements.txt

# إنشاء المجلدات المطلوبة
echo "📁 إنشاء المجلدات المطلوبة..."
echo "📁 Creating required directories..."
mkdir -p /home/ubuntu/output
mkdir -p /home/ubuntu/fonts
mkdir -p /home/ubuntu/upload

# نسخ الخطوط والصور
echo "📋 نسخ الخطوط والصور..."
echo "📋 Copying fonts and images..."
cp -r fonts/* /home/ubuntu/fonts/ 2>/dev/null || echo "⚠️ لم يتم العثور على مجلد الخطوط"
cp -r *.jpg *.png /home/ubuntu/upload/ 2>/dev/null || echo "⚠️ لم يتم العثور على الصور"

# التحقق من ملف الإعدادات
if [ ! -f "config.py" ]; then
    echo "❌ ملف config.py مفقود!"
    echo "❌ config.py file is missing!"
    exit 1
fi

# التحقق من رمز البوت
if grep -q "YOUR_BOT_TOKEN_HERE" config.py; then
    echo "⚠️ يرجى تحديث رمز البوت في ملف config.py"
    echo "⚠️ Please update the bot token in config.py"
    echo "📝 افتح ملف config.py وضع رمز البوت الصحيح"
    echo "📝 Open config.py and set the correct bot token"
    exit 1
fi

echo "✅ جميع الإعدادات جاهزة!"
echo "✅ All configurations are ready!"
echo ""
echo "🤖 تشغيل البوت..."
echo "🤖 Starting the bot..."
echo ""

# تشغيل البوت
python3 bot.py

