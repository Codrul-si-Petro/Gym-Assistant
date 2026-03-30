{% macro create_indexes(table_name, columns_list) %}
  {%- set statements = [] -%}
  {%- for cols in columns_list -%}
    {%- set idx_name = table_name | replace('.', '_') ~ '_' ~ (cols | join('_')) ~ '_idx' -%}
    {%- do statements.append("CREATE INDEX IF NOT EXISTS " ~ idx_name ~ " ON " ~ table_name ~ " (" ~ (cols | join(', ')) ~ ");") -%}
  {%- endfor -%}
  {{ statements | join(' ') }}
{% endmacro %}
