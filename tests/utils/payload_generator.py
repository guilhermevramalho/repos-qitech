from uuid import uuid4

from tests.utils.random_generator import RandomGenerator


class PayloadGenerator:
    @staticmethod
    def create_sample_entity_payload(hello: str = None) -> dict:
        if hello is None:
            hello = "world"

        payload = {
            "hello": hello,
            "name": "Maria da Silva",
            "email": f"maria.silva.{uuid4()}@exemplo.com.br",
            "document_number": RandomGenerator.generate_cpf(),
            "birthdate": "1990-05-17",
        }
        return payload

    @staticmethod
    def create_new_status_payload(new_status: str = None) -> dict:
        payload = {"status": new_status}
        return payload
