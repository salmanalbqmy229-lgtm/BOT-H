import discord
from discord import app_commands
from discord.ext import commands

class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="قراءة القوانين", style=discord.ButtonStyle.secondary, custom_id="haven_rules_button", emoji="📜")
    async def read_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        rules_embed = discord.Embed(
            title="📜 قوانين وشروط سيرفر HAVEN",
            description=(
                "يا هلا ويا مرحبا فيكم في **HAVEN**! عشان نضمن بيئة ممتعة ومحترمة للجميع، "
                "الله لا يهينكم اركدو واقرو القوانين هذي وامشوا عليها:\n\n"
                "**1️⃣ | الاحترام المتبادل:**\n"
                "خلك سمح واحترم الكل. الطقطقة الزايدة، السب، وقذف خلق الله هذي ما نمشيها هنا أبد وعاقبتها وخيمة.\n\n"
                "**2️⃣ | الخصوصية خط أحمر:**\n"
                "صور الناس، أرقامهم، أو معلوماتهم الشخصية لا تنشرها. خلك في حالك واحترم خصوصية غيرك.\n\n"
                "**3️⃣ | التخريب والـ Spam:**\n"
                "التاغات الزايدة بدون سنع، وتكرار الكلام بالشات (الإسبام) ممنوع. خلو الشات نظيف.\n\n"
                "**4️⃣ | المحتوى الحساس:**\n"
                "السيرفر مكان نظيف للجميع؛ يمنع منعاً باتاً نشر صور، مقاطع، أو نقاشات سياسية، دينية، أو غير لائقة.\n\n"
                "**5️⃣ | الإعلانات والخاص:**\n"
                "ممنوع تنشر روابط سيرفرات ثانية أو تروح للأعضاء خاص وتزعجهم بإعلاناتك.\n\n"
                "**6️⃣ | سماع توجيهات الإدارة:**\n"
                "إذا كلمك أحد من طاقم الإدارة أو المشرفين، اسمع منه وامشِ بالحق. تراهم موجودين لخدمتكم وراحتكم.\n\n"
                "✨ *التزامك بالقوانين يعكس تربيتك وأخلاقك العالية. منورنا يا بعدي وقتاً ممتعاً!*"
            ),
            color=discord.Color.from_rgb(47, 49, 54)
        )
        rules_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        rules_embed.set_footer(text="إدارة سيرفر HAVEN تتمنى لكم أسعد الأوقات •")
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

class RulesPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RulesView())

    @app_commands.command(name="send-rules", description="Sends the official HAVEN server rules panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def send_rules(self, interaction: discord.Interaction):
        panel_embed = discord.Embed(
            title="✨ القوانين ✨",
            description="قوانين السيرفر الخاص بـ **HAVEN**\nاضغط على الزر بالأسفل لقراءة القوانين والشروط وتجنب العقوبات.",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        panel_embed.set_image(url="https://top4top.io")
        
        await interaction.response.send_message("⌛ جاري إعداد لوحة القوانين بالصورة الجديدة...", ephemeral=True)
        await interaction.channel.send(embed=panel_embed, view=RulesView())

async def setup(bot):
    await bot.add_cog(RulesPanel(bot))
