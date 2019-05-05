import math
from copy import copy


"""
This module contains formulas for advanced cannons in From The Depths game
All calculations are done according to:
 - https://fromthedepths.gamepedia.com/Damage
 - https://fromthedepths.gamepedia.com/Advanced_Cannon
"""

"""
Useful Values:	AC	HP
Metal Block	15	350
Metal Beam	15	2100
Wood Block	3	180
Wood Beam	3	1080
Alloy Block	13	260
Alloy Beam	13	1560
HA Block	40	1000
HA Beam	40	6000
Stone Block	7	300
Stone Beam	7	1800

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
    "HE" : 1.0,
    "solid": 1.3,
    "flak": 1.0,
    "stab": 0.95,
    "frag": 1.0, 
    "squash" : 1.0,
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
    "HE" : 1.5,
    "solid": 2,
    "flak": 0.4,
    "stab": 0.5,
    "frag": 0.4, 
    "squash" : 0.3,
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
    "HE" : 2.5,
    "solid": 5,
    "flak": 0.4,
    "stab": 0.7,
    "frag": 0.8, 
    "squash" : 0.4,
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

# Bullet length without casing modules
def calcShellLength(context):
    numModules = context["modules"]
    propellant = context.get("propellant", 0)
    rails = context.get("rails", 0)
    return numModules - propellant - rails

# Calculates shell velocity from propellant burn
def calcVelocityFromPropellant(context):
    diameter = context["diameter"]
    propellant = context.get("propellant", 0)
    modules = context["modules"] 
    #length = context["shellLength"]
    shellModules = calcShellLength(context)
    speedC = context.get("speedC", 1.0)
    
    #mod = calcShellVolume(diameter, length)**0.03
    mod = calcShellVolumeForModules(diameter, shellModules)**0.03
    return 700.0 * propellant * speedC * mod / modules

# Calculates shell velocity from rail charge
def calcVelocityFromRails(context):
    diameter = context["diameter"]
    modules = context["modules"] 
    length = context["shellLength"]
    speedC = context.get("speedC")
    charge = context.get("velCharge", 0) # Energy used per shot
    numRail = context.get("rails", 0) # Number of rail casings
    if charge != 0:
        # Rail casings produce a series like: [1.0, 1.5, 1.9499999999999997, 2.3549999999999995, 2.7195]
        return (6.0 - 5.0 * (0.9**numRail)) * speedC * (8.0*charge)**0.5 / (length**0.25 * (5.0*diameter)**0.75)
    return 0

# Calculates total shell velocity
def calcTotalVelocity(context):
    prop = calcVelocityFromPropellant(context)
    rail = calcVelocityFromRails(context)
    return prop + rail

# Barrel length for propellant burn
def lengthForPropellant(propellant, diameter):
    return 16*propellant*diameter

"""
This is the "time to pass shell to ammo clip". Specifically, 
after this many seconds pass, each Input Feeder checks whether
it can reload its associated autoloader. If there is space,
the Input Feeder moves one cartridge from the supply to the autoloader's clips. Otherwise, it retries every second. 
"""
def calcTimeToClip(diameter, length):
    return 100 * calcShellVolume(diameter, length)**0.5

"""
This is the time to load from clip to autoloader.
Notice, it is twice faster than loading to a clip
"""
def calcClipToAutoloader(context):
    diameter = context["diameter"]
    length = context["length"]
    totalLoaders = context.get("loaders", 1)
    if context.get("belt", False):
        return 10 * (totalLoaders**0.25) * (calcShellVolume(diameter, length))**0.5
    clipsAttached = context.get("clipsPerLoader", 1)
    return 50 * (totalLoaders**0.25) * (calcShellVolume(diameter, length)/ clipsAttached)**0.5

"""
Time to cool down a barrel after a shot.
"""
def calcBarrelCooldown(diameter, propellant, numCooling):
    return 6 * (5*diameter)**1.5 * (propellant ** 0.5) * 0.92 ** numCooling

# 0.92 ** numCooling = clipToAutoloader(context) / (6 * (5*diameter)**1.5 * (propellant ** 0.5))
# numCooling = math.log(clipToAutoloader(context) / (6 * (5*diameter)**1.5 * (propellant ** 0.5)))

# Number of coolers necessary to match autoloader speed
def calcNumberOfCoolers(context):
    diameter = context["diameter"]
    propellant = context.get("propellant", 0)
    if propellant == 0:
        return 0
    return math.log(calcClipToAutoloader(context) / (6 * (5*diameter)**1.5 * (propellant ** 0.5)), 0.92)

# Total inaccuracy, in degrees
def calcAccuracy(context):
    # barrelLength, diameter, numModules, propellant, railCharge = 0
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
    shellModules = calcShellLength(context)
    kineticC = context["kineticC"]
    vel = calcTotalVelocity(context)
    ap = 0.01 * context["armorC"] * vel
    # Right now it calculates a proper values, but maybe we should replace 'shellModules' by an actual length
    return 1.25 * kineticC * vel * ((5*diameter)**1.95) * (shellModules**0.65), ap

def calcExplosiveDamage(diameter, numExplosive):
    return 500 * ((5*diameter)**1.95) * (numExplosive**0.65)

def calcFlakDamage(diameter, numFlak):
    return 250 * ((5*diameter)**1.95) * (numExplosive**0.65)

def calcNumFrags(diameter):
    return 10 * (d**2 / 0.008)**0.65

def calcFragDamage(diameter):
    return 200 * (5*d)**0.5

"""
Upon hitting a surface the squash head ejects damaging particles on the opposite side. The number of particles is equal to the spalling metric divided by the number of AC-metres passed through.

Each particle does 200 damage and has AP equal to twice the armour of the last material passed through
@returns list of damages
"""
def calcSquashDamage(diameter, numExplosive, armor = 6):
    # This damage has two parts:
    # - direct thump damage and spalling particles
    spallMetric = 15 * (5*diameter)**1.95 * numExplosive**0.65
    numSpalls = spallMetric / armor
    thumpDamage = 400 * (5*diameter)**1.95 * numExplosive**0.65
    # Thump damage has AP 6. 
    return [(thumpDamage, 6), (numSpalls * 200, 2*armor)]

def calcShapeChargeDamage(diameter, numExplosive, factor):
    # Penetration metric. Where do we use it?
    metric = 30* (5*diameter)**1.95 * (metric*numExplosive)**0.65
    particleCount = 10 * (5*diameter)**1.95 * ((1 - factor)*numExplosive)**0.65
    # Each particulate deals 200 damage at AP 10. 
    return 200 * particleCount, 10
    

# Total damage from fragmentation parts
# Note: all frags have AP=6
def calcTotalFragDamage(diameter, frags):
    return calcNumFrags(diameter) * calcFragDamage(diameter) * frags

def calcArmorMod(ap, armor):
    if ap != 0:
        return 0.05 + 0.45 * ap / armor
    return 0.05

# Fills in damage values
def calcDPS(context):
    diameter = context.get("diameter")
    
    if 'length' not in context:
        context['length'] = context['modules'] * diameter
    if 'shellLength' not in context:
        context['shellLength'] = calcShellLength(context) * diameter
        
    period = calcClipToAutoloader(context)
    
    damage = {}
    result = {"period" : period, "damage": damage}
    
    damageKin = calcKineticDamage(context)
    if damageKin != 0:   
        damage["kinetic"] = damageKin
        
    baseAp = calcBaseAp(context)
    
    numExplosive = context.get("numExplosive", 0)
    if numExplosive != 0:
        damageExp = calcExplosiveDamage(diameter, numExplosive)
        damage["HE"] = (damageExp, baseAp)
    
    numFlak = context.get("numFlak", 0)
    if numFlak != 0:
        damageFlak = calcFlakDamage(diameter, numFlak)
        damage["flak"]  = (damageFlak, baseAp)
    
    armor = context.get("armor", 8)
    
    damageTotal = 0
    # Calculates DPS using damage profile
    for name, val in result["damage"].items():
        if len(val) != 2:
            raise "Invalid data for damage type %s: %s" % (name, str(val))
        damageTotal += val[0] # * calcArmorMod(val[1], armor)
        
    dps = damageTotal / period
    result["dps"] = dps
    
    velProp = calcVelocityFromPropellant(context)
    if velProp != 0:
        result["vp"] = velProp
        
    velRail = calcVelocityFromRails(context)
    if velRail != 0:
        result["vr"] = velRail
    return result

"""
This set of functions is used to generate shell variants and calculate its stats
"""

def shellSize(shell):
    size = 0
    for i in range(0, len(shell)):
        if shell[i] in TailParts:
            break
        size += 1
    return size

shell_mod_scale = 0.75

# Calculates speed modifier for a shell
def calcSpeedMod(shell):
    up = 0
    down = 0
    for i in range(0, len(shell)):
        module = shell[i]
        if module in TailParts:
            break
        weight = shell_mod_scale**i
        mod = ShellSpeedMod.get(module, 1.0)
        up += mod * weight
        down += weight
    
    return up / down if down > 0 else 1.0

# Calculates armor piercing modifier
def calcApMod(shell):
    up = 0
    down = 0
    size = shellSize(shell)
    for i in range(0, max(size, 3)):
        weight = shell_mod_scale**i
        mod = ShellApMod.get(shell[i], 1.0) if i < size else 0.5
        up += mod * weight
        down += weight
    return up / down if down > 0 else 1.0

def calcApModTest(shell):
    up = []
    down = []
    size = shellSize(shell)
    for i in range(0, max(size, 3)):
        weight = shell_mod_scale**i
        mod = ShellApMod.get(shell[i], 1.0) if i < size else 0.5
        up.append(mod * weight)
        down.append(weight)
    return up, down

# Calculates kinetic modifier for the shell
def calcKineticMod(shell):
    up = 0
    down = 0
    size = shellSize(shell)
    for i in range(0, max(size, 3)):
        mod = ShellKineticMod.get(shell[i], 1.0) if i < size else 0.5
        up += mod
        down += 1
    
    return up / down if down > 0 else -1.0

def calcKineticModTest(shell):
    up = []
    size = shellSize(shell)
    for i in range(0, max(size, 3)):
        mod = ShellKineticMod.get(shell[i], 1.0) if i < size else 0.5
        up.append(mod)
    return up

# Calculates basic stats for a shell blueprint
# @param shell: a list containing names of shell parts, in order from top to bottom
def calcBulletStats(blueprint):
    bleeder = 0.0
    explosive = 0
    flak = 0
    rails = 0
    propellant = 0
    explosiveMod = 1.0
    flakMod = 1.0
    
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
            explosiveMod = 0.25
    
    shellHead = blueprint[-(propellant + rails):]
            
    result = {
        "kineticC": calcKineticMod(blueprint),
        "speedC": calcSpeedMod(blueprint) * (1+bleeder),
        "armorC": calcApMod(blueprint),
        "modules": len(blueprint),
        "expMod": explosiveMod, # Applies for explosive, flak, EMP
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
    return result


def calcBulletLength(config, diameter):
    """
    Calculates button length given config and diameter
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
    

# Generator for tail sections
def tailGen(limit, data=[]):
    if len(data) == 0:
        yield []
        return
    for i in range(0, limit+1):
        for j in range(0, limit+1-i): 
            for k in range(0, min(limit+1-i-j, 2)):
                if i + j > 0:
                    yield data + ["bleeder"]*k+["gunpowder"]*i + ["rail"]*j
    pass

# Generator for shell body part
def bodyGen(name):
    def variants(limit, data, nextGen=None, *kargs):
        #if nextGen is not None:
        #    yield from nextGen(limit, copy(data), *kargs)
        for i in range(0, limit+1):
            result = data + [name]*i
            if nextGen is not None and limit-i >= 0:
                yield from nextGen(limit-i, result, *kargs)
            else:
                yield result

    return variants

# Generator for a body
def bodySingleGen(variants):
    def generator(limit, data, nextGen=None, *kargs):
        if nextGen is not None:
            yield from nextGen(limit, data, *kargs)
        for head in variants:
            result = data + [head]
            if limit > 0:
                yield from nextGen(limit-1, copy(result), *kargs)
            else:
                yield result
    return generator

# Generator for head varians
def headVariants(limit, data, nextGen, *kargs):
    yield from nextGen(limit, data, *kargs)
    for head in ["composite", "apcap", "hollow", "scharge", "sabot", "squash"]:
        result = data + [head]
        if limit > 1:
            yield from nextGen(limit-1, copy(result), *kargs)
        else:
            yield result
    
def makeShellVariants(limit, first,  *kargs):
    variants = []
    data = []
    for var in first(limit, data, *kargs):
        if len(var) > 0:
            variants.append(var)
    return variants

"""
Generator for all body shell types.
@param limit: max number of elements in a blueprint. 
@generates a set of blueprints, like: ['apcap', 'solid', 'solid', 'bleeder', 'bleeder', 'bleeder', 'rail', 'rail']
Note: it can generate a blueprint with a lesser number of elements. It just iterates over all possible variants.
"""
def allBodyGen(limit):
    generators = ()
    data = []
    gens = [bodyGen(part) for part in ['bsabot', 'solid', 'HE']]
    for var in headVariants(limit, data, *gens, tailGen):
        if len(var) > 0:
            yield var    

"""
Finds best diameter/dps for specified loader length
"""
def calcDPSForLoader(loaderLength, context):
    # length = diameter * (modules)
    modules = context.get("modules", 1)
    diameter = float(loaderLength) / modules
    context["diameter"] = diameter
    results = []
    for p in range(0, modules):
        for r in range(0, modules-p+1):
            context["propellant"] = p
            context["rails"] = r
            data = calcDPS(context)
            data["diameter"] = diameter
            
            if p > 0:
                data["propellant"] = p            
            if r > 0:
                data["rails"] = r
            calcWeaponInfo(data)
            
            results.append(data)
    return results

def calcCannonData(config):
    """
    Calculates weapon data that could be derived from shell data and diameter
    @param config: weapon config
    """
    data = calcDPS(config)
    config.update(data)

    prop = config.get("propellant", 0)
    if prop > 0:
        barrel = lengthForPropellant(prop, config['diameter'])
        if barrel > 0:
            config["barrel_p"] = barrel
    coolers = calcNumberOfCoolers(config)
    if coolers > 0:
        config["coolers"] = coolers
        
    config["velocity"] = calcTotalVelocity(config)
    config["accuracy"] = calcAccuracy(config)

"""
Finds the best weapon config for specified weapon limits
@param loaderLength: max length of loader
@param maxModules: max shell modules to be used
@param batch: number of results to be uploaded
@param context: additional weapon data
@param scoreFn: function to calculate a score to generated config
"""
def calcBestShells(loaderLength, maxModules, batch, context, scoreFn=None):
    best = []
    current = []
    
    if scoreFn is None:
        scoreFn = lambda a: a["dps"]
    
    for blueprint in allBodyGen(maxModules):
        config = calcBulletStats(blueprint)
        config = dict(context, **config)
        
        modules = config.get("modules", 1)
        diameter = float(loaderLength) / modules
        if diameter > 0.5:
            diameter = 0.5
        config["diameter"] = diameter
        
        calcBulletLength(config, diameter)
        
        calcCannonData(config)
        
        if scoreFn(config) > 0:
            current.append(config)
        
        if len(current) > batch: 
            best = sorted(best + current, key=scoreFn)[-batch:]
            current = []
    
    return sorted(best + current, key=scoreFn)[-batch:]
