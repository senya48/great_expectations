import os
import shutil

import pytest

from great_expectations.data_context.util import safe_mmkdir, file_relative_path
from great_expectations.datasource import Datasource
from great_expectations.exceptions import BatchKwargsError
from great_expectations.datasource.types import SqlAlchemyDatasourceQueryBatchKwargs
from great_expectations.datasource.generator import QueryBatchKwargsGenerator


def test_basic_operation(basic_sqlalchemy_datasource):
    # We should be able to include defined queries as part of configuration
    generator = QueryBatchKwargsGenerator(
        datasource=basic_sqlalchemy_datasource,
        queries={
            "my_asset": "SELECT * FROM my_table WHERE value = $condition",
            "my_simple_asset": "SELECT c1, c2 FROM my_table"
        }
    )

    # Returned assets should be typed and processed by template language
    batch_kwargs = generator.yield_batch_kwargs("my_asset", query_parameters={'condition': "foo"})
    assert isinstance(batch_kwargs, SqlAlchemyDatasourceQueryBatchKwargs)
    assert batch_kwargs.query == "SELECT * FROM my_table WHERE value = $condition"
    assert batch_kwargs.query_parameters == {'condition': "foo"}

    # Without a template, everything should still work
    batch_kwargs = generator.yield_batch_kwargs("my_simple_asset")
    assert isinstance(batch_kwargs, SqlAlchemyDatasourceQueryBatchKwargs)
    assert batch_kwargs.query == "SELECT c1, c2 FROM my_table"


def test_add_query(basic_sqlalchemy_datasource):
    generator = QueryBatchKwargsGenerator(datasource=basic_sqlalchemy_datasource)
    generator.add_query("my_asset", "select * from my_table where val > $condition")

    batch_kwargs = generator.yield_batch_kwargs("my_asset", query_parameters={"condition": 5})
    assert isinstance(batch_kwargs, SqlAlchemyDatasourceQueryBatchKwargs)
    assert batch_kwargs.query == "select * from my_table where val > $condition"
    assert batch_kwargs.query_parameters == {"condition": 5}


def test_partition_id(basic_sqlalchemy_datasource):
    generator = QueryBatchKwargsGenerator(
        datasource=basic_sqlalchemy_datasource,
        queries={
            "my_asset": "SELECT * FROM my_table WHERE value = $partition_id",
        }
    )

    batch_kwargs = generator.build_batch_kwargs("my_asset", partition_id="foo")
    assert isinstance(batch_kwargs, SqlAlchemyDatasourceQueryBatchKwargs)
    assert batch_kwargs.query == "SELECT * FROM my_table WHERE value = $partition_id"
    assert batch_kwargs.query_parameters == {"partition_id": "foo"}


def test_get_available_data_asset_names_for_query_path(empty_data_context):
    # create queries path
    context_path = empty_data_context.root_directory
    query_path = os.path.join(context_path, "datasources/mydatasource/generators/mygenerator")
    safe_mmkdir(query_path)
    shutil.copy(file_relative_path(__file__, "../../test_fixtures/dummy.sql"), query_path)

    data_source = Datasource(name="mydatasource", data_context=empty_data_context)
    generator = QueryBatchKwargsGenerator(name="mygenerator", datasource=data_source)
    sql_list = generator.get_available_data_asset_names()
    assert ("dummy", "query") in sql_list["names"]
