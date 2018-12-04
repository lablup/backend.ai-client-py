Request API
===========

.. module:: ai.backend.client.request
.. currentmodule:: ai.backend.client.request

This module provides low-level API request/response interfaces
based on aiohttp.

Depending on the session object where the request is made from,
:class:`Request` and :class:`Response` differentiate their behavior:
works as plain Python functions or returns awaitables.

.. autoclass:: Request
   :members:
   :undoc-members:

.. autoclass:: Response
   :members:
   :undoc-members:

.. autoclass:: FetchContextManager
   :members:
   :undoc-members:

.. autoclass:: AttachedFile
