import math
from copy import copy
from shell_gen import *

"""
This module contains formulas for advanced cannons in From The Depths game
All calculations are done according to:
 - https://fromthedepths.gamepedia.com/Damage
 - https://fromthedepths.gamepedia.com/Advanced_Cannon
"""

"""
Useful Values:	AC	HP
Metal Block	    15	350
Metal Beam	    15	2100
Wood Block	    3	180
Wood Beam	    3	1080
Alloy Block	    13	260
Alloy Beam	    13	1560
HA Block	    40	1000
HA Beam         40	6000
Stone Block	    7	300
Stone Beam  	7	1800

Thump damage is dealt by:
    Hollow point and squash head shells (AP 6)
    Impact particle cannons (AP 15)
    Thumper missile warheads (AP 6)
    Collisions (AP 1)
    Rams (AP 15)
"""

            
# Speed modifier for the shell's part
ShellSpeedMod = {
    "rail": 1.0,
    "gunpowder": 1.0,
    "bleeder": 1.1,
    "bsabot": 1.75,
    "HE": 1.0,
    "solid": 1.3,
    "flak": 1.0,
    "stab": 0.95,
    "frag": 1.0, 
    "squash": 1.0,
    "sabot": 2.05,
    "scharge": 1.4,
    "hollow": 1.4,
    "apcap": 1.5,
    "composite": 1.6,
}

# Armor piercing modifier for the shell's part
ShellApMod = {
    "rail": 1,
    "gunpowder": 1,
    "bleeder": 1,
    "bsabot": 3.6,
    "HE": 1.5,
    "solid": 2,
    "flak": 0.4,
    "stab": 0.5,
    "frag": 0.4, 
    "squash": 0.3,
    "sabot": 6.75,
    "scharge": 0.1,
    "hollow": 0.25,
    "apcap": 3.5,
    "composite": 4.5,
}

# Kinetic modifier for the shell's part
ShellKineticMod = {
    "rail": 1.0,
    "gunpowder": 1.0,
    "bleeder": 1.0,
    "bsabot": 2.7,
    "HE": 2.5,
    "solid": 5,
    "flak": 0.4,
    "stab": 0.7,
    "frag": 0.8, 
    "squash": 0.4,
    "sabot": 1.8,
    "scharge": 0.5,
    "hollow": 1.2,
    "apcap": 10.0,
    "composite": 5.0,
}

TailParts = ['rail', 'gunpowder']

# Limits to shell module length
ShellModuleLength = {
    "bleeder": 0.1,
}


def calcShellVolume(diameter, length):
    """
    Calculates shell volume
    @param diameter - shell diameter, [m]
    @param length - shell length, [m]
    """
    return 0.25*math.pi * diameter**2 * length


def calcShellVolumeForModules(diameter, modules):
    """
    Calculates shell volume, considering each module have the same length,
    equal to diameter
    @param diameter - shell diameter, [m]
    @param modules - number of modules
    """
    return 0.25*math.pi * diameter**3 * modules


def calcShellLength(context):
    """Bullet length without casing modules"""
    numModules = context["modules"]
    propellant = context.get("propellant", 0)
    rails = context.get("rails", 0)
    return numModules - propellant - rails


def calcVelocityFromPropellant(context):
    """Calculates shell velocity from propellant burn"""
    diameter = context["diameter"]
    propellant = context.get("propellant", 0)
    modules = context["modules"] 
    length = context["shellLength"]
    speedC = context.get("speedC", 1.0)
    
    mod = calcShellVolume(diameter, length)**0.03
    return 700.0 * propellant * speedC * mod / modules


def calcVelocityFromRails(context):
    """Calculates shell velocity from rail charge"""
    diameter = context["diameter"]
    shellLength = context["shellLength"]
    length = context["length"]
    speed_mod = context.get("speedC")
    charge = context.get("velCharge", 0)  # Energy used per shot
    num_rails = context.get("rails", 0)  # Number of rail casings
    if charge != 0:
        # Rail casings produce a series like: [1.0, 1.5, 1.9499999999999997, 2.3549999999999995, 2.7195]
        rail_mod = 6.0 - 5.0 * (0.9**num_rails)
        return rail_mod * speed_mod * (8.0*charge)**0.5 / (125 * length * diameter**3)**0.25
        #return rail_mod * speed_mod * (8.0*charge)**0.5 / (shellLength**0.25 * (5.0*diameter)**0.5)
    return 0


def calcTotalVelocity(context):
    """Calculates total shell velocity"""
    prop = calcVelocityFromPropellant(context)
    rail = calcVelocityFromRails(context)
    return prop + rail


def lengthForPropellant(propellant, diameter):
    """Barrel length for propellant burn"""
    return 16*propellant*diameter


def calcTimeToClip(diameter, length):
    """
    This is the "time to pass shell to ammo clip". Specifically,
    after this many seconds pass, each Input Feeder checks whether
    it can reload its associated autoloader. If there is space,
    the Input Feeder moves one cartridge from the supply to the autoloader's clips. Otherwise, it retries every second.
    """
    return 100 * calcShellVolume(diameter, length)**0.5


def calcClipToAutoloader(context):
    """
    This is the time to load from clip to autoloader.
    Notice, it is twice faster than loading to a clip
    """
    diameter = context["diameter"]
    length = context["length"]
    totalLoaders = context.get("loaders", 1)
    if context.get("belt", False):
        return 10 * (totalLoaders**0.25) * (calcShellVolume(diameter, length))**0.5
    clipsAttached = context.get("clipsPerLoader", 1)
    return 50 * (totalLoaders**0.25) * (calcShellVolume(diameter, length)/ clipsAttached)**0.5


def calcBarrelCooldown(diameter, propellant, numCooling):
    """
    Time to cool down a barrel after a shot.
    """
    return 6 * (5*diameter)**1.5 * (propellant ** 0.5) * 0.92 ** numCooling


def calcNumberOfCoolers(context):
    """Number of coolers necessary to match autoloader speed"""
    diameter = context["diameter"]
    propellant = context.get("propellant", 0)
    if propellant == 0:
        return 0
    coolers = math.log(calcClipToAutoloader(context) / (6 * (5*diameter)**1.5 * (propellant ** 0.5)), 0.92)
    if coolers < 0:
        coolers = 0
    return math.ceil(coolers)


def calcAccuracy(context):
    """Total inaccuracy, in degrees"""
    diameter = context["diameter"]
    propellant = context.get("propellant", 0)
    shell = context.get("length", calcShellLength(context))
    # Barrel length
    barrel = context.get("barrel", 10)
    railCharge = context.get("accCharge", 0)
    base = 4*shell*diameter**0.5 / (barrel - propellant*diameter) if barrel - propellant*diameter > 0 else 0
    return base / (1 + 0.001 * railCharge / (shell*diameter))


def calcBaseAp(context):
    vel = calcTotalVelocity(context)
    ap = 0.01 * context["armorC"] * vel
    return ap


def calcKineticDamage(context):
    diameter = context["diameter"]
    length = context["shellLength"]
    kineticC = context["kineticC"]
    vel = calcTotalVelocity(context)
    ap = 0.01 * context["armorC"] * vel
    return 1.25 * kineticC * vel * (125 * diameter**2 * length) ** 0.65, ap


def calcExplosiveDamage(diameter, num_explosive):
    return 500 * (125*diameter**3 * num_explosive)**0.65


def calcFlakDamage(diameter, num_flak):
    return 250 * (125*diameter**3 * num_flak)**0.65


def calcNumFrags(diameter):
    return 10 * (diameter**2 / 0.008)**0.65


def calcFragDamage(diameter):
    return 200 * (5*diameter)**0.5


def calcSquashDamage(diameter, num_explosive, armor=6):
    """
    Upon hitting a surface the squash head ejects damaging particles on the opposite side. The number of particles is equal to the spalling metric divided by the number of AC-metres passed through.

    Each particle does 200 damage and has AP equal to twice the armour of the last material passed through
    @returns list of damages
    """

    # This damage has two parts:
    # - direct thump damage and spalling particles
    spall_metric = 15 * (125*diameter**3 * num_explosive)**0.65
    num_spalls = spall_metric / armor
    thump_damage = 400 * (125*diameter**3 * num_explosive)**0.65
    # Thump damage has AP 6. 
    return [(thump_damage, 6), (num_spalls * 200, 2*armor)]


def calcShapeChargeDamage(diameter, num_explosive, factor):
    # Penetration metric. Where do we use it?
    metric = 30 * (5*diameter)**1.95 * (factor * num_explosive) ** 0.65
    particle_count = 10 * (5*diameter)**1.95 * ((1 - factor) * num_explosive) ** 0.65
    # Each particulate deals 200 damage at AP 10. 
    return 200 * particle_count, 10
    

# Total damage from fragmentation parts
# Note: all frags have AP=6
def calcTotalFragDamage(diameter, frags):
    return calcNumFrags(diameter) * calcFragDamage(diameter) * frags


def calcArmorMod(ap, armor):
    if ap != 0:
        return 0.05 + 0.45 * ap / armor
    return 0.05


def calcWeaponDPS(context):
    """
    Calculates the best DPS for a weapon, considering there are enough reloaders and coolers
    """
    diameter = context.get("diameter")
    
    if 'length' not in context:
        context['length'] = context['modules'] * diameter
    if 'shellLength' not in context:
        context['shellLength'] = calcShellLength(context) * diameter
        
    period = calcClipToAutoloader(context)
    
    damage = {}
    result = {"period": period, "damage": damage}
    
    damage_kinetic = calcKineticDamage(context)
    if damage_kinetic != 0:
        damage["kinetic"] = damage_kinetic
        
    base_ap = calcBaseAp(context)
    
    num_explosive = context.get("numExplosive", 0)
    if num_explosive != 0:
        damage_explosive = calcExplosiveDamage(diameter, num_explosive)
        damage["HE"] = (damage_explosive, base_ap)
    
    num_flak = context.get("numFlak", 0)
    if num_flak != 0:
        damage_flak = calcFlakDamage(diameter, num_flak)
        damage["flak"] = (damage_flak, base_ap)
    
    armor = context.get("armor", 8)
    
    damage_total = 0
    # Calculates DPS using damage profile
    for name, val in result["damage"].items():
        if len(val) != 2:
            raise "Invalid data for damage type %s: %s" % (name, str(val))
        damage_total += val[0]
        
    dps = damage_total / period
    result["dps"] = dps
    
    velocity_from_propellant = calcVelocityFromPropellant(context)
    if velocity_from_propellant != 0:
        result["vp"] = velocity_from_propellant
        
    velocity_from_rail = calcVelocityFromRails(context)
    if velocity_from_rail != 0:
        result["vr"] = velocity_from_rail
    return result


def shell_module_size(shell):
    size = 0
    for i in range(0, len(shell)):
        if shell[i] in TailParts:
            break
        size += 1
    return size


# Calculates speed modifier for a shell
def calcSpeedMod(shell):
    up = 0
    down = 0
    for i in range(0, len(shell)):
        module = shell[i]
        if module in TailParts:
            break
        weight = 0.75**i
        mod = ShellSpeedMod.get(module, 1.0)
        up += mod * weight
        down += weight
    
    return up / down if down > 0 else 1.0


# Calculates armor piercing modifier
def calcApMod(shell):
    up = 0
    down = 0
    size = shell_module_size(shell)
    for i in range(0, max(size, 3)):
        weight = 0.75**i
        mod = ShellApMod.get(shell[i], 1.0) if i < size else 0.5
        up += mod * weight
        down += weight
    return up / down if down > 0 else 1.0


def calcApModTest(shell):
    up = []
    down = []
    size = shell_module_size(shell)
    for i in range(0, max(size, 3)):
        weight = 0.75**i
        mod = ShellApMod.get(shell[i], 1.0) if i < size else 0.5
        up.append(mod * weight)
        down.append(weight)
    return up, down


# Calculates kinetic modifier for the shell
def calcKineticMod(shell):
    up = 0
    down = 0
    size = shell_module_size(shell)
    for i in range(0, max(size, 3)):
        mod = ShellKineticMod.get(shell[i], 1.0) if i < size else 0.5
        up += mod
        down += 1
    
    return up / down if down > 0 else -1.0


def calcKineticModTest(shell):
    up = []
    size = shell_module_size(shell)
    for i in range(0, max(size, 3)):
        mod = ShellKineticMod.get(shell[i], 1.0) if i < size else 0.5
        up.append(mod)
    return up


def calcBulletStats(blueprint, diameter=None):
    """
    Calculates basic stats for a shell blueprint
    @param blueprint: a list containing names of shell parts, in order from top to bottom
    @param diameter - shell diameter
    @return:dict weapon config, used for further calculations

    It will contain:
     - kineticC": calcKineticMod(blueprint),
     - speedC": calcSpeedMod(blueprint) * (1+bleeder),
     - armorC": calcApMod(blueprint),
     - modules": len(blueprint),
     - expMod": explosive_mod,  # Applies for explosive, flak, EMP
     - shell: shell blueprint: copy(blueprint),
     - propellant - number of propellant modules
     - rails - number of railgun casings
     - numExplosive - number of explosive modules
     - numFlak - number of flak modules

    It will calculate geometry if diameter is not None:
     - shellLength - length of the shell, in meters
     - length - total length, in meters
     - diameter - assigned diameter
    """

    bleeder = 0.0
    explosive = 0
    flak = 0
    rails = 0
    propellant = 0
    explosive_mod = 1.0
    flak_mod = 1.0
    
    for part in blueprint:
        if part == "bleeder":
            # Only one bleeder is allowed
            bleeder = 0.2
        elif part == "HE":
            explosive += 1
        elif part == "flak":
            flak += 1
        elif part == "gunpowder":
            propellant += 1
        elif part == "rail":
            rails += 1
        elif part == 'sabot' or part == 'bsabot':
            explosive_mod = 0.25
            
    result = {
        "kineticC": calcKineticMod(blueprint),
        "speedC": calcSpeedMod(blueprint) * (1+bleeder),
        "armorC": calcApMod(blueprint),
        "modules": len(blueprint),
        "expMod": explosive_mod,  # Applies for explosive, flak, EMP
        "shell": copy(blueprint),
    }
    if propellant > 0:
        result["propellant"] = propellant
    if explosive > 0:
        result["numExplosive"] = explosive
    if flak > 0:
        result["numFlak"] = flak
    if rails > 0:
        result["rails"] = rails
        
    if diameter is not None:
        calcBulletGeometry(result, diameter)
        
    return result


def calcBulletGeometry(config, diameter):
    """
    Calculates button geometry given config and diameter
    """
    # Length without casing parts
    shellLength = 0
    # Total shell length
    length = 0
    
    for part in config.get('shell', []):
        partLength = min(ShellModuleLength.get(part, 1.0), diameter)
        if part not in TailParts:
            shellLength += partLength
        length += partLength
        
    config["shellLength"] = shellLength
    config["length"] = length
    config["diameter"] = diameter
    return config


def calcCannonData(config):
    """
    Calculates weapon data that could be derived from shell data and diameter
    @param config: weapon config
    """
    data = calcWeaponDPS(config)
    config.update(data)

    # Approximate number of blocks in laboratory weapon design.
    blocks = 1

    prop = config.get("propellant", 0)
    if prop > 0:
        barrel = lengthForPropellant(prop, config['diameter'])
        if barrel > 0:
            config["barrel_p"] = barrel
            blocks += math.ceil(barrel)
    coolers = calcNumberOfCoolers(config)
    if coolers > 0:
        config["coolers"] = coolers
        
    config["velocity"] = calcTotalVelocity(config)
    config["accuracy"] = calcAccuracy(config)
    
    # TODO: Calculate number of recoil adsorbers
    # TODO: Calculate number of gauge increasers

    autoloaderSize = config.get('loader_length', 1)
    loaders = config.get('loaders', 1)
    # Gauge complex
    blocks += coolers
    # Autoloader complex
    blocks += (loaders + config.get("clipsPerLoader", 1)) * autoloaderSize
    # Inserters
    blocks += loaders * config.get("clipsPerLoader", 1) * 2

    # Rail block
    vel_charge = config.get('vel_charge', 0)
    if vel_charge > 0:
        charge_per_second = vel_charge / config['period']
        # 100 charge per second
        chargers = math.ceil(charge_per_second / 100)
        blocks += chargers + 4

    config['blocks'] = blocks

    return config


MAX_DIAMETER = 0.500
MIN_DIAMETER = 0.018


class ShellOptimizer:
    """
    This class provides sheel optimization routines
    """
    def __init__(self, **kwargs):
        """
        @param loader_length: length of autoloader
        @param max_modules: max shell modules to be used
        @param max_results: number of results to be uploaded
        @param score_fn: function to calculate a score to generated config
        """
        # Max module number to be optimized
        self.max_modules = kwargs.get('max_modules', 4)
        # Maximum number of reported results per optimization run
        self.max_results = kwargs.get('max_results', 4)
        # Score/filter function
        self.score_fn = kwargs.get('score_fn', None)
        self.diameter = kwargs.get('diameter', 'auto')

    def calcBestShells(self, **kwargs):
        """
        Finds the best weapon config for specified weapon limits
        """
        best = []
        current = []
        scoreFn = self.score_fn
        diameter_mode = self.diameter
        
        if scoreFn is None:
            scoreFn = lambda a: a["dps"]

        vel_charge = kwargs.get('velCharge', 0)

        for blueprint in allBodyGen(self.max_modules):
            config = dict(calcBulletStats(blueprint), **kwargs)
            if 'loader_length' not in config:
                config['loader_length'] = 1
            if vel_charge == 0 and config.get('propellant', 0) == 0:
                continue
                
            modules = config.get("modules", 1)
            
            if diameter_mode == 'auto':
                # TODO: check if there are only rail blocks. Then we will take lowest diameter possible
                # We are trying to get max possible diameter for the shell. Some modules have a limit for max diameter,
                # so this calculation can provide us a bit smaller shell than it could be
                if vel_charge > 0 and config.get('propellant', 0) == 0:
                    diameter = MIN_DIAMETER
                else:
                    diameter = float(config['loader_length']) / modules
            else:
                diameter = diameter_mode
                
            if diameter > MAX_DIAMETER:
                diameter = MAX_DIAMETER
            if diameter < MIN_DIAMETER:
                diameter = MIN_DIAMETER

            calcBulletGeometry(config, diameter)
            calcCannonData(config)

            if scoreFn(config) > 0:
                current.append(config)

            if len(current) > self.max_results: 
                best = sorted(best + current, key=scoreFn)[-self.max_results:]
                current = []

        return sorted(best + current, key=scoreFn)[-self.max_results:]

    
def calcBestShells(loaderLength, maxModules, batch, context, scoreFn=None):
    """
    Finds the best weapon config for specified weapon limits
    @param loaderLength: max length of loader
    @param maxModules: max shell modules to be used
    @param batch: number of results to be uploaded
    @param context: additional weapon data
    @param scoreFn: function to calculate a score to generated config
    """
    best = []
    current = []
    
    if scoreFn is None:
        scoreFn = lambda a: a["dps"]
    
    for blueprint in allBodyGen(maxModules):
        config = calcBulletStats(blueprint)
        config = dict(context, **config)
        
        modules = config.get("modules", 1)
        # We are trying to get max possible diameter for the shell. Some modules have a limit for max diameter,
        # so this calculation can provide us a bit smaller shell than it could be
        diameter = float(loaderLength) / modules
        if diameter > MAX_DIAMETER:
            diameter = MAX_DIAMETER
        if diameter < MIN_DIAMETER:
            diameter = MIN_DIAMETER
        
        calcBulletGeometry(config, diameter)
        calcCannonData(config)
        
        if scoreFn(config) > 0:
            current.append(config)
        
        if len(current) > batch: 
            best = sorted(best + current, key=scoreFn)[-batch:]
            current = []
    
    return sorted(best + current, key=scoreFn)[-batch:]


def formatValue(key, value):
    """
    Formating value to be displayed in results table
    """
    if key == 'diameter':
        return '{:3}'.format(math.floor(value*1000))
    if key == 'damage':
        damage_data = []
        for dtype, damage in value.items():
            if isinstance(damage, tuple) and len(damage) == 2:
                damage_data.append('{0}={1:3d}:{2:3.1f}'.format(dtype, int(damage[0]), damage[1]))
            else:
                damage_data.append('{0}={1}'.format(dtype, str(damage)))
        return '</br>'.join(damage_data)
    if isinstance(value, float):
        return '{: 3.2f}'.format(value)
    
    return str(value)

from IPython.display import HTML, display

def displayTable(results, columns=None):
    """
    Generates HTML table for results obtained from calcBestShells
    @param results - a list with results, obtained from calcBestShells
    @param columns:list - a list of column names to be displayed
    """
    if columns is None:
        columns = ["dps", "damage", "diameter", "velocity", "period", "blocks", "shell"]
    # Row start - caption
    # Column - output variant
    # html = <table><tr><td>Name</td><td>Data1</td></tr></table>
    caption = '<td>{}</td>'.format('</td><td>'.join('<b>{}</b>'.format(str(key).upper()) for key in columns))
    rows = []
    for row in results:
        line = '</td><td>'.join(formatValue(key, row[key]) for key in columns)
        rows.append('<td>{}</td>'.format(line))
    
    htmlData = '</tr><tr>'.join(rows)
    return display(HTML('<table><tr>' + caption + '</tr><tr>' + htmlData + '</tr></table>'))
