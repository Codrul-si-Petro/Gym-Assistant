from collections import defaultdict
from pathlib import Path

from django.db import connection

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def execute_sql(sql: str, params: dict) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def _build_children(rows):
    children = defaultdict(list)
    by_id = {}
    for r in rows:
        cid = r["current_id"]
        by_id[cid] = r
        children[r["parent_id"]].append(cid)
    return children, by_id


def _subtree_terminal_exercise_ids(node_id, children, cache):
    if node_id in cache:
        return cache[node_id]
    direct = children.get(node_id, [])
    if not direct:
        out = frozenset([node_id])
    else:
        s = set()
        for c in direct:
            s |= _subtree_terminal_exercise_ids(c, children, cache)
        out = frozenset(s)
    cache[node_id] = out
    return out


def rollup_exercise_total_volume(hierarchy_rows, volume_by_exercise_id, parent_id):
    children, _by_id = _build_children(hierarchy_rows)
    cache = {}
    results = []
    for r in hierarchy_rows:
        if r["parent_id"] != parent_id:
            continue
        cid = r["current_id"]
        terminals = _subtree_terminal_exercise_ids(cid, children, cache)
        total = sum(volume_by_exercise_id.get(eid, 0) for eid in terminals)
        if total == 0:
            continue
        results.append(
            {
                "exercise_id": cid,
                "exercise_name": r["current_name"],
                "is_leaf": len(children.get(cid, [])) == 0,
                "total_volume_kg": total,
            }
        )
    results.sort(key=lambda x: x["total_volume_kg"], reverse=True)
    return results


def get_dimension_hierarchies(dimension_name):
    query_file = SQL_DIR / "get_dimension_hierarchies.sql"
    query = query_file.read_text()

    return execute_sql(query, {"dimension_name": dimension_name})
