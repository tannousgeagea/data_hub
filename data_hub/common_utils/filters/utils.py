
import re

def map_value_range(value:str):
    value = value.strip().lower()

    # Handle range like "51 - 100"
    range_match = re.match(r"^(\d+)\s*-\s*(\d+)", value)
    if range_match:
        lower = int(range_match.group(1)) / 100
        upper = int(range_match.group(2)) / 100
        return [
            ("value__gte", lower),
            ("value__lte", upper)
        ]

    # Handle range like "51 - 100"
    range_match = re.match(r"^(\d+)\s*_\s*(\d+)", value)
    if range_match:
        lower = int(range_match.group(1)) / 100
        upper = int(range_match.group(2)) / 100
        return [
            ("value__gte", lower),
            ("value__lte", upper)
        ]

    # Handle threshold like "> 150 cm"
    gt_match = re.match(r"^>\s*(\d+)", value)
    if gt_match:
        threshold = int(gt_match.group(1))
        return ("value__gt", threshold / 100)
    
    lt_match = re.match(r"^<\s*(\d+)", value)
    if lt_match:
        threshold = int(lt_match.group(1))
        return ("value__lt", threshold / 100)
    
    try:
        num = int(value) / 100
        return ("value__gte", num)
    except ValueError:
        raise ValueError(f"Unrecognized value format: {value}")
    

def map_description(desc:str):
    try:
        number = float(desc.split('[')[1].split(']')[0])
        return f"{round(number * 100)} cm"
    except:
        return ""

def map_value(value:float, flag_type:str):
    if value is None:
        return None
    
    value = float(value)
    if flag_type == "impurity":
        return f"{round(value * 100)} cm"
    elif flag_type == "hotspot":
        return f"{value} °C"
    else:
        return None
    
def map_entity_type_to_table_type(entity_type:str=None):
    if entity_type is None: 
        return "alarm"
    
    entity_type = entity_type.lower()
    if entity_type not in ["gate", "trichter", "bunker"]:
        return "alarm"
    
    if entity_type != "gate":
        return f"alarm{entity_type}"

    return "alarm"