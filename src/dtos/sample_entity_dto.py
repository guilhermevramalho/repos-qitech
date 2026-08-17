from models import SampleEntity
from typing import List
from copy import deepcopy


class SampleEntityDTO:
    @staticmethod
    def obj_to_dict(sample_entity: SampleEntity) -> dict:

        dto = deepcopy(sample_entity.sample_entity_data)
        dto["status"] = sample_entity.status.enumerator
        dto["sample_entity_key"] = sample_entity.sample_entity_key
        dto["counter"] = sample_entity.counter

        return dto

    @staticmethod
    def list_obj_to_list_dict(sample_entities_list: List[dict]) -> dict:

        sample_entities_dict_list = []

        for asset in sample_entities_list:
            sample_entities_dict_list.append(SampleEntityDTO.obj_to_dict(asset))
        return sample_entities_dict_list

    @staticmethod
    def only_obj_key(sample_entity: SampleEntity) -> dict:

        dto = dict()
        dto["sample_entity_key"] = sample_entity.sample_entity_key

        return dto
