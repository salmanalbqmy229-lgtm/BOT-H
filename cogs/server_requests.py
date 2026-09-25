import discord, random, string
from discord import app_commands
from discord.ext import commands

# --- HAVEN IDs CONFIGURATION ---
REQUEST_LOG_CHANNEL_ID = 1552708534192308294  # روم استقبال الطلبات لدى الإدارة
ROLE_MANAGER_ID = 1552700984336195614        # رتبة مسؤول الإدارة
ROLE_ADMIN_ID = 1552701169611317349          # رتبة أدمن

# دالة لتوليد كود عشوائي فريد لكل طلب
def generate_request_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

# --- أزرار التحكم بالطلبات للإدارة (قبول / رفض) ---
class RequestActionsView(discord.ui.View):
    def __init__(self, user_id: int, req_type: str, details: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.req_type = req_type
        self.details = details

    async def is_admin(self, interaction: discord.Interaction):
        allowed = [ROLE_MANAGER_ID, ROLE_ADMIN_ID]
        if not any(r.id in allowed for r in interaction.user.roles) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا التحكم مخصص لإدارة HAVEN فقط!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="قبول الطلب", style=discord.ButtonStyle.success, custom_id="haven_accept_req", emoji="✅")
    async def accept_req(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.is_admin(interaction): return
        await interaction.response.defer()
        
        code = generate_request_code()
        embed = interaction.message.embeds[0]
        embed.title = f"✅ تم قبول الطلب [كود: {code}]"
        embed.color = discord.Color.green()
        embed.add_field(name="💼 الإداري المستلم:", value=interaction.user.mention, inline=False)
        
        for child in self.children: child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                dm_embed = discord.Embed(
                    title="🎉 أبشر، طلبك انقبل!",
                    description=(
                        f"أهلاً بك يا غالي، طلبك لـ (**{self.req_type}**) تم قبوله بنجاح!\n\n"
                        f"🔑 **كود الطلب الخاص بك:** `{code}`\n\n"
                        f"📋 **تفاصيل طلبك التي تم قبولها:**\n{self.details}\n\n"
                        "📌 **الخطوة التالية:** افتح تكت دعم وصور الكلام اللي هنا ووده لهم وبيضبطونك فوراً ✨."
                    ),
                    color=discord.Color.green()
                )
                await member.send(embed=dm_embed)
            except: pass

    @discord.ui.button(label="رفض الطلب", style=discord.ButtonStyle.danger, custom_id="haven_reject_req", emoji="❌")
    async def reject_req(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.is_admin(interaction): return
        await interaction.response.defer()
        
        embed = interaction.message.embeds[0]
        embed.title = f"❌ تم رفض الطلب | {self.req_type}"
        embed.color = discord.Color.red()
        embed.add_field(name="👤 المرفوض بواسطة:", value=interaction.user.mention, inline=False)
        
        for child in self.children: child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                dm_embed = discord.Embed(
                    title="⚠️ لأسف انرفض طلبك",
                    description=f"أهلاً بك، نعتذر منك لقد تم رفض طلبك لـ (**{self.req_type}**) من قبل إدارة السيرفر.",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except: pass

# --- النوافذ المنبثقة لجمع البيانات (Modals) ---
class RoomRequestModal(discord.ui.Modal, title="طلب روم جديد"):
    r_name = discord.ui.TextInput(label="اسم الروم المطلوبة", placeholder="اكتب اسم الروم هنا...", required=True)
    r_type = discord.ui.TextInput(label="صنف الروم (مثال: فويس شات)", placeholder="فويس شات، شات كتابي...", required=True)
    r_roles = discord.ui.TextInput(label="الرتب المسموح لها دخول الروم", placeholder="الكل، رتبة معينة...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        details = f"• **اسم الروم:** {self.r_name.value}\n• **الصنف:** {self.r_type.value}\n• **الرتب المسموح لها:** {self.r_roles.value}"
        await send_request_to_admin(interaction, "طلب روم", details)

class GirlsRequestModal(discord.ui.Modal, title="طلب توثيق بنات"):
    g_name = discord.ui.TextInput(label="وش اسمك؟", placeholder="اكتبِ اسمك هنا...", required=True)
    g_age = discord.ui.TextInput(label="كم عمرك؟", placeholder="اكتبِ عمرك هنا...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        details = f"• **الاسم:** {self.g_name.value}\n• **العمر:** {self.g_age.value}"
        await send_request_to_admin(interaction, "توثيق بنات", details)

class RoleRequestModal(discord.ui.Modal, title="طلب رتبة جديدة"):
    ro_name = discord.ui.TextInput(label="اسم الرتبة المطلوبة", placeholder="اكتب اسم الرتبة هنا...", required=True)
    ro_color = discord.ui.TextInput(label="لون الرتبة", placeholder="أزرق، أحمر، أو كود اللون...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        details = f"• **اسم الرتبة:** {self.ro_name.value}\n• **اللون المطلوبة:** {self.ro_color.value}"
        await send_request_to_admin(interaction, "طلب رتبة", details)

# --- الدالة المشتركة لإرسال الطلب لروم الإدارة ---
async def send_request_to_admin(interaction: discord.Interaction, req_type: str, details_text: str):
    await interaction.response.defer(ephemeral=True)
    guild, member = interaction.guild, interaction.user
    
    log_channel = guild.get_channel(REQUEST_LOG_CHANNEL_ID)
    if not log_channel:
        await interaction.followup.send("❌ روم استقبال الطلبات غير موجودة!", ephemeral=True)
        return

    admin_embed = discord.Embed(
        title=f"📥 طلب جديد مستلم | {req_type}",
        description=f"👤 **صاحب الطلب:** {member.mention}\n\n📋 **البيانات المستلمة:**\n{details_text}",
        color=discord.Color.orange()
    )
    admin_embed.set_thumbnail(url=member.display_avatar.url)
    
    mentions = f"<@&{ROLE_MANAGER_ID}> <@&{ROLE_ADMIN_ID}>"
    await log_channel.send(content=mentions, embed=admin_embed, view=RequestActionsView(member.id, req_type, details_text))
    await interaction.followup.send("✅ أبشر، تم إرسال طلبك لطاقم الإدارة وبيتواصل البوت معك بالخاص فور المراجعة!", ephemeral=True)

# --- واجهة الأزرار الثلاثة الرئيسية اللوحة ---
class RequestButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="طلب روم", style=discord.ButtonStyle.secondary, custom_id="btn_req_room", emoji="📁")
    async def req_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoomRequestModal())

    @discord.ui.button(label="طلب توثيق بنات", style=discord.ButtonStyle.danger, custom_id="btn_req_girls", emoji="🌸")
    async def req_girls(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GirlsRequestModal())

    @discord.ui.button(label="طلب رتبة", style=discord.ButtonStyle.primary, custom_id="btn_req_role", emoji="🎖️")
    async def req_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleRequestModal())

# --- كلاس الـ Cog الرئيسي لتشغيل النظام ---
class ServerRequestsSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RequestButtonsView())
        self.bot.add_view(RequestActionsView(0, "", ""))

    @app_commands.command(name="setup-requests", description="Sends the official HAVEN server requests panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_requests(self, interaction: discord.Interaction):
        panel_embed = discord.Embed(
            title="✨ طلبات السيرفر ✨",
            description="اطلب وتبشر به\n\nاضغط على الزر المناسب بالأسفل لتقديم طلبك مباشرة إلى الإدارة.",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        panel_embed.set_image(url="https://g.top4top.io/p_3920zv86q1.png") # الرابط الجديد المباشر المرفق
        panel_embed.set_footer(text="إدارة سيرفر HAVEN ترحب بكم •")
        
        await interaction.response.send_message("⌛ جاري إطلاق لوحة طلبات السيرفر...", ephemeral=True)
        await interaction.channel.send(embed=panel_embed, view=RequestButtonsView())

async def setup(bot):
    await bot.add_cog(ServerRequestsSystem(bot))
