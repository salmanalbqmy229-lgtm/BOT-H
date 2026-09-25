import discord
from discord import app_commands
from discord.ext import commands

# Persistent View for the Rules Button
class RulesView(discord.ui.View):
    def __init__(self):
        # timeout=None makes the button persistent (works forever even if bot restarts)
        super().__init__(timeout=None)

    # The interaction button for reading rules
    @discord.ui.button(
        label="قراءة القوانين", 
        style=discord.ButtonStyle.secondary, 
        custom_id="haven_rules_button",
        emoji="📜"
    )
    async def read_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Creating a luxurious embed for the detailed rules in Saudi dialect
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
                "التاغات الزايدة بدون سنع، وتكرار الكلام اللي يوجع الرأس بالشات (الإسبام) ممنوع. خلو الشات نظيف.\n\n"
                "**4️⃣ | المحتوى الحساس:**\n"
                "السيرفر مكان نظيف للجميع؛ يمنع منعاً باتاً نشر صور، مقاطع، أو نقاشات سياسية، دينية، أو غير لائقة.\n\n"
                "**5️⃣ | الإعلانات والخاص:**\n"
                "ممنوع تنشر روابط سيرفرات ثانية أو تسوق لنفسك بالعام أو تروح للأعضاء خاص وتزعجهم بإعلاناتك.\n\n"
                "**6️⃣ | سماع توجيهات الإدارة:**\n"
                "إذا كلمك أحد من طاقم الإدارة أو المشرفين، اسمع منه وامشِ بالحق. تراهم موجودين لخدمتكم وراحتكم.\n\n"
                "✨ *التزامك بالقوانين يعكس تربيتك وأخلاقك العالية. منورنا يا بعدي وقتاً ممتعاً!*"
            ),
            color=discord.Color.from_rgb(47, 49, 54) # Dark elegant background look
        )
        # Display the member's profile picture as a thumbnail in the corner
        rules_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        rules_embed.set_footer(text="إدارة سيرفر HAVEN تتمنى لكم أسعد الأوقات •")

        # Send the embed dynamically and privately only to the user who clicked the button
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)


class RulesPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Trigger when the cog is fully loaded to register the persistent button structure
    @commands.Cog.listener()
    async def on_ready(self):
        # Tells the bot to listen to this custom_id even after code reboot
        self.bot.add_view(RulesView())

    # Slash command to drop the rules panel in a designated server channel
    @app_commands.command(name="send-rules", description="Sends the official HAVEN server rules panel")
    @app_commands.checks.has_permissions(administrator=True) # Protected command for admins only
    async def send_rules(self, interaction: discord.Interaction):
        # Initial message layout configuration setup
        panel_embed = discord.Embed(
            title="✨ القوانين ✨",
            description="قوانين السيرفر الخاص بـ **HAVEN**\nاضغط على الزر بالأسفل لقراءة القوانين والشروط وتجنب العقوبات.",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        # Setting up your exact requested remote image view layer URL
        panel_embed.set_image(url="https://top4top.io")
        
        # Responding publicly in the channel with the full panel and interactive view
        await interaction.response.send_message("⌛ Processing rules panel setup...", ephemeral=True)
        await interaction.channel.send(embed=panel_embed, view=RulesView())

async def setup(bot):
    await bot.add_cog(RulesPanel(bot))
