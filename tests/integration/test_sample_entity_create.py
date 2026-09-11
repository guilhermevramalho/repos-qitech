from tests.utils import RequestGenerator


class TestSampleEntityCreate:
    def test_schema(self):
        payload = {}
        status, response = RequestGenerator.POST_sample_entity(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        """Campo que o schema nao pediu e erro, nao um campo ignorado.

        Quem escreve `{"hllo": "mundo"}` com erro de digitacao prefere
        receber um 400 agora a descobrir amanha que o campo nunca chegou.
        Quem garante isso e o "additionalProperties": false do
        src/schemas/post_sample_entity.json.
        """
        payload = {"hello": "mundo", "campo_que_nao_existe": 1}
        status, response = RequestGenerator.POST_sample_entity(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_success(self):
        payload = {"hello": "world"}
        status, response = RequestGenerator.POST_sample_entity(payload)
        assert status == 201

        _key = response["sample_entity_key"]

        status, response = RequestGenerator.GET_sample_entity(_key)
        assert status == 200
        assert response["sample_entity_key"] == _key
        assert response["status"] == "pending"
