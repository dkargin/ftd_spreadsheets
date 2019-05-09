import ftd_calc as FTD
import json

shell_ref = dict(shell=['HE', 'HE', 'bleeder', 'gunpowder'])
FTD.calcBulletLength(shell_ref, diameter=0.5)
print(shell_ref)


shell_bp = ['HE', 'HE', 'bleeder', 'gunpowder']
shell_stats = FTD.calcBulletStats(shell_bp, 0.5)
print(shell_stats)

FTD.calcCannonData(shell_stats)
print(shell_stats)


# Tests for optimization
def checkResult(config):
    if config.get("velocity", 0) < 50:
        return -1.0
    return config["dps"]

batch = 4
results = FTD.calcBestShells(2, 4, batch, dict(loaders=1, clipsPerLoader=1, velCharge=0), checkResult)
results += FTD.calcBestShells(1, 16, batch, dict(loaders=1, clipsPerLoader=1, velCharge=1000), checkResult)
