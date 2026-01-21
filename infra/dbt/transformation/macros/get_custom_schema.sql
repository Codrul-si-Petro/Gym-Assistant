{#
WHy this is needed:
dbt automatically calls generate_schema_name whenever 
it needs to determine the schema for any model, seed, or snapshot. It's a built-in hook - the macro name is special.
Use it so it's not concatenating schema names
#}


{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is not none -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}
    {%- endif -%}
{%- endmacro %}
