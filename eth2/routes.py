from typing import Optional, Protocol

from eth2spec.phase0 import spec

from remerkleable.complex import Container

from eth2.core import ModelAPIEndpoint, ContentType, Method, api


class HeadInfo(spec.Container):
    slot: spec.Slot
    block_root: spec.Root
    state_root: spec.Root
    finalized_slot: spec.Slot
    finalized_block_root: spec.Root
    justified_slot: spec.Slot
    justified_block_root: spec.Root
    previous_justified_slot: spec.Slot
    previous_justified_block_root: spec.Root


class APIState(Container):
    root: spec.Root
    beacon_state: spec.BeaconState


class APIBlock(Container):
    root: spec.Root
    block: spec.SignedBeaconBlock


consensus_formats = {ContentType.json, ContentType.ssz}


class BeaconAPI(ModelAPIEndpoint, Protocol):

    @api(supports=consensus_formats)
    async def block(self, root: Optional[spec.Root] = None, slot: Optional[spec.Slot] = None) -> APIBlock:
        """
        Get a block. Either by root or by slot.
        :param root: beacon block hash-tree-root (of BeaconBlock type)
        :param slot: beacon slot
        :return: APIBlock, a SignedBeaconBlock with the block root
        """
        ...

    @api(supports=consensus_formats)
    async def state(self, root: Optional[spec.Root] = None, slot: Optional[spec.Slot] = None) -> APIState:
        """
        Get a state. Either by root or by slot.
        :param root: state hash-tree-root
        :param slot: beacon slot
        :return: APIState, a BeaconState with the state root
        """
        ...

    @api(supports=consensus_formats)
    async def head(self) -> HeadInfo: ...

    # TODO: many more typed methods

    # Example: can have both gets and puts at the same time.

    # @api(spec.ProposerSlashing, method=Method.GET, name='proposer_slashing')
    # async def get_proposer_slashing(self) -> spec.ProposerSlashing: ...

    @api(method=Method.POST, name='proposer_slashing', data='slashing')
    async def post_proposer_slashing(self, slashing: spec.ProposerSlashing) -> None: ...


class NetworkAPI(ModelAPIEndpoint, Protocol):

    @api()
    async def enr(self) -> str:
        """
        :return: The ENR of the node
        """


class Eth2API(ModelAPIEndpoint, Protocol):
    api_version: str

    beacon: BeaconAPI
    network: NetworkAPI

