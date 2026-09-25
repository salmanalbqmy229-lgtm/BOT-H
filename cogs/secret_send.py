import discord
from discord import app_commands
from discord.ext import commands

# --- الآيديهات المصرح لها فقط باستخدام الأمر (أنت وخويك) ---
ALLOWED_USERS = [1495450684731162664, 1499889093780312204]

class SecretSend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dm-send", description="أمر خاص لإرسال رسائل مباشرة لأي عضو في السيرفر")
    @app_commands.describe(user="اختر العضو أو ضع الآي دي حقه", message="اكتب النص اللي تبي البوت يرسله للخاص حقه")
    async def dm_send(self, interaction: discord.Interaction, user: discord.User, message: str):
        # 1. التحقق من هوية الشخص اللي استخدم الأمر (إذا مو أنت أو خويك يرفض تماماً)
        if interaction.user.id not in ALLOWED_USERS:
            await interaction.response.send_message("❌ نعتذر منك، هذا الأمر غير موجود أو مخصص لأشخاص آخرين.", ephemeral=True)
            return

        # تأخير الاستجابة لضمان معالجة الإرسال بدون تعليق
        await interaction.response.defer(ephemeral=True)

        try:
            # 2. إرسال الرسالة النصية المكتوبة مباشرة لخاص العضو المستهدف
            await user.send(content=message)
            
            # 3. إرسال نسخة تأكيدية لك أنت شخصياً في الخاص لتشوف وش انرسل للولد
            confirmation_embed = discord.Embed(
                title="🚀 تم إرسال الرسالة بنجاح!",
                description=f"**إلى العضو:** {user.mention} ({user.id})\n\n**نص الرسالة المرسلة:**\n{message}",
                color=discord.Color.green()
            )
            try:
                await interaction.user.send(embed=confirmation_embed)
            except:
                pass # في حال كان خاصك مقفل ما يعلق الكود

            # رد مخفي في الشات لتأكيد العملية لك
            await interaction.followup.send(f"✅ تم إرسال الرسالة إلى {user.name} بنجاح، ووصلتك نسخة في الخاص يا بعدي.", ephemeral=True)

        except discord.Forbidden:
            # في حال كان العضو مقفل الخاص حقه بالكامل أو صاك البوت بلوك
            await interaction.followup.send(f"❌ فشل الإرسال! يبدو أن العضو `{user.name}` مقفل الخاص حقه أو صاك البوت بلوك.", ephemeral=True)
        except Exception as e:
            # أي خطأ برمي آخر غير متوقع
            await interaction.followup.send(f"❌ حدث خطأ غير متوقع أثناء محاولة الإرسال: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SecretSend(bot))
