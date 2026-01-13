import discord
from discord.ext import commands
import aiohttp
import sqlite3
import re

# --- CONFIGURATION ---
TOKEN = 'YOUR_BOT_TOKEN'
OWNER_ID = 1234567890 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# --- DATABASE EXTENSION ---
def init_db():
    conn = sqlite3.connect('guard_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS permissions (user_id INTEGER PRIMARY KEY, role TEXT)''')
    # Table for locked channels (Announcements/Panels)
    c.execute('''CREATE TABLE IF NOT EXISTS locked_channels (channel_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

# --- CHANNEL LOCK LOGIC ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # Check if the channel is locked (Announcements/Panel)
    conn = sqlite3.connect('guard_bot.db')
    c = conn.cursor()
    c.execute("SELECT channel_id FROM locked_channels WHERE channel_id=?", (message.channel.id,))
    is_locked = c.fetchone()
    conn.close()

    if is_locked and message.author.id != OWNER_ID:
        await message.delete()
        # Optional: Warn the user privately or in chat
        return

    # Process all other Guard Logic (Links, Words, etc.)
    await bot.process_commands(message)

# --- FULL EMBED BUILDER WITH CHANNEL ID ---
@bot.command()
async def embed(ctx):
    """Full Version Builder with Channel Selection"""
    if not is_authorized(ctx.author.id, ['trusted']): return

    def check(m): return m.author == ctx.author and m.channel == ctx.channel

    try:
        await ctx.send("🆔 **Step 1:** Enter the **Channel ID** to send this to (or type 'here' for this channel):")
        target_msg = await bot.wait_for('message', timeout=60.0, check=check)
        
        if target_msg.content.lower() == 'here':
            target_channel = ctx.channel
        else:
            target_channel = bot.get_channel(int(target_msg.content))

        await ctx.send("🎨 **Step 2:** What is the **Title**?")
        title = (await bot.wait_for('message', timeout=60.0, check=check)).content

        await ctx.send("📝 **Step 3:** What is the **Description**?")
        desc = (await bot.wait_for('message', timeout=60.0, check=check)).content

        await ctx.send("🌈 **Step 4:** Hex Color (e.g., `0xff0000`)?")
        color_code = (await bot.wait_for('message', timeout=60.0, check=check)).content
        color = int(color_code, 16) if color_code.startswith('0x') else 0x3498db

        final_embed = discord.Embed(title=title, description=desc, color=color)
        final_embed.set_footer(text=f"Official Announcement • {ctx.guild.name}")

        await target_channel.send(embed=final_embed)
        await ctx.send(f"✅ Announcement sent to {target_channel.mention}!")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# --- LOCK COMMANDS ---

@bot.command()
async def lockchannel(ctx, channel: discord.TextChannel = None):
    """Prevents anyone except the bot/owner from talking in this channel"""
    if ctx.author.id != OWNER_ID: return
    target = channel or ctx.channel
    conn = sqlite3.connect('guard_bot.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO locked_channels (channel_id) VALUES (?)", (target.id,))
    conn.commit()
    conn.close()
    await ctx.send(f"🔒 {target.mention} is now a **Locked Panel**. Only Owner/Bot can post.")

@bot.command()
async def unlockchannel(ctx, channel: discord.TextChannel = None):
    if ctx.author.id != OWNER_ID: return
    target = channel or ctx.channel
    conn = sqlite3.connect('guard_bot.db')
    c = conn.cursor()
    c.execute("DELETE FROM locked_channels WHERE channel_id=?", (target.id,))
    conn.commit()
    conn.close()
    await ctx.send(f"🔓 {target.mention} is now unlocked.")

bot.run(TOKEN)
