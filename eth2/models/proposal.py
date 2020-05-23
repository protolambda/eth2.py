from enum import Enum
from typing import TypeVar, Protocol, List, Union, Sequence

from eth2.core import FromObjProtocol, var_path, api
from eth2spec.phase0 import spec

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


class BeaconStateValidatorAPI(Protocol):

    @api()
    async def __call__(self) -> ValidatorInfo:
        ...


# Routes can also be callable
class BeaconStateValidatorsAPI(ValidatorID[BeaconStateValidatorAPI], Protocol):

    @api()
    async def __call__(self,
                       validator_ids: Union[Sequence[spec.ValidatorIndex], Sequence[spec.BLSPubkey]]
                       ) -> ValidatorInfoList:  # TODO spec is inconsistent with casing
        ...


class BeaconStateAPI(Protocol):

    @api()
    async def root(self) -> spec.Root:
        pass

    @api()
    async def fork(self) -> spec.Fork:
        pass


class BeaconAPI(Protocol):

    states: StateID[BeaconStateAPI]


# TODO: many more methods are missing. Update API to match latest API proposal
