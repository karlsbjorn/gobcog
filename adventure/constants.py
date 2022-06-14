from enum import Enum


class Skills(Enum):
    attack = "attack"
    charisma = "charisma"
    intelligence = "intelligence"
    reset = "reset"


class Rarities(Enum):
    normal = "normal"
    rare = "rare"
    epic = "epic"
    legendary = "legendary"
    ascended = "ascended"
    set = "set"
    event = "event"
    forged = "forged"


class Slots(Enum):
    head = "head"
    neck = "neck"
    chest = "chest"
    gloves = "gloves"
    belt = "belt"
    legs = "legs"
    boots = "boots"
    left = "left"
    right = "right"
    two_handed = "two handed"
    ring = "ring"
    charm = "charm"


class HeroClasses(Enum):
    wizard = "wizard"
    tinkerer = "tinkerer"
    berserker = "berserker"
    cleric = "cleric"
    ranger = "ranger"
    bard = "bard"
    psychic = "psychic"

DEV_LIST = (208903205982044161, 154497072148643840, 218773382617890828, 87446677010550784)

ORDER = [
    "head",
    "neck",
    "chest",
    "gloves",
    "belt",
    "legs",
    "boots",
    "left",
    "right",
    "two handed",
    "ring",
    "charm",
]
TINKER_OPEN = r"{.:'"
TINKER_CLOSE = r"':.}"
LEGENDARY_OPEN = r"{Legendary:'"
ASC_OPEN = r"{Ascended:'"
LEGENDARY_CLOSE = r"'}"
SET_OPEN = r"{Set:'"
EVENT_OPEN = r"{Event:'"
RARITIES = ("normal", "rare", "epic", "legendary", "ascended", "set", "event", "forged")
REBIRTH_LVL = 20
REBIRTH_STEP = 10
