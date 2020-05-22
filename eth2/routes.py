from enum import Enum
from typing import Optional, Protocol, TypeVar, List, Union, Sequence

from eth2spec.phase0 import spec

from remerkleable.complex import Container

from eth2.core import ContentType, Method, api, FromObjProtocol, S, var_path


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


class ValidatorStatus(Enum):
    slashed = "slashed"
    activation_queue = "activation_queue"
    active = "active"
    exit_queue = "exit_queue"
    exited = "exited"
    withdrawable = "withdrawable"


class ValidatorInfo(FromObjProtocol):
    validator: spec.Validator
    status: ValidatorStatus
    balance: spec.Gwei


class ValidatorInfoList(List[ValidatorInfo], FromObjProtocol):
    pass


consensus_formats = {ContentType.json, ContentType.ssz}


K = TypeVar('K')


class StateID(Protocol[K]):

    head: K
    finalized: K
    justified: K
    genesis: K

    @var_path()
    def state_root(self, value: spec.Root) -> K:
        ...

    @var_path()
    def slot(self, value: spec.Slot) -> K:
        ...


class ValidatorID(Protocol[K]):

    @var_path()
    def pubkey(self, value: spec.BLSPubkey) -> K:
        ...

    @var_path()
    def index(self, value: spec.ValidatorIndex) -> K:
        ...


class BeaconStateValidatorAPI(Protocol):

    @api()
    async def __call__(self) -> ValidatorInfo:
        ...


# Routes can also be callable
class BeaconStateValidatorsAPI(ValidatorID[BeaconStateValidatorAPI], Protocol):

    @api()
    async def __call__(self, validatorIds: Union[Sequence[spec.ValidatorIndex], Sequence[spec.BLSPubkey]]) -> ValidatorInfoList:  # TODO spec is inconsistent with casing
        ...


class BeaconStateAPI(Protocol):

    @api(supports=consensus_formats)
    async def root(self) -> spec.Root:
        pass

    @api(supports=consensus_formats)
    async def fork(self) -> spec.Fork:
        pass


class BeaconAPI(Protocol):

    states: StateID[BeaconStateAPI]

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

    @api(method=Method.POST, supports=consensus_formats, name='proposer_slashing', data='slashing')
    async def post_proposer_slashing(self, slashing: spec.ProposerSlashing) -> None: ...


class NetworkAPI(Protocol):

    @api()
    async def enr(self) -> str:
        """
        :return: The ENR of the node
        """


class Eth2API(Protocol):
    api_version: str

    beacon: BeaconAPI
    network: NetworkAPI
