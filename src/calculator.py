import math
import random
import json
from enum import IntEnum

DEFAULTS = {
    'bsb_price': 2_500_000, # BSB
    # ROWS: EQUIP TYPE
    # COLS: ORE TYPE
    'ore_prices': [[1200000, 5600000], [1200000, 5300000]]
}

def load_config(config_file):
    with open(config_file) as f:
        data = json.load(f)
    return data

class EquipType(IntEnum):
    WEAPON = 0  # oridecom
    ARMOR = 1   # elunium

    def __repr__(self) -> str:
        return self.name

class OreType(IntEnum):
    ENRICHED = 0
    PERFECT = 1

    def __repr__(self) -> str:
        return self.name

def get_over_data(item_over: int) -> dict:
    if str(item_over) not in OVER_MODIFIERS['over']:
        item_over = -1
    return OVER_MODIFIERS['over'][str(item_over)]

def _get_refine_chance(item_over):
    return get_over_data(item_over)['chance']

def _is_refined(item_over):
    return True if random.random() < _get_refine_chance(item_over+1) else False

def _set_over(item_over, refine_success, ore_type, use_bsb):
    if refine_success:
        return item_over + 1

    # over protection
    if use_bsb:
        return item_over

    # perfect ores prevent breaking the item
    if ore_type == OreType.PERFECT:
        return item_over - 1

    # item breaks
    return -1

def _get_bsb_amount(over):
    return get_over_data(over)['bsb']

def _get_over_price(over: int, equip_type: EquipType):
    if str(over) not in OVER_MODIFIERS['over']:
        over = -1
    return OVER_MODIFIERS['over'][str(over)]['price'][str(equip_type)]

def _get_total_bsb_price(bsb_amount):
    return bsb_amount * DEFAULTS['bsb_price']

def _get_ore_type_price(equip_type, ore_type):
    return DEFAULTS['ore_prices'][equip_type][ore_type]

def refine(item_over, ore_type, use_bsb=False):
    
    success = _is_refined(item_over)

    return _set_over(item_over, success, ore_type, use_bsb)

def calc_resources(initial_over: int, target_over: int, equip_type: EquipType, bsb_default: bool=True, **kwargs: dict):

    data = []
    summary = {
        "tries": 0,
        "initial_over": 0,
        "final_over": 0,
        "resources": {
            "ore": 0,
            "bsb": 0,
        },
        "costs": {
            "over": 0,
            "bsb": 0,
            "ore": 0,
            "total": 0,
        },
        "over_data": None,
    }

    it = 0
    item_over = initial_over
    while item_over < target_over:

        use_bsb = kwargs.get(f'over_{item_over}', bsb_default)
        ore_type = OreType.ENRICHED if use_bsb else OreType.PERFECT

        old_over = item_over
        item_over = refine(item_over, ore_type, use_bsb)

        bsb_amount = _get_bsb_amount(old_over) if use_bsb else 0

        over_cost = _get_over_price(old_over, equip_type)
        bsb_cost = _get_total_bsb_price(bsb_amount)
        ore_cost = _get_ore_type_price(equip_type, ore_type)

        data.append({
            "index": it,
            "old_over": old_over,
            "new_over": item_over,
            "ore_type": ore_type,
            "bsb_amount": bsb_amount,
            "costs": {
                "over": over_cost,
                "bsb": bsb_cost,
                "ore": ore_cost,
                "total": over_cost + bsb_cost + ore_cost,
            }
        })

        summary["resources"]["ore"] += 1
        summary["resources"]["bsb"] += bsb_amount

        summary["costs"]["over"] += over_cost
        summary["costs"]["bsb"] += bsb_cost
        summary["costs"]["ore"] += ore_cost
        summary["costs"]["total"] += over_cost + bsb_cost + ore_cost

        if item_over == -1:
            break

        it += 1

    summary["tries"] = data[-1]['index'] + 1
    summary["initial_over"] = data[0]['old_over']
    summary["final_over"] = data[-1]['new_over']
    summary["over_data"] = data

    return summary

def acumulate(store, new_data):
    store['ore'] += new_data['resources']['ore']
    store['bsb'] += new_data['resources']['bsb']

    store['over_cost'] += new_data['costs']['over']
    store['bsb_cost'] += new_data['costs']['bsb']
    store['ore_cost'] += new_data['costs']['ore']
    store['total'] += new_data['costs']['total']

    return store

def simulate(initial_over: int, target_over: int, equip_type: int, num_simulations: int=1000, **kwargs: dict):

    simulations = {
        "min": None,
        "max": None,
        "avg": {
            'ore': 0,
            'bsb': 0,
            'over_cost': 0,
            'bsb_cost': 0,
            'ore_cost': 0,
            'total': 0,
        },
        'runs': [],
    }

    for _ in range(num_simulations):
        over_data = calc_resources(
            initial_over=initial_over,
            target_over=target_over,
            equip_type=equip_type,
            **kwargs,
        )

        simulations["runs"].append(over_data)

        if simulations["min"] is None:
            simulations["min"] = over_data

        if simulations["max"] is None:
            simulations["max"] = over_data

        simulations["min"] = min(simulations["min"], over_data, key=lambda x: x['costs']['total'])
        simulations["max"] = max(simulations["max"], over_data, key=lambda x: x['costs']['total'])

        simulations["avg"] = acumulate(simulations['avg'], over_data)

    for key in simulations['avg']:
        simulations['avg'][key] //= num_simulations

    return simulations

#---

OVER_MODIFIERS = load_config('./src/config.json')

over_data = calc_resources(
    initial_over=8,
    target_over=10,
    equip_type=EquipType.WEAPON,
    # over_9=False,
)

simulations = simulate(8, 10, EquipType.ARMOR, num_simulations=1000)

print(
    'MIN',
    simulations['min']['resources'],
    simulations['min']['costs'],
)
print(
    'MAX',
    simulations['max']['resources'],
    simulations['max']['costs'],
)
print(
    'AVG',
    simulations['avg']
)
print('---')

for run in simulations['runs']:
    print(
        'tries',
        run['tries'],
        run['resources'],
        run['costs'],
    )

print(simulations['runs'][0]['over_data'])
