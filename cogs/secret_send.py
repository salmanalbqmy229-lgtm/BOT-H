import discord
from discord import app_commands
from discord.ext import commands

# --- المعرفات المصرح لها باستخدام الأمر واستقبال رسائل الخاص ---
ALLOWED_USERS = [1495450684731162664, 1499889093780312204] # آيديهاتكم الشخصية

# رتب الإدارة العليا المصرح لها باستخدام أمر الإرسال فقط
ALLOWED_ROLES = [1552700483938947072, 1552699892214792256] # أونر و كونر

class SecretSend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # دالة داخلية للتحقق من الصلاحيات (أنت، خويك، أو رتب الأونر والكونر)
    def has_permission(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in ALLOWED_USERS:
            return True
        if hasattr(interaction.user, 'roles'):
            user_role_ids = [role.id for role in interaction.user.roles]
            if any(r_id in ALLOWED_ROLES for r_id in user_role_ids):
                return True
        return False

    # --- 1. حدث الاستماع التلقائي لرسائل الخاص المرسلة للبوت ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # يتجاهل رسائل البوت نفسه، ويتأكد أن الرسالة قادمة في الخاص (DM) فقط
        if message.author.bot or message.guild is not None:
            return

        # تصميم إمبيد فخم يعرض الرسالة الموجهة للبوت وبيانات المرسل
        spy_embed = discord.Embed(
            title="📥 رسالة خاصة جديدة مستلمة للبوت!",
            description=f"👤 **المرسل:** {message.author.mention} ({message.author.name})\n🆔 **آي دي المرسل:** `{message.author.id}`\n\n💬 **محتوى الرسالة:**\n{message.content}",
            color=discord.Color.orange()
        )
        spy_embed.set_thumbnail(url=message.author.display_avatar.url)
        spy_embed.set_footer(text="HAVEN Spy System •")

        # إرسال النسخة التلقائية لك أنت وخويك مباشرة في الخاص (DM)
        for user_id in ALLOWED_USERS:
            target_user = self.bot.get_user(user_id)
            if target_user:
                try:
                    await target_user.send(embed=spy_embed)
                except:
                    pass # يتخطى إذا كان حساب أحدكم مقفل الخاص

    # --- 2. أمر الإرسال المائل الخاص والمحمي ---
    @app_commands.command(name="dm-send", description="أمر خاص لإرسال رسائل مباشرة لأي عضو في السيرفر")
    @app_commands.describe(user="اختر العضو أو ضع الآي دي حقه", message="اكتب النص اللي تبي البوت يرسله للخاص حقه")
    async def dm_send(self, interaction: discord.Interaction, user: discord.User, message: str):
        # التحقق من الصلاحية الأمنية للمستدعي
        if not self.has_permission(interaction):
            await interaction.response.send_message("❌ نعتذر منك، هذا الأمر غير موجود أو مخصص لأشخاص آخرين.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # إرسال النص للعضو المستهدف مباشرة حتى لو كان كلام قوي أو عيب
            await user.send(content=message)
            
            # إرسال نسخة تأكيدية فورية لك في الخاص لتشوف وش انرسل
            confirmation_embed = discord.Embed(
                title="🚀 تم إرسال الرسالة بنجاح!",
                description=f"**إلى العضو:** {user.mention} ({user.id})\n\n**نص الرسالة المرسلة:**\n{message}",
                color=discord.Color.green()
            )
            try:
                await interaction.user.send(embed=confirmation_embed)
            except:
                pass

            await interaction.followup.send(f"✅ تم إرسال الرسالة إلى {user.name} بنجاح، ووصلتك نسخة في الخاص يا بعدي.", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send(f"❌ فشل الإرسال! يبدو أن العضو `{user.name}` مقفل الخاص حقه أو صاك البوت بلوك.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ غير متوقع أثناء محاولة الإرسال: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SecretSend(bot))
