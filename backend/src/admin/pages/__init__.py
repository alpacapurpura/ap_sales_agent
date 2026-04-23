"""Admin panel pages — one file per URL route.

Each page is a thin wrapper that delegates rendering to a function in
`src.admin.modules`. This keeps render logic testable in isolation while
letting Streamlit's native multi-page routing handle URL paths, bookmarks
and browser refresh.

Do NOT add business logic here. Add it to the matching module under
`src/admin/modules/` and keep the page file as a single-call bootstrap.
"""
