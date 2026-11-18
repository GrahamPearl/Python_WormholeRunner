"""Between-level perks (Expedition mode). Each level clear offers 3 random choices."""
PERKS = {
    "firepower": ("Firepower", "+20% weapon damage"),
    "armor": ("Hull Plating", "+25 max health and repair 25"),
    "engines": ("Overdrive Engines", "+12% speed and acceleration"),
    "cooldown": ("Quick Cycle", "Abilities recharge 20% faster"),
    "magnet": ("Tractor Field", "Pickups are drawn toward your ship"),
    "scavenger": ("Scavenger", "+25% credits earned"),
    "resupply": ("Resupply", "Refill all ammunition now"),
    "barrier": ("Barrier Cell", "+30 rechargeable shield"),
}


def apply_perk(player, perk_id):
    ship = player.ship
    player.perks[perk_id] = player.perks.get(perk_id, 0) + 1
    if perk_id == "firepower":
        player.dmg_mult *= 1.2
    elif perk_id == "armor":
        ship.max_health += 25
        ship.health = min(ship.max_health, ship.health + 25)
    elif perk_id == "engines":
        ship.speed_mult *= 1.12
        ship.accel_mult *= 1.12
    elif perk_id == "cooldown":
        player.cd_mult *= 0.8
    elif perk_id == "magnet":
        player.magnet += 170.0
    elif perk_id == "scavenger":
        player.credit_mult *= 1.25
    elif perk_id == "resupply":
        for slot in range(1, 10):
            start = int(player.weapons.cfg(slot).get("ammo", -1))
            if start > 0:
                player.weapons.ammo[slot] = start
    elif perk_id == "barrier":
        ship.shield_max += 30.0
        ship.shield_hp = min(ship.shield_max, ship.shield_hp + 30.0)
        ship.shield_rate = ship.shield_rate or 12.0
        ship.shield_delay = ship.shield_delay or 3.0
