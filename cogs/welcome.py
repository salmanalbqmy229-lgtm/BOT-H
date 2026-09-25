import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

class WelcomeAndLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "bot_settings.db"
        
        # الآيديهات الافتراضية المخصصة لسيرفر HAVEN التي زودتني بها
        self.DEFAULT_WELCOME_ID = 1552698475530158133
        self.DEFAULT_LEAVE_ID = 1552707125870854184
        self.CATEGORY_ID = 1552698475530158131
        
        self.init_db()

    # إنشاء قاعدة البيانات والجدول والتأكد من إدخال الآيديهات الافتراضية
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_channels (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                leave_channel_id INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    # دالة لجلب الآي دي الخاص بالروم (تأخذ القيمة الافتراضية إذا لم يتم التعديل بالأوامر)
    def get_channel_id(self, guild_id, channel_type):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT {channel_type} FROM server_channels WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            return result[0]
        
        # إرجاع الآيديهات الافتراضية التي وضعتها إذا كانت قاعدة البيانات فارغة
        if channel_type == "welcome_channel_id":
            return self.DEFAULT_WELCOME_ID
        elif channel_type == "leave_channel_id":
            return self.DEFAULT_LEAVE_ID
        return None

    # دالة لحفظ أو تحديث الروم في قاعدة البيانات
    def save_channel_id(self, guild_id, channel_id, channel_type):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO server_channels (guild_id, {channel_type})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {channel_type} = excluded.{channel_type}
        ''', (guild_id, channel_id))
        conn.commit()
        conn.close()

    # --- أوامر السلاش في حال رغبت في تغيير الرومات مستقبلاً ---

    @app_commands.command(name="set-welcome", description="تعديل روم الترحيب الافتراضية لسيرفر HAVEN")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(channel="اختر روم الترحيب الجديدة")
    async def set_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.save_channel_id(interaction.guild_id, channel.id, "welcome_channel_id")
        await interaction.response.send_message(f"💾 تم تحديث وحفظ روم الترحيب بنجاح: {channel.mention}", ephemeral=True)

    @app_commands.command(name="set-leave", description="تعديل روم المغادرة الافتراضية لسيرفر HAVEN")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(channel="اختر روم المغادرة الجديدة")
    async def set_leave(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.save_channel_id(interaction.guild_id, channel.id, "leave_channel_id")
        await interaction.response.send_message(f"💾 تم تحديث وحفظ روم المغادرة بنجاح: {channel.mention}", ephemeral=True)


    # --- الأحداث التلقائية مع المنشن وصور الحساب ---

    # 1. حدث دخول عضو جديد
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = self.get_channel_id(member.guild.id, "welcome_channel_id")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                # حساب ترتيب العضو في السيرفر
                member_count = len(member.guild.members)
                
                # إنشاء تصميم الترحيب لـ HAVEN
                embed = discord.Embed(
                    title="✨ عضو جديد في HAVEN ✨",
                    description=f"يا هلا يا مرحبا في سيرفرنا **HAVEN** شرفتنا ونورتنا! ✨\n\n👤 **العضو:** {member.mention}",
                    color=discord.Color.from_rgb(114, 137, 218)
                )
                avatar_url = member.display_avatar.url
                embed.set_image(url=avatar_url)
                embed.set_footer(text=f"أنت العضو رقم: {member_count} 🌟")
                
                await channel.send(content=f"أهلاً بك {member.mention}", embed=embed)

    # 2. حدث خروج عضو
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel_id = self.get_channel_id(member.guild.id, "leave_channel_id")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                # إنشاء تصميم المغادرة لـ HAVEN
                embed = discord.Embed(
                    title="😢 غادرنا شخص غالي...",
                    description=f"مع السلامه يا حب بنفقدك يالغالي.. 💔\n\n👤 **العضو:** {member.mention}",
                    color=discord.Color.red()
                )
                avatar_url = member.display_avatar.url
                embed.set_image(url=avatar_url)
                
                await channel.send(content=f"{member.mention} غادرنا..", embed=embed)

# ربط الملف تلقائياً
async def setup(bot):
    await bot.add_cog(WelcomeAndLeave(bot))
