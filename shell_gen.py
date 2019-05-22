"""
This file contains generators for APS shell body parts
"""
from copy import copy


# Generator for tail sections
def tailGen(limit, data=None):
    if data is None or len(data) == 0:
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
    def variants(limit, data, next_gen=None, *kargs):
        for i in range(0, limit+1):
            result = data + [name]*i
            if next_gen is not None and limit-i >= 0:
                yield from next_gen(limit - i, result, *kargs)
            else:
                yield result

    return variants


def bodySingleGen(variants):
    # Generator for a body
    def generator(limit, data, next_gen=None, *kargs):
        if next_gen is not None:
            yield from next_gen(limit, data, *kargs)
        for head in variants:
            result = data + [head]
            if limit > 0:
                yield from next_gen(limit - 1, copy(result), *kargs)
            else:
                yield result
    return generator


def headVariants(limit, data, next_gen, *args):
    # Generator for head variants
    yield from next_gen(limit, data, *args)
    for head in ["composite", "apcap", "hollow", "scharge", "sabot", "squash", "fraghead", "flakhead", "skimmer", "hollow", "HEhead"]:
        result = data + [head]
        if limit > 1:
            yield from next_gen(limit - 1, copy(result), *args)
        else:
            yield result


def makeShellVariants(limit, first, *args):
    variants = []
    data = []
    for var in first(limit, data, *args):
        if len(var) > 0:
            variants.append(var)
    return variants


def allBodyGen(limit):
    """
    Generator for all body shell types.
    @param limit: max number of elements in a blueprint.
    @generates a set of blueprints, like: ['apcap', 'solid', 'solid', 'bleeder', 'bleeder', 'bleeder', 'rail', 'rail']
    Note: it can generate a blueprint with a lesser number of elements. It just iterates over all possible variants.
    """
    data = []
    gens = [bodyGen(part) for part in ['bsabot', 'solid', 'HE', 'frag']]
    for var in headVariants(limit, data, *gens, tailGen):
        if len(var) > 0:
            yield var
