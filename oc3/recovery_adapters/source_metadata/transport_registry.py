"""Technical-only transport adapters; scientific query text is caller-owned."""
from __future__ import annotations

from dataclasses import dataclass
import urllib.request

from oc3lib.source_metadata_acquisition_pilot import RejectRedirect, frozen_headers, query_url


class AdapterError(Exception):
    pass


@dataclass(frozen=True)
class QueryManagerPublicAnonymousV1:
    adapter_id: str = "query_manager_public_anonymous_v1"

    def execute(self, query_id: str, literal_adql: str, response_cap: int,
                evidence_context: dict[str, object]) -> tuple[bytes, dict[str, object]]:
        if evidence_context.get("adapter_validated") is not True:
            raise AdapterError("TECHNICAL_ADAPTER_NOT_VALIDATED")
        url = query_url(literal_adql)
        request = urllib.request.Request(url, headers=frozen_headers(), method="GET")
        response = urllib.request.build_opener(RejectRedirect()).open(request, timeout=300)
        body = response.read(response_cap + 1)
        if len(body) > response_cap:
            raise AdapterError("DATALAB_BODY_CAP_EXCEEDED")
        return body, {"content_type": response.headers.get("Content-Type", ""),
            "http_status": response.getcode(), "query_id": query_id, "url": url}


ADAPTERS = {"query_manager_public_anonymous_v1": QueryManagerPublicAnonymousV1()}


def get_adapter(adapter_id: str):
    try:
        return ADAPTERS[adapter_id]
    except KeyError as exc:
        raise AdapterError("TECHNICAL_ADAPTER_NOT_VALIDATED") from exc
