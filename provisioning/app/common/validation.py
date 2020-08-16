from typing import Dict

def less_than_or_equal_to_other(value: object, other_prop: str, values: Dict[str, object]):
    return other_prop in values and (isinstance(values[other_prop], int) or isinstance(values[other_prop], float)) and value <= values[other_prop]
