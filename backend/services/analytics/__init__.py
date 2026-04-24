"""Analytics subpackage.

Each module owns one analytical domain and receives a DataService reference
(ds_ref) so that cache invalidation, cross-analytics composition, and
shared helpers (e.g. STATIC_TICKERS, _get_cache_key) keep working without
reshaping the facade's public API.
"""
