import pytest

from clt_util import query


@pytest.mark.parametrize("order_string, expected_order", [
    ("col", "order by col desc nulls last"),
    ("col:asc", "order by col asc"),
    ("col:desc", "order by col desc nulls last"),
    ("col1;col2", "order by col1 desc nulls last, col2 desc nulls last"),
    ("col1:desc;col2:asc", "order by col1 desc nulls last, col2 asc"),
])
def test_generate_ordering(order_string, expected_order):
    assert query.generate_ordering(order_string) == expected_order


def test_generate_ordering_with_alias_and_default():
    order_by = query.generate_ordering("col", {"col": ("alias.col", "default_dir")})
    assert order_by == "order by alias.col default_dir"


class TestFilterArgs:
    @pytest.mark.parametrize("filter", [
        query.Filter,
        query.BreakFilter,
    ])
    def test_filter_args(self, filter):
        f = filter()
        assert f.args == []

    @pytest.mark.parametrize("filter", [
        query.NotNullFilter,
        query.NullFilter,
    ])
    def test_null_filter_args(self, filter):
        f = filter("column")
        assert f.args == []

    def test_greater_than_filter_args(self):
        f = query.GreaterThanFilter("column", "value")
        assert f.args == []

    def test_equal_filter_args(self):
        f = query.EqualFilter("column", "value")
        assert f.args == []

    def test_range_filter_args(self):
        f = query.RangeFilter("column", "from", "to")
        assert f.args == []

    def test_list_filter_args(self):
        f = query.ListFilter("column", ["v1", "v2"])
        args = f.args
        assert len(args) == 1
        assert args[0].expanding is True
        assert args[0].key == "columns"


class TestFilterParams:
    @pytest.mark.parametrize("filter", [
        query.Filter,
        query.BreakFilter,
    ])
    def test_filter_params(self, filter):
        f = filter()
        assert f.params == {}

    @pytest.mark.parametrize("filter", [
        query.NotNullFilter,
        query.NullFilter,
    ])
    def test_null_filter_params(self, filter):
        f = filter("column")
        assert f.params == {}

    def test_greater_than_filter_params(self):
        f = query.GreaterThanFilter("column", "value")
        assert f.params == {"column": "value"}

    def test_equal_filter_params(self):
        f = query.EqualFilter("column", "value")
        assert f.params == {"column": "value"}

    @pytest.mark.parametrize("date_from, date_to, expected", [
        ("from", "to", {"date_from": "from", "date_to": "to"}),
        ("from", None, {"date_from": "from"}),
        (None, "to", {"date_to": "to"}),
    ])
    def test_range_filter_params(self, date_from, date_to, expected):
        f = query.RangeFilter("date", date_from, date_to)
        assert f.params == expected

    def test_list_filter_params(self):
        f = query.ListFilter("column", ["v1", "v2"])
        assert f.params == {"columns": ["v1", "v2"]}


class TestFilterClauses:
    def test_break_filter_clause(self):
        f = query.BreakFilter()
        assert f.clause == "1 = 0"

    def test_null_filter_clause(self):
        f = query.NullFilter("column")
        assert f.clause == "column is null"

    def test_not_null_filter_clause(self):
        f = query.NotNullFilter("column")
        assert f.clause == "column is not null"

    def test_greater_than_filter_clause(self):
        f = query.GreaterThanFilter("column", "value")
        assert f.clause == "column > :column"

    def test_greater_than_filter_clause_alias(self):
        f = query.GreaterThanFilter("column", "value", alias="t.column")
        assert f.clause == "t.column > :column"

    def test_equal_filter_clause(self):
        f = query.EqualFilter("column", "value")
        assert f.clause == "column = :column"

    def test_equal_filter_clause_alias(self):
        f = query.EqualFilter("column", "value", alias="t.column")
        assert f.clause == "t.column = :column"

    @pytest.mark.parametrize("date_from, date_to, expected", [
        ("from", "to", "date >= :date_from and date < :date_to"),
        ("from", None, "date >= :date_from"),
        (None, "to", "date < :date_to"),
    ])
    def test_range_filter_clause(self, date_from, date_to, expected):
        f = query.RangeFilter("date", date_from, date_to)
        assert f.clause == expected

    @pytest.mark.parametrize("date_from, date_to, expected", [
        ("from", "to", "t.date >= :date_from and t.date < :date_to"),
        ("from", None, "t.date >= :date_from"),
        (None, "to", "t.date < :date_to"),
    ])
    def test_range_filter_clause_alias(self, date_from, date_to, expected):
        f = query.RangeFilter("date", date_from, date_to, alias="t.date")
        assert f.clause == expected

    def test_list_filter_clause(self):
        f = query.ListFilter("column", ["v1", "v2"])
        assert f.clause == "column in :columns"

    def test_list_filter_clause_alias(self):
        f = query.ListFilter("column", ["v1", "v2"], alias="t.column")
        assert f.clause == "t.column in :columns"


class TestGenerateWhere:
    def test_no_clause(self):
        assert query.generate_where() == ("", {}, [])

    def test_base_clause(self):
        assert query.generate_where(base_clause="column = 1") == ("where column = 1", {}, [])

    def test_additional_clause(self):
        where, params, args = query.generate_where(query.EqualFilter("column", 1))
        assert where == "where column = :column"
        assert params == {"column": 1}
        assert args == []

    def test_base_clause_with_additional_clause(self):
        where, params, args = query.generate_where(query.EqualFilter("column", 1), base_clause="column is not null")
        assert where == "where column is not null and column = :column"
        assert params == {"column": 1}
        assert args == []

    def test_base_clause_with_ignored_additional_clause(self):
        where, params, args = query.generate_where(query.EqualFilter("column", None), base_clause="column is not null")
        assert where == "where column is not null"
        assert params == {}
        assert args == []
