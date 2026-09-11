from tests.utils import DbUtils, PayloadGenerator, RequestGenerator


class TestSampleEntities:
    def test_get_pages(self):
        DbUtils.rollback()

        # Um payload novo por entidade, e nao o mesmo tres vezes: cada
        # cadastro precisa do proprio CPF e do proprio e-mail, senao o
        # segundo POST bate na regra de duplicidade do controller.
        for _entidade in range(3):
            payload = PayloadGenerator.create_sample_entity_payload()
            status, response = RequestGenerator.POST_sample_entity(payload)
            assert status == 201

        status, response = RequestGenerator.GET_sample_entities()
        assert status == 200
        assert len(response["data"]) == 3
        assert response["is_last_page"] is True

        status, response = RequestGenerator.GET_sample_entities({"limit": 2})
        assert status == 200
        assert len(response["data"]) == 2
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_sample_entities({"limit": 2, "page": 1})
        assert status == 200
        assert len(response["data"]) == 1
        assert response["is_last_page"] is True

    def test_get_filtered(self):
        DbUtils.rollback()

        payload = PayloadGenerator.create_sample_entity_payload()
        status, response = RequestGenerator.POST_sample_entity(payload)
        assert status == 201

        _key1 = response["sample_entity_key"]

        for _entidade in range(2):
            payload = PayloadGenerator.create_sample_entity_payload()
            status, response = RequestGenerator.POST_sample_entity(payload)
            assert status == 201

        new_status = "success"
        payload = {"status": new_status}

        status, response = RequestGenerator.PUT_sample_entity(_key1, payload)
        assert status == 202

        status, response = RequestGenerator.GET_sample_entities({"status": "success"})
        assert status == 200
        assert len(response["data"]) == 1
        assert response["is_last_page"] is True
        assert response["data"][0]["sample_entity_key"] == _key1

        status, response = RequestGenerator.GET_sample_entities({"status": "pending"})
        assert status == 200
        assert len(response["data"]) == 2
        assert response["is_last_page"] is True

    def test_wrong_params(self):
        status, response = RequestGenerator.GET_sample_entities({"page": -3})
        assert status == 400
        assert response["code"] == "QIT000010"
