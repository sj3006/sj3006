"""The 20 pen colours and their codes.

The order follows the pen tray photo, top to bottom. The code printed on each
pen cap could not be read from the photo, so the CODE column is a best guess.
If your pens are labelled differently, just change the code letters here
(each code must be used exactly once).
"""

# (code, name, hex) — hex values are approximations of the pen ink
PENS = [
    ("1", "Black",        "#1c1c1c"),
    ("2", "Slate Grey",   "#4d5d60"),
    ("3", "Brown",        "#6e3f2c"),
    ("4", "Deep Purple",  "#4a2a7c"),
    ("5", "Purple",       "#8a3fa6"),
    ("6", "Violet",       "#5b4cc0"),
    ("7", "Lavender",     "#c7a8e6"),
    ("8", "Navy Blue",    "#1f3c9e"),
    ("9", "Blue",         "#1f74d6"),
    ("0", "Turquoise",    "#22aec6"),
    ("A", "Aqua",         "#93dbe0"),
    ("B", "Sky Blue",     "#5cbdea"),
    ("C", "Teal Green",   "#1d7a5f"),
    ("D", "Green",        "#3dbb6b"),
    ("E", "Mint",         "#97e2b4"),
    ("F", "Mustard",      "#e9a92f"),
    ("G", "Lemon",        "#f6e173"),
    ("H", "Orange",       "#f17a2f"),
    ("I", "Peach",        "#f6a98f"),
    ("J", "Red",          "#d42b2b"),
]

CODES = [p[0] for p in PENS]
NAMES = {p[0]: p[1] for p in PENS}
HEX = {p[0]: p[2] for p in PENS}
assert len(set(CODES)) == 20

# Colour schemes that look good together. Patterns pick one of these,
# so every page has a harmonious 5–9 colour set rather than random pens.
SCHEMES = {
    "ocean":    ["8", "9", "B", "0", "A", "C", "E"],
    "sunset":   ["4", "5", "J", "H", "F", "G", "I"],
    "forest":   ["3", "C", "D", "E", "G", "F"],
    "berry":    ["4", "5", "6", "7", "J", "I"],
    "rainbow":  ["J", "H", "F", "G", "D", "0", "9", "6", "5"],
    "earth":    ["3", "H", "F", "I", "G", "C"],
    "cool":     ["4", "6", "7", "8", "9", "B", "A"],
    "candy":    ["5", "I", "7", "A", "E", "G"],
    "fire":     ["3", "J", "H", "F", "G"],
    "peacock":  ["4", "8", "0", "C", "D", "F"],
    "dusk":     ["2", "4", "6", "7", "I", "H"],
    "tropical": ["J", "H", "G", "D", "0", "9"],
}
