import os
import sys
import discord
from discord.ext import commands

# قراءة التوكن مباشرة من متغيرات البيئة الخاصة بالاستضافة (Environment Variables)
TOKEN = os.getenv('DISCORD_TOKEN')

# إعداد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # قراءة المجلد الفرعي cogs تلقائياً وتحميل الملفات
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f'✅ تم تحميل الملف الفرعي بنجاح: {filename}')
                    except Exception as e:
                        print(f'❌ فشل تحميل الملف الفرعي {filename}: {e}')
        else:
            print("⚠️ تنبيه: مجلد 'cogs' غير موجود، يرجى إنشاؤه.")
        
        # مزامنة أوامر السلاش عالمياً مع ديسكورد
        print("جاري مزامنة أوامر السلاش عالمياً...")
        try:
            synced = await self.tree.sync()
            print(f"🚀 تمت مزامنة {len(synced)} أمر سلاش بنجاح وبوتك جاهز للعمل!")
        except Exception as e:
            print(f"❌ حدث خطأ أثناء مزامنة الأوامر: {e}")

    async def on_ready(self):
        print(f'🤖 تم تسجيل الدخول بنجاح باسم: {self.user.name} ({self.user.id})')

# تشغيل البوت
if __name__ == "__main__":
    bot = MyBot()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ حرج: لم يتم العثور على المتغير 'DISCORD_TOKEN' في إعدادات الاستضافة!")
        print("💡 تلميح: توجه إلى لوحة تحكم الاستضافة، واضف متغير جديد (Variable) باسم DISCORD_TOKEN وحط التوكن حقك داخله.")
