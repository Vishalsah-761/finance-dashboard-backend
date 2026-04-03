from flask import request


def get_pagination_params(default_limit=20, max_limit=100):
    """Extract and validate ?page= and ?limit= from query string."""
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = min(max_limit, max(1, int(request.args.get("limit", default_limit))))
    except (ValueError, TypeError):
        limit = default_limit

    skip = (page - 1) * limit
    return page, limit, skip


def paginate_response(items, total, page, limit):
    """Wrap a list of items with pagination metadata."""
    total_pages = max(1, -(-total // limit))  # ceiling division
    return {
        "items": items,
        "pagination": {
            "total":       total,
            "page":        page,
            "limit":       limit,
            "total_pages": total_pages,
            "has_next":    page < total_pages,
            "has_prev":    page > 1,
        },
    }
