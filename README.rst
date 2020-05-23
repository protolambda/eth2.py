.. image:: https://raw.githubusercontent.com/protolambda/eth2.py/master/docs/_static/logo.png
   :width: 100 px

``eth2``
-----------------

.. image:: https://img.shields.io/pypi/l/eth2.svg
    :target: https://pypi.python.org/pypi/eth2

.. image:: https://img.shields.io/pypi/pyversions/eth2.svg
    :target: https://pypi.python.org/pypi/eth2

.. image::  https://img.shields.io/pypi/status/eth2.svg
    :target: https://pypi.python.org/pypi/eth2

.. image:: https://img.shields.io/pypi/implementation/eth2.svg
    :target: https://pypi.python.org/pypi/eth2

.. image:: https://github.com/protolambda/eth2.py/workflows/Eth2%20API%20Python%20CI/badge.svg
    :target: https://github.com/protolambda/eth2.py/actions


**Eth2.py**: Python API interface to the `Eth2.0 API <https://github.com/ethereum/eth2.0-apis>`_.

If you are looking for the Eth2 spec, see ``eth2spec`` on `PyPi <https://pypi.org/project/eth2spec/>`_ and `GitHub <https://github.com/ethereum/eth2.0-specs>`_.

Features
---------

- Uses the excellent `httpx <https://www.python-httpx.org/>`_ library, with `support <https://www.python-httpx.org/async/>`_
  for `Trio <https://github.com/python-trio/trio>`_ and `AsyncIO <https://docs.python.org/3/library/asyncio.html>`_ async runtimes.
- Full type annotations, type hints for every API method
- Compatible with the ``eth2spec`` package types and ``remerkleable`` for SSZ.
- Through the ``eth2spec`` package, Beacon types can be configured, to use the API for testnets or other Eth2 variants.
- Extensive use of Python 3.8 ``Protocol`` typing (`PEP 544 <https://www.python.org/dev/peps/pep-0544/>`_).
  Testing has your code has never been easier, just mock the object, type-safe!.
- Easy extension and definition of API routes. The API function signatures and object types are all you need.

Example
--------

Getting started
^^^^^^^^^^^^^^^^^

.. code-block:: python

    import trio
    from eth2.models import lighthouse
    from eth2.core import ContentType
    from eth2.providers.http import Eth2HttpClient, Eth2HttpOptions

    async def start():
        # Customize this to use your Beacon endpoint
        address = 'http://localhost:4000'
        # Optionally bring in your own HTTP client
        # async with httpx.AsyncClient() as client:
        #     prov = Eth2HttpProvider(client, options=Eth2HttpOptions(api_base_url=address))
        async with Eth2HttpClient(options=Eth2HttpOptions(
                api_base_url=address,
                default_req_type=ContentType.json,
                default_resp_type=ContentType.ssz)) as prov:
            # The provider can be extended with any API model.
            await fun(prov.extended_api(lighthouse.Eth2API))
        print("done!")

    trio.run(start)


Using the API model
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from eth2.models.lighthouse import Eth2API

    async def fun(api: Eth2API):
        print("fetching state!")
        data = await api.beacon.state(slot=spec.Slot(1))
        print(data.beacon_state.eth1_data)

        # Much faster than retrieving full state!
        head = await api.beacon.head()
        print(f"finalized: {head.finalized_block_root.hex()} {head.finalized_slot}")

        enr = await api.network.enr()
        print(enr)

        # Will error, the slashing is invalid, two equal headers (and no signatures ofc)
        await api.beacon.post_proposer_slashing(spec.ProposerSlashing())


Advanced API calls
^^^^^^^^^^^^^^^^^^^^

When you need to tweak individual API call settings

.. code-block:: python

    from eth2.core import ContentType, APIEndpointFn
    from eth2.models.lighthouse import Eth2API, APIState

    async def advanced(api: Eth2API):
        # Make a copy of the callable function, to then change its settings
        fn = APIEndpointFn(api.beacon.state)
        fn.resp_type = ContentType.json  # Instead of default ssz, because why not

        # The most inefficient way to retrieve finalized checkpoint.
        # Full state, as json.
        # But hey, access any data, and process with the spec as you like.
        data: APIState = await fn(slot=spec.Slot(300))
        print(data.beacon_state.finalized_checkpoint)

Defining custom models
^^^^^^^^^^^^^^^^^^^^^^^^

The HTTP provider can "learn" how to use a model of routes, on the fly! No need to hardcode any API calls.
Just define the model as a Pytho 3.8 Protocol. The Eth2 API provider will shadow this model with an implementation.

- Any ``Protocol`` class with annotations can be interpreted as route model. Fields are sub-routes.
- ``api()`` decorator to make function calls usable endpoints. Customize endpoint options if you need.
- ``var_path()`` decorator to make function calls construct dynamic paths

Currently the Lighthouse API model is well supported, and the new standard-API is being experimented with, but incomplete.


Project Links
--------------

- Docs: https://eth2py.readthedocs.io/
- Changelog: https://eth2py.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/eth2
- Issues: https://github.com/protolambda/eth2.py/issues


Contact
--------

Author: `@protolambda <https://github.com/protolambda>`_

License
--------

MIT, see `LICENSE <./LICENSE>`_ file.
