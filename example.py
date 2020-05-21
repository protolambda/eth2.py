import trio

from eth2spec.phase0 import spec

from eth2.core import ContentType, APIEndpointFn
from eth2.routes import Eth2API, APIState
from eth2.providers.http import Eth2HttpClient, Eth2HttpOptions


async def fun(api: Eth2API):
    # Can make a copy of the callable function, to then change its settings
    fn = APIEndpointFn(api.beacon.state)
    fn.req_type = ContentType.json  # Instead of default ssz, because why not

    # The most inefficient way to retrieve finalized checkpoint. But hey,
    data: APIState = await fn(slot=spec.Slot(300))
    print(data.beacon_state.finalized_checkpoint)

    print("fetching state!")

    data = await api.beacon.state(slot=spec.Slot(1))
    print(data.beacon_state.eth1_data)

    head = await api.beacon.head()
    print(head)

    # Much faster than retrieving full state!
    print(f"finalized: {head.finalized_block_root.hex()} {head.finalized_slot}")

    enr = await api.network.enr()
    print(enr)

    # Will error, the slashing is invalid, two equal headers (and no signatures ofc)
    await api.beacon.post_proposer_slashing(spec.ProposerSlashing())


async def start():
    address = 'http://ec2-18-194-126-78.eu-central-1.compute.amazonaws.com:4000'
    # Or specify a custom
    # async with httpx.AsyncClient() as client:
    #     prov = Eth2HttpProvider(client, options=Eth2HttpOptions(api_base_url=address))
    async with Eth2HttpClient(options=Eth2HttpOptions(
            api_base_url=address,
            default_req_type=ContentType.json,
            default_resp_type=ContentType.ssz)) as prov:
        await fun(prov.api)
    print("done!")

trio.run(start)



