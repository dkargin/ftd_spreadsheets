import ftd_calc as FTD
import json

shell_ref = dict(shell=['HE', 'HE', 'bleeder', 'gunpowder'])
FTD.calcBulletGeometry(shell_ref, diameter=0.5)
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

# Number of top variants to be generated
optimizer = FTD.ShellOptimizer(max_modules=8, max_results=4, score_fn=checkResult)
# A list to store results
results = []
batch = 4


#results += optimizer.calcBestShells(loader_length=1, loaders=1, clipsPerLoader=1, velCharge=0)

#results += FTD.calcBestShells(2, 4, batch, dict(loaders=1, clipsPerLoader=1, velCharge=0), checkResult)
#results += FTD.calcBestShells(1, 16, batch, dict(loaders=1, clipsPerLoader=1, velCharge=1000), checkResult)

real_data = [
    dict(shell=['HE', 'gunpowder'], diameter=0.5,
         T=22.16, velocity=326, ap=3.0, exp=2985, kin=2842),
    dict(shell=['HE', 'HE', 'HE', 'gunpowder'], diameter=0.5,
         velocity=169, ap=2.5, explosive=6096, kinetic=6428),
    dict(shell=['solid', 'solid', 'solid', 'gunpowder'], diameter=0.5,
         velocity=219, ap=4.4, kinetic=16713),
    dict(shell=['solid', 'solid', 'gunpowder', 'gunpowder'], diameter=0.5,
         velocity=433, ap=7.1, kinetic=17760),
    dict(shell=['solid', 'solid', 'gunpowder', 'gunpowder'], diameter=0.5, charge=1000,
         velocity=482, ap=7.9, kinetic=19775),
    dict(shell=['HE', 'HE', 'gunpowder', 'gunpowder'],
         diameter=0.5, T=31.33, velocity=333, ap=4.2, explosive=4684, kinetic=7196),
    dict(shell=['HE', 'HE', 'bleeder', 'gunpowder'],
         diameter=0.5, T=28.7, velocity=257, ap=3.5, explosive=4684, kinetic=6399),
    dict(shell=['HE', 'gunpowder', 'gunpowder', 'gunpowder'],
         diameter=0.5, velocity=490, ap=4.6, explosive=2985, kinetic=4263)
]


FTD.run_verification(real_data)
