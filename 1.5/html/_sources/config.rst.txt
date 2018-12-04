Client Configuration
====================

.. module:: ai.backend.client.config
.. currentmodule:: ai.backend.client.config

The configuration for Backend.AI API includes the endpoint URL prefix, API
keypairs (access and secret keys), and a few others.

There are two ways to set the configuration:

1. Setting environment variables before running your program that uses this SDK.
2. Manually creating :class:`APIConfig` instance and creating sessions with it.

The list of supported environment variables are:

* ``BACKEND_ENDPOINT``
* ``BACKEND_ACCESS_KEY``
* ``BACKEND_SECRET_KEY``
* ``BACKEND_VFOLDER_MOUNTS``

Other configurations are set to defaults.

Note that when you use our client-side Jupyter integration,
``BACKEND_VFOLDER_MOUNTS`` is the only way to attach your virtual folders to the
notebook kernels.

.. autofunction:: get_env

.. autofunction:: get_config

.. autofunction:: set_config

.. autoclass:: APIConfig
  :members:
