#!/usr/bin/env python3
"""
Describe the window-style and finish matrix used by the prototype.
"""

WINDOW_TYPES = {
    "awning": ("Awning Windows", "Hinged at the top, opening outward."),
    "bay": ("Bay Windows", "Three windows at varying angles."),
    "bow": ("Bow Windows", "Four or more windows in a gentle curve."),
    "casement": ("Casement Windows", "Hinged at the sides, opening outward."),
    "double_hung": ("Double-Hung Windows", "Two sashes that slide vertically."),
    "garden": ("Garden Windows", "Extend outward with a deep greenhouse sill."),
    "hopper": ("Hopper Windows", "Hinge at the bottom, opening inward."),
    "picture": ("Picture Windows", "Grand seamless unobstructed panoramic pane."),
    "sliding": ("Sliding Windows", "Glide horizontally with ease."),
    "specialty": ("Specialty Windows", "Unique architectural designs from arches to geometric shapes.")
}

FINISH_CATALOG = {
    "Golden Oak": "#AC7E5B",
    "Natural Pine / Birch": "#D4AF76",
    "Walnut": "#593C27",
    "Espresso / Dark Ebony": "#2C221C",
    "Mahogany": "#672420",
    "Cherry": "#8C3525",
    "Pure White": "#F5F5F5",
    "Off-White / Soft White": "#EEE9E0",
    "Matte Black": "#282828",
    "Bronze / Dark Anodized": "#443B34",
    "Charcoal / Slate Gray": "#4A5055"
}


def main():
    print("=" * 70)
    print("  ChromaKey AI - Multi-Style Window Matrix")
    print("=" * 70)
    print(f"Supported window types : {len(WINDOW_TYPES)}")
    print(f"Supported finishes     : {len(FINISH_CATALOG)}")
    print(f"Total combinations     : {len(WINDOW_TYPES) * len(FINISH_CATALOG)}")
    print("\nClient-side shader swaps the magenta key for every catalog finish.")
    for title, description in WINDOW_TYPES.values():
        print(f"  - {title:<22} : {description}")


if __name__ == "__main__":
    main()
