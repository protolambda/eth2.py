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
    :target: https://github.com/protolambda/eth2/actions


**Eth2.py**: Python API interface to the `Eth2.0 API <https://github.com/ethereum/eth2.0-apis>`_.

If you are looking for the Eth2 spec, see `eth2spec` on `PyPi <https://pypi.org/project/eth2spec/>`_ and `GitHub <github.com/ethereum/eth2.0-specs>`_.

Features
---------

- Uses the excellent `httpx <https://www.python-httpx.org/>`_ library, with `support <https://www.python-httpx.org/async/>`_
  for `Trio <https://github.com/python-trio/trio>`_ and `AsyncIO <https://docs.python.org/3/library/asyncio.html>`_ async runtimes.
- Full type annotations, type hints for every API method
- Compatible with the `eth2spec` package types and `remerkleable` for SSZ.
- Through the `eth2spec` package, Beacon types can be configured, to use the API for testnets or other Eth2 variants.


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
