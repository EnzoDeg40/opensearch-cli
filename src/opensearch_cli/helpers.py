from typing import Any, Dict, List, Union


def black_list(
    data: Union[Dict[str, Any], List[Any]], fields: List[str]
) -> Union[Dict[str, Any], List[Any]]:
    """Remove specified fields from any level of a nested dict or list."""
    if isinstance(data, dict):
        return {k: black_list(v, fields) for k, v in data.items() if k not in fields}
    elif isinstance(data, list):
        return [black_list(item, fields) for item in data]
    return data
