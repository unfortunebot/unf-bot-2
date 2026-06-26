import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from datetime import datetime

# =========================
# AYARLAR
# =========================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN bulunamadı.")

RULES_TEXT = (
    "• POV almak kesinlikle zorunludur.\n"
    "• No Stamina, No Bush, No Prop gibi avantaj sağlayacak şeyler yasaktır.\n"
    "• Bilgisayarınızda hile / mod kalıntısı bulunmamalıdır.\n"
    "• Şüpheli durumlarda yönetim manuel kontrol yapabilir."
)

DEFAULT_BANNER = "https://cdn.discordapp.com/attachments/1519426746041110791/1520049279773708429/unfortune_banner.webp?ex=6a3fc7b5&is=6a3e7635&hm=b53cf06e93b1e09e883a83ca6693e42b8899374ff2fdd736bc5b6108f2ec8150&"

DEFAULT_THUMBNAIL = "https://cdn.discordapp.com/attachments/1519426746041110791/1520049279408799816/unfortune_pp.jpg?ex=6a3fc7b5&is=6a3e7635&hm=f4bf8c5f49ade1920e77bb30adf31841fb5478e0df89dcfe9eecc8c8d94fe542&"

# =========================
# BOT
# =========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

EVENT_FILE = "events.json"

def load_events():
    if os.path.exists(EVENT_FILE):
        try:
            with open(EVENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception:
            return {}
    return {}

def save_events():
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

events = load_events()

# =========================
# SAAT KONTROL
# =========================

def event_closed(event):

    now = datetime.now()

    try:
        event_time = datetime.strptime(
            event["event_time"],
            "%H:%M"
        ).time()

        return now.time() >= event_time

    except Exception:
        return False

# =========================
# EMBED GÜNCELLE
# =========================

async def update_embed(interaction, event_id):

    event = events[event_id]

    current = len(event["participants"])
    required = event["required"]

    percent = int((current / required) * 100) if required > 0 else 0

    embed = discord.Embed(
        title=f"🎯 {event['title']}",
        description=(
            f"```{event['description']}```\n\n"
            f"🕒 **ETKİNLİK SAATİ:** {event['event_time']}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📜 **KATILIM ŞARTLARI**\n"
            f"{RULES_TEXT}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 **GEREKLİ KİŞİ:** {required}\n"
            f"✅ **KATILAN:** {current}/{required}\n"
            f"📊 **DOLULUK:** %{percent}\n"
            f"❌ **SON AYRILAN:** {event['last_left']}\n"
        ),
        color=0x2ecc71
    )

    embed.set_footer(text="UNFORTUNE EVENT SYSTEM")
    embed.set_thumbnail(url=DEFAULT_THUMBNAIL)
    embed.set_image(url=DEFAULT_BANNER)

    await interaction.response.edit_message(
        embed=embed,
        view=EventView(event_id)
    )

# =========================
# BUTONLAR
# =========================

class EventView(discord.ui.View):

    def __init__(self, event_id):
        super().__init__(timeout=None)
        self.event_id = event_id

    @discord.ui.button(
        label="Katıl",
        emoji="✅",
        style=discord.ButtonStyle.green
    )
    async def join_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        event = events[self.event_id]

        if event_closed(event):
            await interaction.response.send_message(
                "⛔ Etkinlik saati geçti. Katılım kapatılmıştır.",
                ephemeral=True
            )
            return

        if interaction.user.id in event["participants"]:
            await interaction.response.send_message(
                "Zaten etkinliğe katıldın.",
                ephemeral=True
            )
            return

        event["participants"].append(interaction.user.id)
        save_events()
        save_events()

        await update_embed(
            interaction,
            self.event_id
        )

    @discord.ui.button(
        label="Ayrıl",
        emoji="❌",
        style=discord.ButtonStyle.red
    )
    async def leave_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        event = events[self.event_id]

        if event_closed(event):
            await interaction.response.send_message(
                "⛔ Etkinlik başlamıştır. Ayrılma işlemi kapatılmıştır.",
                ephemeral=True
            )
            return

        if interaction.user.id not in event["participants"]:
            await interaction.response.send_message(
                "Etkinliğe katılmamışsın.",
                ephemeral=True
            )
            return

        event["participants"].remove(interaction.user.id)

        event["last_left"] = interaction.user.name
        save_events()
        save_events()

        await update_embed(
            interaction,
            self.event_id
        )

    @discord.ui.button(
        label="Katılımcılar",
        emoji="👥",
        style=discord.ButtonStyle.blurple
    )
    async def participants_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        event = events[self.event_id]

        if len(event["participants"]) == 0:
            await interaction.response.send_message(
                "Katılımcı bulunmuyor.",
                ephemeral=True
            )
            return

        liste = "\n".join(
            f"{i+1}. 👤 <@{uid}> | 🆔 {uid}"
            for i, uid in enumerate(event["participants"])
        )

        await interaction.response.send_message(
            f"📋 **CASTELLANO KATILIMCI LİSTESİ**\n\n{liste}",
            ephemeral=True
        )

# =========================
# ETKİNLİK OLUŞTUR
# =========================

@bot.tree.command(
    name="etkinlik_olustur",
    description="Yeni etkinlik oluştur."
)
@app_commands.describe(
    baslik="Etkinlik başlığı",
    aciklama="Etkinlik açıklaması",
    gerekli_kisi="Gerekli kişi sayısı",
    saat="Etkinlik saati (Örn: 21:45)"
)
async def etkinlik_olustur(
    interaction: discord.Interaction,
    baslik: str,
    aciklama: str,
    gerekli_kisi: int,
    saat: str
):

    ALLOWED_ROLE_IDS = [
        1514176560347742258
    ]

    user_role_ids = [role.id for role in interaction.user.roles]

    if not any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids):
        await interaction.response.send_message(
            "❌ Bu komutu kullanmak için yetkin yok.",
            ephemeral=True
        )
        return

    event_id = len(events) + 1

    events[event_id] = {
        "title": baslik,
        "description": aciklama,
        "required": gerekli_kisi,
        "participants": [],
        "last_left": "Yok",
        "event_time": saat
    }

    save_events()

    save_events()

    embed = discord.Embed(
        title=f"🎯 {baslik}",
        description=(
            f"```{aciklama}```\n\n"
            f"🕒 **ETKİNLİK SAATİ:** {saat}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📜 **KATILIM ŞARTLARI**\n"
            f"{RULES_TEXT}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 **GEREKLİ KİŞİ:** {gerekli_kisi}\n"
            f"✅ **KATILAN:** 0/{gerekli_kisi}\n"
            f"📊 **DOLULUK:** %0\n"
            f"❌ **SON AYRILAN:** Yok\n"
        ),
        color=0x2ecc71
    )

    embed.set_footer(text="UNFORTUNE EVENT SYSTEM")
    embed.set_thumbnail(url=DEFAULT_THUMBNAIL)
    embed.set_image(url=DEFAULT_BANNER)

    await interaction.response.send_message(
        content=f"@everyone\n🆔 Etkinlik ID: `{event_id}`",
        embed=embed,
        view=EventView(event_id),
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )

# =========================
# KATILIMCILAR
# =========================

@bot.tree.command(
    name="katilimcilar",
    description="Son etkinliğin katılımcılarını göster."
)
@app_commands.default_permissions(administrator=True)
async def katilimcilar(
    interaction: discord.Interaction
):

    if len(events) == 0:
        await interaction.response.send_message(
            "Aktif etkinlik bulunmuyor.",
            ephemeral=True
        )
        return

    last_event = list(events.values())[-1]

    if len(last_event["participants"]) == 0:
        await interaction.response.send_message(
            "Katılımcı bulunmuyor.",
            ephemeral=True
        )
        return

    liste = "\n".join(
        f"{i+1}. 👤 <@{uid}> | 🆔 {uid}"
        for i, uid in enumerate(last_event["participants"])
    )

    await interaction.response.send_message(
        f"📋 **CASTELLANO KATILIMCI LİSTESİ**\n\n{liste}",
        ephemeral=True
    )

# =========================
# ETKİNLİK SİL
# =========================

@bot.tree.command(
    name="etkinlik_sil",
    description="Etkinliği sil"
)
@app_commands.default_permissions(administrator=True)
async def etkinlik_sil(
    interaction: discord.Interaction,
    event_id: str
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Bu komutu yalnızca yöneticiler kullanabilir.",
            ephemeral=True
        )
        return

    try:
        eid = int(event_id)

        if eid not in events:
            await interaction.response.send_message(
                "Etkinlik bulunamadı.",
                ephemeral=True
            )
            return

        del events[eid]
        save_events()
        save_events()

        await interaction.response.send_message(
            "✅ Etkinlik başarıyla silindi."
        )

    except Exception:
        await interaction.response.send_message(
            "Geçersiz etkinlik ID.",
            ephemeral=True
        )


# =========================
# SES KOMUTLARI
# =========================

@bot.tree.command(name="sesegir", description="Bulunduğun ses kanalına girer.")
async def sesegir(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message("Önce bir ses kanalına gir.", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.response.send_message("Zaten bir ses kanalındayım.", ephemeral=True)
        return
    await channel.connect()
    await interaction.response.send_message(f"🔊 {channel.name} kanalına girdim.")

@bot.tree.command(name="sescik", description="Ses kanalından çıkar.")
@app_commands.default_permissions(administrator=True)
async def sescik(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("Bir ses kanalında değilim.", ephemeral=True)
        return
    await vc.disconnect()
    await interaction.response.send_message("🔇 Ses kanalından ayrıldım.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    vc = discord.utils.get(bot.voice_clients, guild=member.guild)
    if vc and len(vc.channel.members) == 1:
        pass


# =========================
# BOT HAZIR
# =========================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print("=" * 50)
    print(f"{bot.user} aktif.")
    print("CASTELLANO EVENT BOT HAZIR")
    print("=" * 50)

# =========================
# ÇALIŞTIR
# =========================

keep_alive()

try:
    bot.run(TOKEN)
except Exception as e:
    print("BOT KAPANDI:", e)
    time.sleep(5)