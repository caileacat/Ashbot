import os
import json
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# 🔹 Secrets
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
ASH_BOT_ID = int(os.getenv("ASH_BOT_ID", 0))
CAILEA_ID = os.getenv("CAILEA_ID", "")  # ✅ Keep as string (not int)
LEMON_ID = os.getenv("LEMON_ID", "")  # ✅ Keep as string (not int)
COMMUNITY_SUPPORT_ID = int(os.getenv("COMMUNITY_SUPPORT_ID", 0))

# 🔹 Debugging
DEBUG_FILE = "data/debug.txt"

# 🔹 Weaviate Configuration
WEAVIATE_URL = "http://localhost:8080"
WEAVIATE_CALL_URL = "http://localhost:8080/v1/graphql"
DOCKER_CONTAINER_NAME = "weaviate"
DOCKER_IMAGE = "semitechnologies/weaviate"
DOCKER_PORT = 8080
GRPC_PORT = 50051

# ✅ Load and fix placeholders in `base_data.json`
with open("data/base_data.json", "r", encoding="utf-8") as file:
    data = file.read()

# ✅ Replace placeholders with actual user IDs **before inserting**
data = data.replace("{{CAILEA_ID}}", CAILEA_ID).replace("{{LEMON_ID}}", LEMON_ID)

# ✅ Convert back to dictionary (preparing for Weaviate insert)
BASE_MEMORIES = json.loads(data)

ASH_EPHEMERAL_MESSAGES = [
    "✨ Stirring the tea leaves... visions forming...",
    "🌿 Packing a fresh bowl of inspiration... hold on...",
    "🍃 Whispering with the dryads... one sec...",
    "🫖 Brewing the perfect response... steeping in magic...",
    "💨 Blowing a puff of wisdom into the ether... gimme a moment!",
    "🔮 Gazing into the scrying pool... answers soon!",
    "🌙 Aligning the cosmic energies... nearly there...",
    "🎭 Summoning a goblin to fetch your answer... they’re easily distracted.",
    "🍄 Consulting the council of talking mushrooms... hang tight!",
    "🔥 Tossing some herbs into the cauldron... results pending!",
    "🌲 Listening to the wind through the trees... your words will echo soon!",
    "💫 Tuning into the astral plane... connection is a bit hazy...",

    # 🌿 More cannabis & mystical entries
    "🌬️ Taking a deep inhale of insight... hold that thought...",
    "💨 Rolling up some wisdom... gotta let it burn just right...",
    "🌿 Sprinkling some enchanted keef on the truth... give it a sec!",
    "🍯 Drizzling a little infused honey into the mix... sweet knowledge incoming!",
    "🔥 Sparking up the good stuff... answers should be rolling in shortly!",
    "🦇 Sending a message with a bat courier... those little guys fly fast!",
    "🎶 Humming a spellbound melody... let the magic settle...",
    "🌌 Charting the stars for celestial guidance... cosmic pings take time!",
    "🕯️ Lighting a candle for clarity... flickering with possibilities!",
    "🦊 Sending a fae fox to retrieve your answer... bribes of berries may be required.",
    "📜 Unrolling a dusty scroll... deciphering ancient fae riddles...",
    "🍷 Pouring a glass of enchanted wine... good things take time to age!",
    "🐉 Negotiating with a tiny dragon... they drive a hard bargain.",
    "🎲 Rolling the bones... fate whispers back in cryptic murmurs...",
    "🧪 Mixing a new potion... results may vary!",
    "🌾 Waiting for the wheat to whisper back... nature takes its time!",
    "💨 Exhaling a ring of truth... let’s see what forms in the smoke...",
    
    # 🍃 More fae & nature-inspired responses
    "🐸 Asking the bog witch... she speaks in riddles, but I'll translate!",
    "🛸 Beaming your request to the outer realms... response ETA unknown.",
    "🎩 Checking under my hat... might be something useful under there!",
    "🫛 Consulting the spirit of the bean plant... patience, mortal!",
    "🎨 Painting your fortune in shades of moonlight... drying now!",
    "⏳ Flipping the hourglass... gotta let the magic flow naturally!",
    "🍪 Leaving an offering of cookies... spirits demand snacks first!",
    "🏹 Shooting an arrow into the fae wilds... let's hope the answer returns!",
    "🌋 Waiting for the volcano spirits to respond... they take their time!",
    "📡 Tuning the crystal radio... static... static... almost there!",
    "🦉 Whispering to an owl... if it hoots twice, your answer is near!",
    "🌞 Catching some solar energy... gotta power up the magic circuits!",

    # 🔥 More cannabis-themed responses
    "🌱 Tending to my herb garden... gotta wait for the good stuff to grow!",
    "💚 Grinding up some knowledge... one sec...",
    "🔥 Hotboxing the astral plane... give me a sec to clear the haze!",
    "🍃 Blowing sacred smoke signals... deciphering now...",
    "🛁 Taking a bubble bath in infused wisdom... soaking up the knowledge!",
    "🌲 Sitting in a circle of talking trees... they take their time to respond.",
    "📬 Sending a letter to the fae post... delivery times may vary!",
    "🌪️ Blowing a cloud of insight your way... should be landing soon!",
    "🌊 Tossing your question into the wishing well... echoes take time!",
    "🎐 Letting the wind chimes sing... answers come on the breeze!",
    "🌙 Asking the moon... she only whispers after dusk!",
    "🦋 Watching for omens in butterfly wings... one just landed—wait, no, false alarm.",
    "📖 Flipping through the Book of Shadows... some pages are stuck together!",
    "⚖️ Weighing your request on the scales of fate... balance must be achieved!",
    "🐚 Listening to a seashell... tides of knowledge rolling in!",
    "🔑 Unlocking the door to forbidden wisdom... creaky doors take effort!",
    
    # 🚀 Cosmic & trippy additions
    "🚀 Launching your question into the great unknown... waiting for a signal!",
    "🌎 Spinning the world backwards... that usually works in the movies!",
    "🌀 Getting lost in a time loop... wait, did I answer this already?",
    "🦜 Teaching a parrot your question... they’ll repeat it back soon!",
    "🔋 Recharging my magical reserves... power levels at 80% and rising!",
    "🧊 Waiting for the enchanted ice to melt... patience is key!",
    "🕵️‍♂️ Consulting the library cat... they only answer when they feel like it.",
    "🚪 Knocking on the door to otherworldly knowledge... let's hope someone answers!",
    "💎 Dropping a crystal into the cauldron... clarity should emerge shortly!",
    "🍄 Taking a trip into the unknown... responses may be extra profound!",
    "🌙 Moonbathing in cosmic knowledge... gotta let it absorb!",
    "🪷 Meditating in the lotus realm... insights should flow soon!",
    "☁️ Watching the clouds... they sometimes whisper secrets!",
    "🍵 Sipping enchanted green tea... let the wisdom steep a little longer!",
    "🔥 Slow-roasting an idea in the cosmic oven... be patient!",
    "🐉 Consulting my tiny dragon friend... they speak in riddles!",
    "🌳 Hugging a wisdom tree... waiting for it to whisper back!"
]
