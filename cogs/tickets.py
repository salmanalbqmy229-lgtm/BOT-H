import sqlite3, discord, io
from discord import app_commands
from discord.ext import commands
from datetime import datetime

# --- إعدادات المعرفات (IDs) لـ HAVEN ---
CATEGORY_ID = 1552708423316152480
PANEL_CHANNEL_ID = 1552708534192308294
ROLE_MANAGER_ID = 1552700984336195614
ROLE_ADMIN_ID = 1552701169611317349
ROLE_TRIAL_ADMIN_ID = 1552701257708347412
LOG_1, LOG_2 = 1495450684731162664, 1499889093780312204
DB_PATH = "bot_settings.db"

def get_next_ticket_number():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS ticket_counter (id INTEGER PRIMARY KEY, current_number INTEGER)')
    cursor.execute("SELECT current_number FROM ticket_counter WHERE id = 1")
    row = cursor.fetchone()
    if row:
        next_num = row[0] + 1
        cursor.execute("UPDATE ticket_counter SET current_number = ? WHERE id = 1", (next_num,))
    else:
        next_num = 1
        cursor.execute("INSERT INTO ticket_counter (id, current_number) VALUES (1, 1)")
    conn.commit(); conn.close()
    return next_num

async def create_ticket_channel(interaction, ticket_type, details_text):
    guild, member = interaction.guild, interaction.user
    category = guild.get_channel(CATEGORY_ID)
    if not category: return
    
    ticket_num = get_next_ticket_number()
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    for r_id in [ROLE_MANAGER_ID, ROLE_ADMIN_ID, ROLE_TRIAL_ADMIN_ID]:
        role = guild.get_role(r_id)
        if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

    ticket_channel = await guild.create_text_channel(name=f"ticket-{ticket_num}", category=category, overwrites=overwrites)
    await interaction.followup.send(f"✅ تم فتح تذكرتك: {ticket_channel.mention}", ephemeral=True)

    embed = discord.Embed(
        title=f"🎫 تذكرة جديدة | رقم #{ticket_num}",
        description=f"🗂️ **القسم:** {ticket_type}\n👤 **بواسطة:** {member.mention}\n\n📋 **البيانات:**\n{details_text}\n\n⏳ الإدارة بتجيك الحين، اركد شوي ومالك إلا طيبة الخاطر.",
        color=discord.Color.from_rgb(45, 45, 45)
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    mentions = f"{member.mention} | <@&{ROLE_MANAGER_ID}> <@&{ROLE_ADMIN_ID}> <@&{ROLE_TRIAL_ADMIN_ID}>"
    await ticket_channel.send(content=mentions, embed=embed, view=TicketActionsView(member.id))

class TicketActionsView(discord.ui.View):
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id

    @discord.ui.button(label="استلام التذكرة", style=discord.ButtonStyle.success, custom_id="haven_claim_ticket", emoji="🙋‍♂️")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        allowed = [ROLE_MANAGER_ID, ROLE_ADMIN_ID, ROLE_TRIAL_ADMIN_ID]
        if not any(r.id in allowed for r in interaction.user.roles) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ الاستلام مخصص لطاقم إدارة HAVEN!", ephemeral=True); return
        button.disabled, button.label, button.style = True, "تم الاستلام", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 تم استلام التذكرة بواسطة: {interaction.user.mention}", color=discord.Color.blue()))

    @discord.ui.button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id="haven_close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        allowed = [ROLE_MANAGER_ID, ROLE_ADMIN_ID, ROLE_TRIAL_ADMIN_ID]
        if not any(r.id in allowed for r in interaction.user.roles) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ الإغلاق مخصص للإدارة فقط!", ephemeral=True); return
        await interaction.response.defer()
        
        log = []
        async for m in interaction.channel.history(limit=150, oldest_first=True):
            if not m.author.bot: log.append(f"[{m.created_at.strftime('%m-%d %H:%M')}] {m.author.name}: {m.content}")
        chat_str = "\n".join(log) if log else "لا توجد رسائل."
        
        log_embed = discord.Embed(title=f"🔒 إغلاق تذكرة: {interaction.channel.name}", description=f"**بواسطة:** {interaction.user.mention}\n**التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}", color=discord.Color.red())
        
        creator = interaction.guild.get_member(self.creator_id)
        if creator:
            try: await creator.send(embed=log_embed, file=discord.File(fp=io.BytesIO(chat_str.encode('utf-8')), filename="transcript.txt"))
            except: pass
        for l_id in [LOG_1, LOG_2]:
            ch = interaction.guild.get_channel(l_id)
            if ch:
                try: await ch.send(embed=log_embed, file=discord.File(fp=io.BytesIO(chat_str.encode('utf-8')), filename="transcript.txt"))
                except: pass
        await interaction.channel.delete()

class MemberReportModal(discord.ui.Modal, title="إبلاغ عن عضو"):
    name_input = discord.ui.TextInput(label="اسم العضو المشكو في حقه", placeholder="اكتب اسمه هنا...", required=True)
    reason_input = discord.ui.TextInput(label="السبب بالتفصيل", style=discord.TextStyle.paragraph, placeholder="وش سوا؟ اكتب السالفة هنا...", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await create_ticket_channel(interaction, "إبلاغ عن عضو", f"**المشتكى عليه:** {self.name_input.value}\n**السبب:** {self.reason_input.value}")

class AdminReportModal(discord.ui.Modal, title="إبلاغ عن إداري"):
    name_input = discord.ui.TextInput(label="اسم الإداري المشكو في حقه", placeholder="اكتب اسمه هنا...", required=True)
    reason_input = discord.ui.TextInput(label="السبب بالتفصيل", style=discord.TextStyle.paragraph, placeholder="وش صار؟ اكتب المشكلة هنا...", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await create_ticket_channel(interaction, "إبلاغ عن إداري", f"**المشتكى عليه:** {self.name_input.value}\n**السبب:** {self.reason_input.value}")

class SupportModal(discord.ui.Modal, title="الدعم الفني"):
    problem_input = discord.ui.TextInput(label="وش مشكلتك؟", style=discord.TextStyle.paragraph, placeholder="اكتب مشكلتك هنا وبنساعدك...", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await create_ticket_channel(interaction, "الدعم الفني", f"**المشكلة:**\n{self.problem_input.value}")

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ابلاغ عن اداري", description="تقديم شكوى ضد أحد أفراد الطاقم الإداري", emoji="⚠️"),
            discord.SelectOption(label="ابلاغ عن عضو", description="الإبلاغ عن مخالفة من عضو", emoji="👤"),
            discord.SelectOption(label="الدعم الفني", description="مشكلة تقنية أو طلب مساعدة عامة", emoji="🛠️"),
            discord.SelectOption(label="استفسار", description="استفسار سريع - يفتح تذكرة مباشرة بدون استبيان", emoji="❓")
        ]
        super().__init__(placeholder="اضغط هنا واختر نوع التذكرة المناسبة لك...", min_values=1, max_values=1, options=options, custom_id="haven_ticket_select")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "ابلاغ عن اداري": await interaction.response.send_modal(AdminReportModal())
        elif self.values[0] == "ابلاغ عن عضو": await interaction.response.send_modal(MemberReportModal())
        elif self.values[0] == "الدعم الفني": await interaction.response.send_modal(SupportModal())
        elif self.values[0] == "استفسار":
            await interaction.response.defer(ephemeral=True)
            await create_ticket_channel(interaction, "استفسار", "طلب استفسار عام وسريع.")

class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class TicketsSystem(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketDropdownView())
        self.bot.add_view(TicketActionsView(0))

    @app_commands.command(name="setup-ticket", description="Sends the HAVEN ticket creation menu")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        panel_embed = discord.Embed(
            title="⚙️ الدعم الفني",
            description="حياك الله في قسم الدعم لـ **HAVEN**.\nعشان تفتح تذكرة، اختر القسم المناسب لمشكلتك من **القائمة بالأسفل**.",
            color=discord.Color.from_rgb(25, 25, 25)
        )
        panel_embed.set_image(url="https://top4top.io")
        panel_embed.set_footer(text="إدارة سيرفر HAVEN ترحب بكم •")
        await interaction.response.send_message("⌛ جاري التثبيت...", ephemeral=True)
        channel = self.bot.get_channel(PANEL_CHANNEL_ID) or interaction.channel
        await channel.send(embed=panel_embed, view=TicketDropdownView())

async def setup(bot): await bot.add_cog(TicketsSystem(bot))
