import pandas as pd
import numpy as np
from fractions import Fraction
import periodictable
import re

def get_factor(string):
    if '/' in string:
        # faction
        return float(Fraction(string))
    else:
        # string
        return float(string)


def calculate_mass(count, data):
    mass = 0
    for num in range(count):
        element = data[num]['e']
        mass += data[num]['w'] * periodictable.__dict__[element].mass

    return mass


def get_mass(composition):
    pattern = "A[cglmrstu]|B[aehikr]?|C[adeflmnorsu]?|D[bsy]|E[rsu]|F[elmr]?|G[ade]|H[efgos]?|I[nr]?|Kr?|L[airuv]|M[dgnot]|N[abdeiop]?|Os?|P[abdmortu]?|R[abefghnu]|S[bcegimnr]?|T[abcehilm]|U(u[opst])?|V|W|Xe|Yb?|Z[nr]"
    result = []
    elementCount = 0

    nextString = composition.strip()
    nextMatch = re.search(pattern, nextString)

    while nextMatch:
        element = nextMatch.group(0)
        span = nextMatch.span(0)
        begIdx, endIdx = span

        # Adjust the factor value of the previous element
        if begIdx != 0:
            prefix = nextString[:begIdx]
            previousFactor = get_factor(prefix)
            result[elementCount - 1]['w'] = previousFactor

        # Add element and increase count
        result.append({'e': element, 'w': 1})
        elementCount += 1

        # Searching next match
        nextString = nextString[span[1]:]
        nextMatch = re.search(pattern, nextString)

    if len(nextString) > 0:
        previousFactor = get_factor(nextString)
        result[elementCount - 1]['w'] = previousFactor

    mass = calculate_mass(elementCount, result)

    return mass, result, elementCount


def isSimple(string):
    # Cu2Se0.92S0.08
    # Cu1.98S1/3Se1/3Te1/3
    # Ge0.86Pb0.1Bi0.04Te
    if '(' in string:
        return False
    if '%' in string:
        return False
    #     if ' ' in string:
    #         return False
    if 'wt.' in string:
        return False

    return True


def preprocess_string(string):
    to_remove = [
        ' (Nano)',
        '(porosity 12.3%)',
        'quantum dot'
    ]

    return string.replace('(porosity 12.3%)', '').replace('carbon fiber', 'C').replace('graphene', 'C').replace(
        'quantum dot', '').replace('Carbon dots', 'C').replace(' C coated Boron', 'C').replace(' nano boron',
                                                                                               'B').replace(' Graphene',
                                                                                                            'C').replace(
        ' C fiber', 'C').replace(' (Nano)', '').replace(' (Nano + amorphous)', '').strip()


def get_mass_from_complex(nextString):
    total_mass = 0

    count = 4
    while '(' in nextString and count > 0:
        w = 1
        composition = nextString[nextString.find("(") + 1:nextString.find(")")]
        mass_temp, result, elementCount = get_mass(composition)

        nextString = nextString[nextString.find(")") + 1:]
        begIdx = nextString.find('(')
        prefix = nextString if begIdx == -1 else nextString[:begIdx]
        print('--- prefix', prefix, mass_temp, nextString)
        total_mass += get_factor(prefix) * mass_temp
        count = count - 1

    print(total_mass)
    return total_mass


def get_total_mass(composition_string):
    try:
        total_mass = 0
        all_parts = []

        composition_string = preprocess_string(composition_string)

        parts = composition_string.split('+')

        num_of_parts = len(parts)

        if num_of_parts == 1:

            if isSimple(parts[0]):
                mass, result, elementCount = get_mass(parts[0])
                total_mass = mass
                all_parts.append({
                    'part': parts[0],
                    'mass': mass,
                    'details': result,
                })

            elif '(' in parts[0] and ')' in parts[0]:
                s = parts[0]
                print('----> () case', parts[0])

                total_mass = get_mass_from_complex(parts[0])

        if num_of_parts == 2:
            part_1 = parts[0]
            part_2 = parts[1]

            # handle part 1
            if isSimple(part_1):
                mass_1, result_1, elementCount_1 = get_mass(part_1)
                total_mass += mass_1
                all_parts.append({
                    'part': part_1,
                    'mass': mass_1,
                    'details': result_1,
                })
            elif '(' in part_1 and ')' in part_1:
                s = part_1
                print('----> () case', part_1)

                total_mass += get_mass_from_complex(part_1)

            # handle part 2
            if 'wt.%' in part_2:
                index = part_2.find('wt.%')
                percent = float(part_2[:index]) / 100
                part_2_composition = part_2[index + 4:]
                mass_2_temp, result_2_temp, elementCount_2 = get_mass(part_2_composition)
                mass_2 = mass_1 * mass_2_temp * percent

                total_mass += mass_2
                all_parts.append({
                    'part': part_2,
                    'mass': mass_2_temp,
                    'factorString': part_2[:index + 4],
                    'factor': mass_1 * percent,
                    'details': result_2_temp,
                })

            elif '%' in part_2:
                index = part_2.find('%')
                percent = float(part_2[:index]) / 100
                part_2_composition = part_2[index + 1:]
                mass_2_temp, result_2_temp, elementCount_2 = get_mass(part_2_composition)
                mass_2 = mass_2_temp * percent

                total_mass += mass_2
                all_parts.append({
                    'part': part_2,
                    'mass': mass_2_temp,
                    'factorString': part_2[:index + 1],
                    'factor': percent,
                    'details': result_2_temp,
                })

        # print(total_mass, all_parts)
        if total_mass == 0:
            return np.nan
        return total_mass
    except:
        return np.nan
