# Fantasy Realm Interactive Prompt Template

## Core Components

### Setting Context
```json
{
  "world_name": "Elaria",
  "player_role": "Young sorcerer named Elowen",
  "setting": "Whispering Woods",
  "time": "Night",
  "atmosphere": "Mystical, enchanted",
  "quest_item": "Luminescent Heart",
  "stakes": "Kingdom in peril, shadows of forgotten evil"
}
```

### Scene Description Template
```
In the ancient land of [world_name], where magic weaves through every living thing, you are [player_role]. The moon hangs low, casting a silver glow over [setting]—a forest known for its luminous flora and elusive creatures.

[Insert relevant lore/background]

As you stand at [current_location], [describe immediate surroundings with sensory details]. You notice:
- [Environmental detail 1]
- [Environmental detail 2]
- [Environmental detail 3]

Available paths:
1. [Path description 1]
2. [Path description 2]
3. [Path description 3]
```

### Narrative Guidelines

#### Tone and Style
- Maintain elegant, high-fantasy language
- Use sensory-rich descriptions
- Balance mystery and clarity
- Keep consistent magical elements

#### Interactive Elements
- Present meaningful choices
- Include environmental interactions
- Allow for spell casting and ability use
- Enable NPC interactions
- Incorporate puzzle-solving opportunities

#### Story Tracking
- Remember player decisions
- Track discovered information
- Note acquired items/abilities
- Monitor relationship changes
- Record quest progress

### Response Framework

#### For Each Player Action
```json
{
  "acknowledge": "Reflect player's choice",
  "describe": "Provide immediate outcome",
  "reveal": "Uncover new information/elements",
  "offer": "Present new choices/opportunities",
  "consequences": "Show impact of decisions"
}
```

## Example Implementation

### Initial Scene
```
In the ancient land of Elaria, where magic weaves through every living thing, you are Elowen, a young sorcerer with untapped potential. The moon hangs low, casting a silver glow over the Whispering Woods—a forest known for its luminous flora and elusive creatures.

Legends speak of the Luminescent Heart, a crystal of immense power hidden deep within the woods. It is said to grant unparalleled abilities to those deemed worthy. The kingdom is in peril as shadows of a forgotten evil begin to stir, and the Luminescent Heart may be the key to restoring balance.

As you stand at the forest's edge, the air is thick with the scent of nocturnal blossoms and the soft hum of ancient magic. Twinkling lights flicker between the trees—whether they are fireflies or sprites, you cannot tell. A narrow path before you splits into three directions:

1. The left path winds towards the sound of flowing water, where a faint glow hints at hidden waterfalls.
2. The center path is overgrown but marked with stones etched with runes, pulsing gently with blue light.
3. The right path descends into a mist-laden hollow, where whispers and giggles echo—a place where the veil between realms is thin.

An old oak tree nearby bears carvings that might be inscriptions or warnings. A cool breeze rustles the leaves, as if urging you to choose.

What do you do?
```

### Example Player Actions
```json
{
  "exploration": [
    "Examine the carvings on the oak tree",
    "Follow any of the three paths",
    "Search the immediate area"
  ],
  "magic": [
    "Cast detection spells",
    "Attempt to communicate with magical beings",
    "Analyze magical auras"
  ],
  "interaction": [
    "Call out to potential nearby creatures",
    "Attempt to decipher runes",
    "Listen for specific sounds"
  ]
}
```

### Fantasy Realm Game State Template

RESPONSE FORMAT:
```json
{
  "scene": {
    "location": {
      "name": "current_location_id",
      "description": "Brief atmospheric description",
      "available_exits": ["exit1", "exit2"],
      "objects": ["interactable1", "interactable2"],
      "npcs": ["npc1", "npc2"]
    },
    "state": {
      "time_of_day": "day/night",
      "weather": "current_weather",
      "events": ["active_event1", "active_event2"],
      "threats": ["threat1", "threat2"]
    }
  },
  "player": {
    "status": {
      "health": "current/max",
      "effects": ["effect1", "effect2"],
      "equipped": {
        "weapon": "item_id",
        "armor": "item_id"
      }
    },
    "inventory": [
      {
        "id": "item_id",
        "quantity": number
      }
    ],
    "active_quests": [
      {
        "id": "quest_id",
        "status": "in_progress/complete",
        "objectives": {
          "objective1": true/false
        }
      }
    ]
  },
  "available_actions": {
    "movement": ["north", "south", "east", "west"],
    "interaction": ["examine X", "talk to Y", "use Z"],
    "combat": ["attack A", "defend against B"],
    "inventory": ["use item", "combine items"]
  }
}
```

INSTRUCTIONS:
1. Always maintain consistent location IDs and item IDs
2. Update state based on time progression and player actions
3. Only show actions that are currently possible
4. Keep descriptions brief but atmospheric
5. Track quest progress and update objectives
6. Maintain threat and event states

EXAMPLE STATE UPDATE:
```json
{
  "state_updates": {
    "location_changed": "new_location_id",
    "inventory_changed": {
      "added": [{"id": "item_id", "quantity": 1}],
      "removed": ["used_item_id"]
    },
    "quest_updated": {
      "quest": "quest_id",
      "objective": "objective_completed"
    }
  }
}