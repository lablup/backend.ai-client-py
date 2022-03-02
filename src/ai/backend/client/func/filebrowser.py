import webbrowser

from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("FileBrowser",)


class FileBrowser(BaseFunction):
    @api_function
    @classmethod
    async def create_or_update_browser(self, vfolders: list[str]):
        rqst = Request("POST", "/storage/filebrowser/create")
        rqst.set_json({"vfolders": vfolders})

        async with rqst.fetch() as resp:
            result = await resp.json()
            if result["status"] == "ok":
                if result['addr'] == "0":
                    print("the number of container exceeds the maximum limit.")

                print(
                    f"""
                    File Browser started.
                    Container ID:
                    {result['container_id']}
                    URL: {result['addr']}
                    """,
                )
                webbrowser.open_new_tab(result["addr"])
            else:
                raise Exception

    @api_function
    @classmethod
    async def destroy_browser(self, container_id):
        rqst = Request("DELETE", "/storage/filebrowser/destroy")
        rqst.set_json({"container_id": container_id})

        async with rqst.fetch() as resp:
            result = await resp.json()
            if result["status"] == "ok":
                print("File Browser destroyed.")
            else:
                raise Exception
