{% macro create_indexes(table_name, columns) %}
  {%- set statements = [] -%}
  {%- for col in columns -%}
    {%- set idx_name = table_name | replace('.', '_') ~ '_' ~ col ~ '_idx' -%}
    {%- do statements.append("CREATE INDEX IF NOT EXISTS " ~ idx_name ~ " ON " ~ table_name ~ " (" ~ col ~ ");") -%}
  {%- endfor -%}
  {{ statements | join(' ') }}
{% endmacro %}
