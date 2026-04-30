def is_filters_empty(filters):
    for value in filters.values():
        if value:
            return False
    return True