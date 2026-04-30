import re

def parse_nested_form(form_data, prefix):
    results = {}
    pattern = re.compile(rf"{prefix}\[(\d+)\]\[(\w+)\]")

    for key in form_data.keys():
        match = pattern.match(key)
        if match:
            index = int(match.group(1))
            field = match.group(2)
            if index not in results:
                results[index] = {}
            results[index][field] = form_data.get(key)

    return [results[i] for i in sorted(results.keys())]