from sqlalchemy import bindparam


class Filter:
    value = object()

    @property
    def params(self):
        return {}

    @property
    def args(self):
        return []


class BreakFilter(Filter):
    @property
    def clause(self):
        return "1 = 0"


class NullFilter(Filter):
    def __init__(self, column):
        self.column = column

    @property
    def clause(self):
        return "{} is null".format(self.column)


class NotNullFilter(Filter):
    def __init__(self, column):
        self.column = column

    @property
    def clause(self):
        return "{} is not null".format(self.column)


class EqualFilter(Filter):
    def __init__(self, column, value, alias=None):
        self.column = column
        self.value = value
        self.alias = alias or column

    @property
    def clause(self):
        return "{0} = :{1}".format(self.alias, self.column)

    @property
    def params(self):
        return {self.column: self.value}


class GreaterThanFilter(Filter):
    def __init__(self, column, value, alias=None):
        self.column = column
        self.value = value
        self.alias = alias or column

    @property
    def clause(self):
        return "{0} > :{1}".format(self.alias, self.column)

    @property
    def params(self):
        return {self.column: self.value}


class RangeFilter(Filter):
    def __init__(self, column, date_from, date_to, alias=None):
        self.column = column
        self.date_from = date_from
        self.date_to = date_to
        self.alias = alias or column
        self.value = date_from or date_to

    @property
    def clause(self):
        clause = []
        if self.date_from:
            clause.append("{0} >= :{1}_from".format(self.alias, self.column))
        if self.date_to:
            clause.append("{0} < :{1}_to".format(self.alias, self.column))

        return " and ".join(clause)

    @property
    def params(self):
        params = {}
        if self.date_from:
            params["{0}_from".format(self.column)] = self.date_from
        if self.date_to:
            params["{0}_to".format(self.column)] = self.date_to
        return params


class ListFilter(Filter):
    def __init__(self, column, values, alias=None):
        self.column = column
        self.values = values
        self.alias = alias or column

    @property
    def clause(self):
        return "{0} in :{1}s".format(self.alias, self.column)

    @property
    def params(self):
        return {"{0}s".format(self.column): self.values}

    @property
    def args(self):
        return [bindparam("{0}s".format(self.column), expanding=True)]


def generate_where(*filters, base_clause=None):
    where = ""
    params = {}
    args = []

    additional_clauses = []
    for filter_ in filters:
        if filter_.value is None:
            continue
        additional_clauses.append(filter_.clause)
        params.update(filter_.params)
        args.extend(filter_.args)

    additional_clause = " and ".join(additional_clauses)

    if base_clause and additional_clause:
        where = "where " + base_clause + " and " + additional_clause
    elif base_clause:
        where = "where " + base_clause
    elif additional_clause:
        where = "where " + additional_clause

    return where, params, args


def generate_ordering(order_string, order_lookup=None):
    order_lookup = order_lookup or {}

    order_by = []
    ordering = order_string.split(";")
    for o in ordering:
        if ":" in o:
            key, dir_ = o.split(":")
        else:
            key, dir_ = o, None

        order, dir_default = order_lookup.get(key, (key, "desc"))
        dir_ = dir_ or dir_default
        if dir_ == "desc":
            dir_ = "desc nulls last"
        order_by.append(order + " " + dir_)
    return "order by {}".format(", ".join(order_by))
