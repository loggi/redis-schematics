# encoding: utf8

from __future__ import absolute_import


FILTER_OPS = {
    "__gt": lambda s, r: s > r,
    "__lt": lambda s, r: s < r,
    "__gte": lambda s, r: s >= r,
    "__lte": lambda s, r: s <= r,
    "__eq": lambda s, r: s == r,
    "__not": lambda s, r: s != r,
    "__in": lambda s, r: s in r,
    "__exclude": lambda s, r: s not in r,
}


def group_filters_by_suffix(filters):

    used = {}

    def get_suffix(suffix):
        suffixed = {k: v for k, v in filters.items() if k.endswith(suffix)}
        cleaned = {k.replace(suffix, ""): v for k, v in suffixed.items()}
        used.update(suffixed)
        return cleaned

    filter_group = {k: get_suffix(k) for k in FILTER_OPS}
    filter_group["__eq"].update(**{k: v for k, v in filters.items() if k not in used})
    return filter_group


def match_filters(obj, filter_group):
    for suffix, category_filters in filter_group.items():
        operator = FILTER_OPS[suffix]

        for k, v in category_filters.items():
            if not operator(getattr(obj, k, None), v):
                return False

    return True
