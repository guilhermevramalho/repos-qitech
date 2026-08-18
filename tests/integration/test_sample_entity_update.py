from tests.utils import ObjectGenerator, RequestGenerator, PayloadGenerator


class TestSampleEntityUpdate:
    def test_update(self):
        sample_entity = ObjectGenerator.create_sample_entity()
        _key = sample_entity["sample_entity_key"]

        new_status = "success"
        payload = {"status": new_status}

        status, response = RequestGenerator.PUT_sample_entity(_key, payload)
        assert status == 202

        status, response = RequestGenerator.GET_sample_entity(_key)
        assert status == 200
        assert response["sample_entity_key"] == _key
        assert response["status"] == "success"

    def test_webhook(self):

        sample_entity = ObjectGenerator.create_sample_entity()
        _key = sample_entity["sample_entity_key"]

        status, response = RequestGenerator.PUT_webhook_sample_entity(_key)
        assert status == 204

        status, response = RequestGenerator.GET_sample_entity(_key)
        assert status == 200
        assert response["sample_entity_key"] == _key
        assert response["counter"] == 1

    def test_update_finished(self):

        sample_entity = ObjectGenerator.create_sample_entity()

        _key = sample_entity["sample_entity_key"]

        ObjectGenerator.update_sample_entity(_key, "success")

        status, response = RequestGenerator.GET_sample_entity(_key)
        assert status == 200
        assert response["sample_entity_key"] == _key
        assert response["status"] == "success"

        payload = PayloadGenerator.create_new_status_payload("success")
        status, response = RequestGenerator.PUT_sample_entity(_key, payload)
        assert status == 409
        assert response["code"] == "QIT001002"
