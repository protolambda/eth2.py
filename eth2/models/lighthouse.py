from typing import Protocol, Optional, List

from eth2spec.phase0 import spec
from remerkleable.complex import Container
from remerkleable.core import ObjType

from eth2.core import ContentType, api, Method
from eth2.util import ObjStruct, ObjList, ToObjProtocol, ObjDict


class HeadInfo(Container):
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
    beacon_block: spec.SignedBeaconBlock


class HeadRef(Container):
    beacon_block_root: spec.Root
    beacon_block_slot: spec.Slot


HeadRefs = ObjList[HeadRef]


class CommitteeInfo(ObjStruct):
    slot: spec.Slot
    index: spec.CommitteeIndex
    committee: spec.List[spec.ValidatorIndex, spec.MAX_VALIDATORS_PER_COMMITTEE]


Shuffling = ObjList[CommitteeInfo]


class ValidatorsQuery(ToObjProtocol):
    state_root: Optional[spec.Root]
    pubkeys: List[spec.BLSPubkey]

    def to_obj(self) -> ObjType:
        q = {"pubkeys": list(map(lambda x: x.to_obj(), self.pubkeys))}
        if self.state_root is not None:
            q["state_root"] = self.state_root.to_obj()
        return q


class ValidatorInfo(Container):
    pubkey: spec.BLSPubkey
    validator_index: spec.ValidatorIndex
    balance: spec.Gwei
    validator: spec.Validator


ValidatorInfos = spec.List[ValidatorInfo, spec.VALIDATOR_REGISTRY_LIMIT]

consensus_formats = {ContentType.json, ContentType.ssz}
ssz_api = api(supports=consensus_formats)


class BeaconAPI(Protocol):

    @ssz_api
    async def head(self) -> HeadInfo: ...

    @api()
    async def heads(self) -> HeadRefs: ...

    @ssz_api
    async def block(self, root: Optional[spec.Root] = None, slot: Optional[spec.Slot] = None) -> APIBlock: ...

    @ssz_api
    async def block_root(self, slot: spec.Slot) -> spec.Root: ...

    @api()
    async def committees(self, epoch: spec.Epoch) -> Shuffling: ...

    @ssz_api
    async def fork(self) -> spec.Fork: ...

    @ssz_api
    async def genesis_time(self) -> spec.uint64: ...

    @ssz_api
    async def genesis_validators_root(self) -> spec.Root: ...

    @api(method=Method.POST, supports=consensus_formats, data='query')
    async def validators(self, query: ValidatorsQuery) -> ValidatorInfos: ...

    @api(supports=consensus_formats, name='validators/all')
    async def validators_all(self, state_root: Optional[spec.Root] = None) -> ValidatorInfos: ...

    @api(supports=consensus_formats, name='validators/active')
    async def active(self, state_root: Optional[spec.Root] = None) -> ValidatorInfos: ...

    @ssz_api
    async def state(self, root: Optional[spec.Root] = None, slot: Optional[spec.Slot] = None) -> APIState: ...

    @ssz_api
    async def state_root(self, slot: spec.Slot) -> spec.Root: ...

    @api(supports=consensus_formats, name='state/genesis')
    async def state_genesis(self) -> APIState: ...

    @api(method=Method.POST, supports=consensus_formats, name='attester_slashing', data='slashing')
    async def post_attester_slashing(self, slashing: spec.AttesterSlashing) -> None: ...

    @api(method=Method.POST, supports=consensus_formats, name='proposer_slashing', data='slashing')
    async def post_proposer_slashing(self, slashing: spec.ProposerSlashing) -> None: ...


class GlobalVotes(ObjStruct):
    current_epoch_active_gwei: int
    previous_epoch_active_gwei: int
    current_epoch_attesting_gwei: int
    current_epoch_target_attesting_gwei: int
    previous_epoch_attesting_gwei: int
    previous_epoch_target_attesting_gwei: int
    previous_epoch_head_attesting_gwei: int


class VoteQuery(ObjStruct):
    epoch: spec.Epoch
    pubkeys: ObjList[spec.BLSPubkey]


class VoteInfo(ObjStruct):
    is_slashed: bool
    is_withdrawable_in_current_epoch: bool
    is_active_in_current_epoch: bool
    is_active_in_previous_epoch: bool
    current_epoch_effective_balance_gwei: int
    is_current_epoch_attester: bool
    is_current_epoch_target_attester: bool
    is_previous_epoch_attester: bool
    is_previous_epoch_target_attester: bool
    is_previous_epoch_head_attester: bool


class VoteEntry(ObjStruct):
    epoch: spec.Epoch
    pubkey: spec.BLSPubkey
    validator_index: spec.ValidatorIndex
    vote: VoteInfo


class ConsensusAPI(Protocol):

    @api()
    async def global_votes(self) -> GlobalVotes: ...

    @api(method=Method.POST, data='query')
    async def individual_votes(self, query: VoteQuery) -> ObjList[VoteEntry]: ...


class NetworkAPI(Protocol):

    @api()
    async def enr(self) -> str: ...

    @api()
    async def peer_count(self) -> int: ...

    @api()
    async def peer_id(self) -> str: ...

    @api()
    async def peers(self) -> List[str]: ...

    @api()
    async def listen_port(self) -> int: ...

    @api()
    async def listen_addresses(self) -> List[str]: ...


class ForkchoiceNode(ObjStruct):
    slot: spec.Slot
    state_root: spec.Root
    root: spec.Root
    parent: Optional[int]
    justified_epoch: spec.Epoch
    finalized_epoch: spec.Epoch
    weight: spec.Gwei
    best_child: Optional[int]
    best_descendant: Optional[int]


class ForkchoiceData(ObjStruct):
    prune_threshold: int
    justified_epoch: int
    finalized_epoch: int
    nodes: ObjList[ForkchoiceNode]
    indices: ObjDict[spec.Root, int]


class OperationPool(ObjStruct):
    attestations: ObjList[ObjType]  # TODO: typing is very weird here
    attester_slashings: ObjList[spec.AttesterSlashing]
    proposer_slashings: ObjList[spec.ProposerSlashing]
    voluntary_exits: ObjList[spec.SignedVoluntaryExit]


class AdvancedAPI(Protocol):
    @api()
    async def fork_choice(self) -> ForkchoiceData: ...

    @api()
    async def operation_pool(self) -> OperationPool: ...


class Eth2API(Protocol):
    beacon: BeaconAPI
    consensus: ConsensusAPI
    network: NetworkAPI
    advanced: AdvancedAPI
