import webbrowser

from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("FileBrowser",)


class FileBrowser(BaseFunction):
    @api_function
    @classmethod
    async def create_or_update_browser(self, vfolders: list[str]):
        rqst = Request("POST", "/browser/create")
        rqst.set_json({"vfolders": vfolders})

        async with rqst.fetch() as resp:
            result = await resp.json()
            if result['status'] == "ok":
                print(f"File Browser started with url: {result['addr']}")
                webbrowser.open_new_tab(result["addr"])
            else:
                raise Exception
