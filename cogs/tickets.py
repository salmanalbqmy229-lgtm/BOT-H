import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

# --- إعدادات المعرفات (IDs) لـ HAVEN ---
CATEGORY_ID = 1552708423316152480
PANEL_CHANNEL_ID = 1552708534192308294

# الرتب (Roles) لعمل المنشن داخل التذكرة
ROLE_MANAGER_ID = 1552700984336195614
ROLE_ADMIN_ID = 1552701169611317349
ROLE_TRIAL_ADMIN_ID = 1552701257708347412

# رومات إرسال نسخة التذاكر التلقائية (Logs Channels)
LOG_CHANNEL_1_ID = 1495450684731162664
LOG_CHANNEL_2_ID = 1499889093780312204

DB_PATH = "bot_settings.db"

# --- دالة لحفظ وجلب الأرقام التسلسلية للتذاكر (حفظ دائم) ---
def get_next_ticket_number():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_counter (
            id INTEGER PRIMARY KEY,
            current_number INTEGER
        )
    ''')
    cursor.execute("SELECT current_number FROM ticket_counter WHERE id = 1")
    row = cursor.fetchone()
    if row:
        next_num = row[0] + 1
        cursor.execute("UPDATE ticket_counter SET current_number = ? WHERE id = 1", (next_num,))
    else:
        next_num = 1
        cursor.execute("INSERT INTO ticket_counter (id, current_number) VALUES (1, 1)")
    conn.commit()
    conn.close()
    return next_num

# --- الأزرار التفاعلية داخل التذكرة (استلم / اغلق) ---
class TicketActionsView(discord.ui.View):
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id

    @discord.ui.button(label="استلام التذكرة", style=discord.ButtonStyle.success, custom_id="haven_claim_ticket", emoji="🙋‍♂️")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # التحقق من أن المستخدم إداري (لديه رتبة الإدارة أو الأدمن)
        allowed_roles = [ROLE_MANAGER_ID, ROLE_ADMIN_ID, ROLE_TRIAL_ADMIN_ID]
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(r_id in allowed_roles for r_id in user_role_ids) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ الاستلام مخصص لطاقم إدارة HAVEN فقط يا بعدي!", ephemeral=True)
            return

        button.disabled = True
        button.label = "تم الاستلام"
        button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        
        claim_embed = discord.Embed(
            description=f"💼 تم استلام التذكرة وبدء المتابعة بواسطة الإداري: {interaction.user.mention}",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=claim_embed)

    @discord.ui.button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id="haven_close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        allowed_roles = [ROLE_MANAGER_ID, ROLE_ADMIN_ID, ROLE_TRIAL_ADMIN_ID]
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(r_id in allowed_roles for r_id in user_role_ids) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ الإغلاق مخصص للإدارة فقط!", ephemeral=True)
            return

        await interaction.response.defer()
        
        # تجهيز محتوى الشات لإرسال النسخة التلقائية (Transcript text summary)
        messages_log = []
        async for msg in interaction.channel.history(limit=150, oldest_first=True):
            if not msg.author.bot:
                messages_log.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author.name}: {msg.content}")
        
        chat_history_str = "\n".join(messages_log) if messages_log else "لا توجد رسائل نصية مرسلة من الأعضاء."
        
        # إنشاء ملف نصي يحتوي على المحادثة الكاملة
        import io
        transcript_file = discord.File(
            fp=io.BytesIO(chat_history_str.encode('utf-8')),
            filename=f"transcript-{interaction.channel.name}.txt"
        )
        
        log_embed = discord.Embed(
            title=f"🔒 تم إغلاق التذكرة: {interaction.channel.name}",
            description=f"**بواسطة:** {interaction.user.mention}\n**تاريخ الإغلاق:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            color=discord.Color.red()
        )
        
        # 1. إرسال نسخة تلقائية لصاحب التذكرة في الخاص (DM) مع الملف النصي
        creator = interaction.guild.get_member(self.creator_id)
        if creator:
            try:
                # إرسال الملف النصي للخاص
                transcript_file_dm = discord.File(fp=io.BytesIO(chat_history_str.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
                await creator.send(embed=log_embed, file=transcript_file_dm)
            except Exception:
                pass # إذا كان الخاص مغلقاً يتخطاه

        # 2. إرسال النسخة التلقائية لرومات المراقبة المحددة (الأولى والثانية)
        for log_id in [LOG_CHANNEL_1_ID, LOG_CHANNEL_2_ID]:
            log_channel = interaction.guild.get_channel(log_id)
            if log_channel:
                try:
                    transcript_file_log = discord.File(fp=io.BytesIO(chat_history_str.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
                    await log_channel.send(embed=log_embed, file=transcript_file_log)
                except Exception:
                    pass

        # حذف الروم فوراً
        await interaction.channel.delete()

# --- الاستبيانات والنوافذ المنبثقة (Modals) ---
class MemberReportModal(discord.ui.Modal, title="إبلاغ عن عضو"):
    name_input = discord.ui.TextInput(label="اسم العضو المشكو في حقه", placeholder="اكتب اسمه أو الأي دي الخاص به هنا...", required=True)
    reason_input = discord.ui.TextInput(label="السبب بالتفصيل", style=discord.TextStyle.paragraph, placeholder="وش سوا العضو؟ اكتب السالفة هنا...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "إبلاغ عن عضو", f"**العضو المشتكى عليه:** {self.name_input.value}\n**السبب:** {self.reason_input.value}")

class AdminReportModal(discord.ui.Modal, title="إبلاغ عن إداري"):
    name_input = discord.ui.TextInput(label="اسم الإداري المشكو في حقه", placeholder="اكتب اسمه هنا...", required=True)
    reason_input = discord.ui.TextInput(label="السبب بالتفصيل", style=discord.TextStyle.paragraph, placeholder="وش صار؟ اكتب المشكلة هنا بكل وضوح...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "إبلاغ عن إداري", f"**الإداري المشتكى عليه:** {self.name_input.value}\n**السبب:** {self.reason_input.value}")

class SupportModal(discord.ui.Modal, title="الدعم الفني"):
    problem_input = discord.ui.TextInput(label="وش مشكلتك؟", style=discord.TextStyle.paragraph, placeholder="اكتب مشكلتك هنا وبنساعدك بأقرب وقت...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "الدعم الفني", f"**المشكلة الموضحة:**\n{self.problem_input.value}")

# --- الدالة المشتركة لإنشاء الروم وتوزيع المنشن والإمبيد ---
async def create_ticket_channel(interaction: discord.Interaction, ticket_type: str, details_text: str):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    member = interaction.user
    
    category = guild.get_channel(CATEGORY_ID)
    if not category:
        await interaction.followup.send("❌ كاتجوري التذاكر غير موجود بالسيرفر، تواصل مع الإدارة العليا.", ephemeral=True)
        return

    # جلب الرقم المحفوظ وحساب رقم التذكرة الجديد
    ticket_num = get_next_ticket_number()
    channel_name = f"ticket-{ticket_num}"

    # إعداد الصلاحيات (العضو المستدعي + الإدارة)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    # إضافة صلاحيات رتب الإدارة تلقائياً لرؤية الشات
    for role_id in [ROLE_MANAGER_ID, ROLE_ADMIN_ID, ROLE_TRIAL_ADMIN_ID]:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

    # إنشاء القناة
    ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
    await interaction.followup.send(f"✅ تم فتح تذكرتك بنجاح يا غالي، توجه هنا: {ticket_channel.mention}", ephemeral=True)

    # تجهيز محتوى صياغة المنشن المطلوبة للرتب
    mentions_str = f"{member.mention} | <@&{ROLE_MANAGER_ID}> <@&{ROLE_ADMIN_ID}> <@&{ROLE_TRIAL_ADMIN_ID}>"

    # تصميم الإمبيد الفخم للتذكرة الجديدة
    embed = discord.Embed(
        title=f"🎫 تذكرة جديدة | رقم #{ticket_num}",
        description=(
            f"يا هلا والله ومرحبا بك في قسم الدعم الفني الخاص بـ **HAVEN**.\n\n"
            f"🗂️ **نوع التذكرة:** {ticket_type}\n"
            f"👤 **بواسطة:** {member.mention}\n\n"
            f"📋 **البيانات المستلمة:**\n{details_text}\n\n"
            f"⏳ طاقم الإدارة بيلتفت لك الحين ويعطيك العلم، اركد شوي ومالك إلا طيبة الخاطر.\n"
            f"⚙️ *للإداري المستلم:* يرجى الضغط على زر (استلام التذكرة) قبل البدء."
        ),
        color=discord.Color.from_rgb(45, 45, 45)
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="HAVEN Management System •")

    await ticket_channel.send(content=mentions_str, embed=embed, view=TicketActionsView(member.id))

# --- القائمة المنسدلة (Select Menu) ---
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ابلاغ عن اداري", description="تقديم شكوى مخصصة ضد أحد أفراد الطاقم الإداري", emoji="⚠️"),
