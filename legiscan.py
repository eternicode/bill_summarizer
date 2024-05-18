import io
import os
from base64 import b64decode

import dotenv
import requests

dotenv.load_dotenv()

LEGISCAN_API_KEY = os.getenv("LEGISCAN_API_KEY")


class LegiScanClient:
    def __init__(self, api_key):
        self.root = "https://api.legiscan.com/"
        self.api_key = api_key

    def _build_url(self, **params):
        assert "op" in params, "Operation not specified"
        query_params = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.root}?key={self.api_key}&{query_params}"

    def _get(self, op, **params):
        url = self._build_url(op=op, **params)
        response = requests.get(url).json()
        if response["status"] == "ERROR":
            raise Exception(response)
        return response

    def getSessionList(self, state=None):
        params = {}
        if state:
            params["state"] = state
        return self._get("getSessionList", **params)["sessions"]

    def getMasterList(self, state=None, session_id=None):
        params = {}
        if session_id:
            params["id"] = session_id
        if state:
            params["state"] = state
        if not params:
            raise Exception("Either session_id or state must be provided")

        return self._get("getMasterList", **params)["masterlist"]

    def getBill(self, bill_id):
        return self._get("getBill", id=bill_id)["bill"]

    def getBillText(self, bill_id):
        return self._get("getBillText", id=bill_id)["text"]


def test():
    client = LegiScanClient(LEGISCAN_API_KEY)
    session = client.getMasterList(state="IN")
    print(f"Bill count: {len(session)-1}")
    bill = session["0"]
    bill_data = client.getBill(bill["bill_id"])
    print(f"Bill title: {bill_data['title']}")
    bill_text = client.getBillText(bill_data["texts"][0]["doc_id"])
    doc = io.BytesIO(b64decode(bill_text["doc"]))
    return doc


if __name__ == "__main__":
    test()
