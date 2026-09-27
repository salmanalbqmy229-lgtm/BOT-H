import sqlite3, discord, random, string
from discord import app_commands
from discord.ext import commands

# --- إعدادات المعرفات (IDs) لـ HAVEN ---
PANEL_CHANNEL_ID = 1552708534192308294
TARGET_SEND_CHANNEL_ID = 1552708739633516554

# الرتب المصرح لها فقط بالقبول والرفض (أونر و كونر)
ALLOWED_APPROVE_ROLES = [1552700483938947072, 1552699892214792256]

# رتب الإدارة التي يتم عمل منشن لها عند وصول طلب جديد للروم
ROLE_MANAGER_ID = 1552700984336195614
ROLE_ADMIN_ID = 1552701169611317349

# رومات إرسال نسخة الطلبات التلقائية
LOG_CHANNELS = [1495450684731162664, 1499889093780312204, 1553771326643380476]

def generate_request_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

class RequestActionsView(discord.ui.View):
    def __init__(self, user_id: int, req_type: str, details: str):
        super().__init__(timeout=None)
        self.user_id, self.req_type, self.details = user_id, req_type, details

    async def check_permission(self, interaction: discord.Interaction):
        # السماح للأونر والكونر أو أي شخص لديه صلاحية Administrator كاملة بالسيرفر
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(r_id in ALLOWED_APPROVE_ROLES for r_id in user_role_ids) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ القبول والرفض مخصص للأونر والكونر فقط يا بعدي!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="قبول الطلب", style=discord.ButtonStyle.success, custom_id="h_acc_req", emoji="✅")
    async def accept(self, interaction: discord.Interaction, b: discord.ui.Button):
        if not await self.check_permission(interaction): return
        await interaction.response.defer()
        
        code = generate_request_code()
        emb = interaction.message.embeds
        emb[0].title = f"✅ تم قبول الطلب [كود: {code}]"
        emb[0].color = discord.Color.green()
        emb[0].add_field(name="💼 المسؤول المستلم:", value=interaction.user.mention, inline=False)
        for child in self.children: child.disabled = True
        await interaction.message.edit(embed=emb[0], view=self)
        
        m = interaction.guild.get_member(self.user_id)
        dm = discord.Embed(title="🎉 طلبك انقبل!", description=f"طلبك لـ (**{self.req_type}**) انقبل!\n🔑 **الكود:** `{code}`\n📌 افتح تكت دعم وصور الكلام هنا.", color=discord.Color.green())
        if m:
            try: await m.send(embed=dm)
            except: pass
        for l_id in LOG_CHANNELS:
            ch = interaction.guild.get_channel(l_id)
            if ch:
                try: await ch.send(embed=dm)
                except: pass

    @discord.ui.button(label="رفض الطلب", style=discord.ButtonStyle.danger, custom_id="h_rej_req", emoji="❌")
    async def reject(self, interaction: discord.Interaction, b: discord.ui.Button):
        if not await self.check_permission(interaction): return
        await interaction.response.defer()
        
        emb = interaction.message.embeds
        emb[0].title = f"❌ تم رفض الطلب | {self.req_type}"
        emb[0].color = discord.Color.red()
        emb[0].add_field(name="👤 المرفوض بواسطة:", value=interaction.user.mention, inline=False)
        for child in self.children: child.disabled = True
        await interaction.message.edit(embed=emb[0], view=self)
        
        m = interaction.guild.get_member(self.user_id)
        dm = discord.Embed(title="⚠️ انرفض طلبك", description=f"نعتذر منك، تم رفض طلبك لـ (**{self.req_type}**).", color=discord.Color.red())
        if m:
            try: await m.send(embed=dm)
            except: pass
        for l_id in LOG_CHANNELS:
            ch = interaction.guild.get_channel(l_id)
            if ch:
                try: await ch.send(embed=dm)
                except: pass

class RoomRequestModal(discord.ui.Modal, title="طلب روم جديد"):
    r_name = discord.ui.TextInput(label="اسم الروم المطلوبة")
    r_type = discord.ui.TextInput(label="صنف الروم (مثال: فويس شات)")
    r_roles = discord.ui.TextInput(label="الرتب المسموح لها دخول الروم")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await send_req_to_admin(interaction, "طلب روم", f"• **الاسم:** {self.r_name.value}\n• **الصنف:** {self.r_type.value}\n• **الرتب:** {self.r_roles.value}")

class GirlsRequestModal(discord.ui.Modal, title="طلب توثيق بنات"):
    g_name = discord.ui.TextInput(label="وش اسمك؟")
    g_age = discord.ui.TextInput(label="كم عمرك؟")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await send_req_to_admin(interaction, "توثيق بنات", f"• **الاسم:** {self.g_name.value}\n• **العمر:** {self.g_age.value}")

class RoleRequestModal(discord.ui.Modal, title="طلب رتبة جديدة"):
    ro_name = discord.ui.TextInput(label="اسم الرتبة المطلوبة")
    ro_color = discord.ui.TextInput(label="لون الرتبة")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await send_req_to_admin(interaction, "طلب رتبة", f"• **الاسم:** {self.ro_name.value}\n• **اللون:** {self.ro_color.value}")

class RequestButtonsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="طلب روم", style=discord.ButtonStyle.secondary, custom_id="br_room", emoji="📁")
    async def req_room(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(RoomRequestModal())
    @discord.ui.button(label="طلب توثيق بنات", style=discord.ButtonStyle.danger, custom_id="br_girls", emoji="🌸")
    async def req_girls(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(GirlsRequestModal())
    @discord.ui.button(label="طلب رتبة", style=discord.ButtonStyle.primary, custom_id="br_role", emoji="🎖️")
    async def req_role(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(RoleRequestModal())

async def send_req_to_admin(interaction, req_type, details_text):
    guild, member = interaction.guild, interaction.user
    ch = guild.get_channel(PANEL_CHANNEL_ID)
    if not ch: return
    adm_emb = discord.Embed(title=f"📥 طلب جديد | {req_type}", description=f"👤 **بواسطة:** {member.mention}\n\n📋 **البيانات:**\n{details_text}", color=discord.Color.orange())
    adm_emb.set_thumbnail(url=member.display_avatar.url)
    await ch.send(content=f"<@&{ROLE_MANAGER_ID}> <@&{ROLE_ADMIN_ID}>", embed=adm_emb, view=RequestActionsView(member.id, req_type, details_text))
    await interaction.followup.send("✅ تم إرسال طلبك للإدارة!", ephemeral=True)

class RequestsSystem(commands.Cog):
    def __init__(self, bot): self.bot = bot
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RequestButtonsView())
        self.bot.add_view(RequestActionsView(0, "", ""))

    @app_commands.command(name="setup-requests", description="Sends requests panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_requests(self, interaction: discord.Interaction):
        p = discord.Embed(title="✨ طلبات السيرفر ✨", description="اطلب وتبشر به\n\nاضغط على الزر المناسب بالأسفل لتقديم طلبك مباشرة إلى الإدارة.", color=0x202020)
        p.set_image(url="https://i.top4top.io/p_3922xxfm21.png")
        await interaction.response.send_message("⌛ جاري الإطلاق...", ephemeral=True)
        ch = self.bot.get_channel(TARGET_SEND_CHANNEL_ID) or interaction.channel
        await ch.send(embed=p, view=RequestButtonsView())

async def setup(bot): await bot.add_cog(RequestsSystem(bot))
