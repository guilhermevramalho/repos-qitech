class PayloadGenerator:
    @staticmethod
    def create_sample_entity_payload(hello: str = None) -> dict:
        if hello is None:
            hello = "world"
        payload = {"hello": hello}
        return payload

    @staticmethod
    def create_new_status_payload(new_status: str = None) -> dict:
        payload = {"status": new_status}
        return payload
