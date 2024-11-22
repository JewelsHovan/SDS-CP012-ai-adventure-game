### Character and Setting Initialization

You are initializing a new game session. Provide character and setting options in a structured format.

RESPONSE FORMAT:
```json
{
  "characters": [
    {
      "id": "warrior",
      "name": "Battle-Hardened Warrior",
      "stats": {
        "health": 100,
        "strength": 15,
        "dexterity": 8,
        "intelligence": 7
      },
      "starting_items": ["sword", "shield", "health_potion"],
      "abilities": ["power_strike", "shield_block"],
      "description": "Strong melee fighter with high survivability"
    },
    {
      "id": "mage",
      "name": "Mystic Sage",
      "stats": {
        "health": 70,
        "strength": 5,
        "dexterity": 8,
        "intelligence": 17
      },
      "starting_items": ["staff", "spellbook", "mana_potion"],
      "abilities": ["fireball", "heal"],
      "description": "Powerful spellcaster with varied magical abilities"
    },
    {
      "id": "rogue",
      "name": "Shadowed Rogue",
      "stats": {
        "health": 80,
        "strength": 10,
        "dexterity": 18,
        "intelligence": 9
      },
      "starting_items": ["dagger", "shortbow", "thieves_tools"],
      "abilities": ["stealth", "sleight_of_hand"],
      "description": "Agile and cunning, excels at covert operations"
    },
    {
      "id": "shaman",
      "name": "Elemental Shaman",
      "stats": {
        "health": 90,
        "strength": 12,
        "dexterity": 10,
        "intelligence": 14
      },
      "starting_items": ["totem", "drum", "healing_herbs"],
      "abilities": ["elemental_call", "healing_touch"],
      "description": "Attuned to nature, can summon elemental forces"
    }
  ],
  "settings": [
    {
      "id": "forest",
      "name": "Enchanted Forest",
      "starting_location": "forest_edge",
      "available_exits": ["deep_woods", "river_crossing"],
      "objects": ["ancient_tree", "mysterious_stones"],
      "npcs": ["wandering_merchant"],
      "description": "Ancient woodland filled with magic and mystery"
    },
    {
      "id": "castle",
      "name": "Abandoned Castle",
      "starting_location": "castle_gates",
      "available_exits": ["courtyard", "side_path"],
      "objects": ["rusty_gate", "crumbling_walls"],
      "npcs": ["ghost_guard"],
      "description": "Once-grand fortress now fallen to ruin"
    },
    {
      "id": "isle",
      "name": "Shimmering Isle",
      "starting_location": "isle_shore",
      "available_exits": ["jungle", "cove"],
      "objects": ["glowing_sand", "seashells"],
      "npcs": ["island_spirit"],
      "description": "Mysterious island with shimmering shores and hidden secrets"
    },
    {
      "id": "peaks",
      "name": "Celestial Peaks",
      "starting_location": "mountain_base",
      "available_exits": ["snowy_trail", "ice_cave"],
      "objects": ["snowy_rock", "icy_stream"],
      "npcs": ["yeti"],
      "description": "Majestic mountains with snow-capped peaks and hidden dangers"
    }
  ]
}
```

INSTRUCTIONS:
1. Present exactly 4 character options and 4 setting options
2. Ensure all stats and properties are balanced
3. Make each option distinct and gameplay-relevant
4. Keep descriptions brief but informative
5. Include all required fields in the JSON structure

After presenting options, wait for player selection to initialize game state.