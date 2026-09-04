"""VER-04: private/local addresses must be blocked before any fetch happens."""
from __future__ import annotations

import pytest

from app.evidence import UnsafeUrlError, _host_is_public, fetch_url


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "10.0.0.5", "192.168.1.1", "169.254.169.254"])
def test_private_and_metadata_hosts_are_blocked(host):
    assert _host_is_public(host) is False


def test_fetch_url_rejects_non_http_scheme():
    with pytest.raises(UnsafeUrlError):
        fetch_url("file:///etc/passwd")


def test_fetch_url_rejects_loopback():
    with pytest.raises(UnsafeUrlError):
        fetch_url("http://127.0.0.1/admin")


def test_fetch_url_rejects_cloud_metadata_endpoint():
    with pytest.raises(UnsafeUrlError):
        fetch_url("http://169.254.169.254/latest/meta-data/")
