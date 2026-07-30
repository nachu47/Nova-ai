import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeOutboundURL(ValueError):
    pass


def validate_outbound_url(url: str, *, require_https: bool, allow_private: bool) -> str:
    """Validate an outbound webhook/push URL and reduce SSRF exposure."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeOutboundURL("Only HTTP and HTTPS URLs are supported")
    if require_https and parsed.scheme != "https":
        raise UnsafeOutboundURL("HTTPS is required for outbound URLs in production")
    if not parsed.hostname:
        raise UnsafeOutboundURL("The outbound URL must include a hostname")
    if parsed.username or parsed.password:
        raise UnsafeOutboundURL("Credentials are not allowed in outbound URLs")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" and not allow_private:
        raise UnsafeOutboundURL("Localhost is not allowed for outbound URLs")

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(hostname, parsed.port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise UnsafeOutboundURL("The outbound hostname could not be resolved") from exc

    if not allow_private:
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise UnsafeOutboundURL("Private or non-routable addresses are not allowed")
    return url
